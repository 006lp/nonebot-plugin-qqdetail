import httpx
import re
import nonebot
from nonebot import on_regex
from nonebot.log import logger
from typing import Union, Optional, Tuple
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Bot, Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent
from nonebot.params import RegexGroup
from nonebot.plugin import PluginMetadata
from .config import config, Config
from nonebot.matcher import Matcher

__plugin_meta__ = PluginMetadata(
    name="QQ详细信息查询 (Regex v2)",
    description="让机器人查询QQ详细信息 (使用正则严格匹配)",
    usage="/detail[空格]<QQ号|@用户>\n/info[空格]<QQ号|@用户>\n(无参数查询自己)",
    type="application",
    homepage="https://github.com/006lp/nonebot-plugin-qqdetail",
    supported_adapters={"~onebot.v11"}
)

# --- 获取命令前缀 ---
command_start = ""
try:
    command_start = next(iter(nonebot.get_driver().config.command_start))
except Exception:
    logger.warning("未配置 COMMAND_START，将假定命令前缀为空或'/'")
    if "/" in nonebot.get_driver().config.command_start:
        command_start = "/"

escaped_prefix = re.escape(command_start)

# --- 正则表达式保持不变 ---
# 它用于:
# 1. 匹配命令格式（命令 或 命令+空格+任意内容）
# 2. 捕获命令名 (group 1)
# 3. 区分是否有参数部分 (通过 group 2 是否为 None 判断)
# !! 我们不再依赖 group 2 的 *内容* 来获取参数 !!
pattern_str = rf"^{escaped_prefix}(detail|info)(?:\s+(.*))?\s*$"

qq_detail_regex = on_regex(pattern_str, priority=5, block=True)

# --- 辅助函数 (is_whitelisted, fetch_qq_detail 保持不变) ---
async def is_whitelisted(uid: str) -> bool:
    """检查 UID 是否在白名单内"""
    whitelist = getattr(config, 'qqdetail_whitelist', []) or []
    return uid in whitelist

async def fetch_qq_detail(uid: str) -> dict:
    """调用 API 获取 QQ 详细信息"""
    url = f"https://api.yyy001.com/api/qqdetail?qq={uid}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"API response for UID {uid}: {data}")
            return data
    except httpx.TimeoutException:
        logger.error(f"Request timed out for UID {uid}.")
        return {"response": {"code": 408, "msg": "请求API超时"}}
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error for {uid}: Status {e.response.status_code}")
        error_msg = f"API请求失败: {e.response.status_code}"
        try:
            err_data = e.response.json()
            if isinstance(err_data, dict) and 'msg' in err_data:
                error_msg += f" - {err_data['msg']}"
        except Exception: pass
        return {"response": {"code": e.response.status_code, "msg": error_msg}}
    except Exception as e:
        logger.exception(f"Unexpected error fetching detail for {uid}: {e}")
        return {"response": {"code": 500, "msg": f"处理API请求时发生内部错误"}}


# --- Regex 主处理器 (修改版) ---
@qq_detail_regex.handle()
async def handle_regex_detail(bot: Bot, event: Union[PrivateMessageEvent, GroupMessageEvent], matcher: Matcher, match: Tuple[Optional[str], ...] = RegexGroup()):
    """
    使用 on_regex 处理查询请求。
    match[0]: 命令名 (detail, info)
    match[1]: 用于判断 *是否* 有参数部分 (None 表示无, 非 None 表示有), 但不依赖其内容。
    """
    command_name = match[0]
    has_argument_part = match[1] is not None # 通过第二捕获组是否为None判断有无参数段

    raw_message = getattr(event, 'raw_message', '').strip()
    logger.debug(f"Regex handler triggered: command='{command_name}', has_argument_part={has_argument_part}")
    logger.debug(f"Raw message: {raw_message}")

    target_uid: Optional[str] = None
    parameter_error = False
    actual_arg_str = "" # 存储实际解析出的参数字符串

    if not has_argument_part:
        # --- 情况 1: 无参数 ---
        # 确保 raw_message 确实只是命令本身
        expected_command_only = f"{command_start}{command_name}"
        if raw_message == expected_command_only:
             target_uid = str(event.get_user_id())
             logger.info(f"命令 '{command_name}' 无参数，查询发送者: {target_uid}")
        else:
             # 理论上正则不应该匹配到这里，但作为保险
             logger.warning(f"Regex matched no arg part, but raw_message '{raw_message}' != '{expected_command_only}'. Ignoring.")
             await matcher.finish() # 或者提示错误
             return
    else:
        # --- 情况 2: 有参数部分 ---
        # 从 raw_message 中手动提取参数
        # 找到命令 (包括前缀) 之后第一个空格的位置
        prefix_and_command = f"{command_start}{command_name}"
        try:
            # 寻找第一个空格，且必须紧跟在命令名之后
            first_space_index = -1
            # 确保命令确实以我们期望的前缀和名称开头
            if raw_message.startswith(prefix_and_command):
                # 从命令名之后开始查找空格
                potential_space_index = len(prefix_and_command)
                # 检查命令名后紧跟着的是否是空格
                if potential_space_index < len(raw_message) and raw_message[potential_space_index].isspace():
                    # 跳过所有连续的空格
                    first_non_space_after_command = potential_space_index
                    while first_non_space_after_command < len(raw_message) and raw_message[first_non_space_after_command].isspace():
                        first_non_space_after_command += 1
                    # 如果空格后还有内容，提取它
                    if first_non_space_after_command < len(raw_message):
                        actual_arg_str = raw_message[first_non_space_after_command:].strip()
                    else:
                        # 只有命令+空格的情况
                        actual_arg_str = "" # 明确设置为空字符串
                else:
                    # 命令后没有空格直接跟了其他字符，理论上正则不匹配，但也处理下
                    parameter_error = True
                    logger.warning(f"命令 '{command_name}' 后缺少空格。")

            else: # raw_message 开头不是预期的命令，理论上不该发生
                 logger.error(f"Internal error: Raw message '{raw_message}' doesn't start with expected command '{prefix_and_command}'.")
                 await matcher.finish("处理请求时发生内部错误。")
                 return

            logger.debug(f"Extracted actual argument string: '{actual_arg_str}'")

            if not parameter_error: # 仅在没有发现明显格式错误时校验参数内容
                if not actual_arg_str:
                    # 命令后只有空格的情况
                    parameter_error = True
                    logger.warning(f"命令 '{command_name}' 后只有空格，格式错误。")
                else:
                    # 校验 actual_arg_str 的内容
                    # 2.1 尝试匹配 @用户
                    cq_at_match = re.fullmatch(r"\[CQ:at,qq=(\d{5,11})\]", actual_arg_str)
                    if cq_at_match:
                        target_uid = cq_at_match.group(1)
                        logger.info(f"从参数 '{actual_arg_str}' 解析到 @用户 UID: {target_uid}")
                    else:
                        # 2.2 尝试匹配纯数字 QQ 号
                        if re.fullmatch(r"\d{5,11}", actual_arg_str):
                            target_uid = actual_arg_str
                            logger.info(f"从参数 '{actual_arg_str}' 解析到纯数字 QQ UID: {target_uid}")
                        else:
                            # 2.3 参数既不是有效 @ 也不是有效 QQ 号
                            parameter_error = True
                            logger.warning(f"命令 '{command_name}' 的参数 '{actual_arg_str}' 格式无效。")

        except Exception as e:
            logger.exception(f"Error parsing arguments from raw_message: {e}")
            parameter_error = True

        # 如果在参数解析或校验过程中发现错误
        if parameter_error:
             usage_msg = __plugin_meta__.usage or "请检查命令用法。"
             await matcher.finish(f"命令参数格式错误。\n请提供有效的 QQ号(5-11位) 或 @用户。\n\n用法:\n{usage_msg}")
             return

    # --- 后续通用逻辑 ---
    if target_uid is None:
         logger.error("Logic error: target_uid is None after argument processing.")
         await matcher.finish("处理请求时发生内部错误。")
         return

    sender_id = str(event.get_user_id())
    superusers = getattr(bot.config, "superusers", set())
    is_sender_superuser = sender_id in superusers

    logger.debug(f"最终 Query Target UID: {target_uid}, Sender UID: {sender_id}, Is Superuser: {is_sender_superuser}")

    # ... (白名单检查, API 调用, 发送结果逻辑保持不变)
    if await is_whitelisted(target_uid) and not is_sender_superuser and sender_id != target_uid:
        await matcher.finish(f"抱歉，您没有权限查询该用户 (UID: {target_uid}) 的信息。")
        return

    data = await fetch_qq_detail(target_uid)

    response_data = data.get("response")
    if isinstance(response_data, dict) and response_data.get("code") == 200:
        nickname = response_data.get('name', '未知')
        headimg_url = response_data.get('headimg')
        details = [
            f"查询对象：{response_data.get('qq')}",
            f"昵称：{nickname}",
            f"QID：{response_data.get('qid')}",
            f"性别：{response_data.get('sex')}",
            f"年龄：{response_data.get('age')}",
            f"IP属地：{response_data.get('ip_city')}",
            f"等级：Lv.{response_data.get('level')}",
            f"等级图标：{response_data.get('icon')}",
            f"能量值：{response_data.get('energy_value')}",
            f"注册时间：{response_data.get('RegistrationTime')}",
            f"注册时长：{response_data.get('RegTimeLength')}",
            f"连续在线天数：{response_data.get('iLoginDays')}",
            f"总活跃天数：{response_data.get('iTotalActiveDay')}",
            f"加速状态：{response_data.get('Accelerate')}",
            f"升到下一级预计天数：{response_data.get('iNextLevelDay')}",
            f"成长值：{response_data.get('iGrowthValue')}",
            f"VIP标识：{response_data.get('iVip')}",
            f"SVIP标识：{response_data.get('iSVip')}",
            f"年费会员：{response_data.get('NVip')}",
            f"VIP等级：{response_data.get('iVipLevel')}",
            f"VIP到期时间：{response_data.get('sVipExpireTime')}",
            f"SVIP到期时间：{response_data.get('sSVipExpireTime')}",
            f"年费到期时间：{response_data.get('sYearExpireTime')}",
            f"大会员标识：{response_data.get('XVip')}",
            f"年费大会员标识：{response_data.get('NXVip')}",
            f"大会员等级：{response_data.get('XVipLevel')}",
            f"大会员成长值：{response_data.get('XVipGrowth')}",
            f"大会员每日成长速度：{response_data.get('XVipSpeed')}",
            f"昨日在线：{response_data.get('iYesterdayLogin')}",
            f"今日在线：{response_data.get('iTodayLogin')}",
            f"今日安卓在线时长：{response_data.get('iMobileQQOnlineTime')}",
            f"今日电脑在线时长：{response_data.get('iPCQQOnlineTime')}",
            f"今日已加速天数：{response_data.get('iRealDays')}",
            f"今日最大可加速天数：{response_data.get('iMaxLvlRealDays')}",
            f"签名：{response_data.get('sign')}"
        ]
        qq_detail_message_text = "\n".join(filter(None, details))
        message_to_send = Message()
        if headimg_url:
            try: message_to_send.append(MessageSegment.image(headimg_url))
            except Exception as e: logger.warning(f"无法创建头像图片 for {headimg_url}: {e}")
        message_to_send.append(MessageSegment.text(qq_detail_message_text))
        await matcher.finish(message_to_send)
    else:
        error_msg = "未知错误"
        if isinstance(response_data, dict): error_msg = response_data.get('msg', error_msg)
        elif isinstance(data, dict) and "msg" in data: error_msg = data.get('msg', error_msg)
        logger.warning(f"获取 QQ 详细信息失败 UID {target_uid}. API Msg: {error_msg}")
        await matcher.finish(f"获取QQ信息失败 (UID: {target_uid})。\n原因：{error_msg}")