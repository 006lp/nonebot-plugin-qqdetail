import httpx
import nonebot
from nonebot import require
from nonebot.log import logger
from typing import Union, Optional
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent
from nonebot.plugin import PluginMetadata
import re

require("nonebot_plugin_alconna")

from arclet.alconna import Alconna, CommandMeta, Arg, Arparma
from nonebot_plugin_alconna import on_alconna, Match, AlconnaMatcher
from nonebot_plugin_alconna.uniseg import At, Text # Text 主要用于 Match[Text] 类型注解

from .config import config, Config

__plugin_meta__ = PluginMetadata(
    name="QQ详细信息查询 (Alconna v2)",
    description="让机器人查询QQ详细信息 (使用 Alconna 解析)",
    usage="/detail[空格]<QQ号|@用户>\n/info[空格]<QQ号|@用户>\n(无参数查询自己)",
    type="application",
    homepage="https://github.com/006lp/nonebot-plugin-qqdetail",
    config=Config,
    supported_adapters={"~onebot.v11"}
)

actual_prefixes: list[str] = []
try:
    nb_command_start_cfg = getattr(nonebot.get_driver().config, "command_start", None)
    if not nb_command_start_cfg:
        logger.warning("全局 COMMAND_START 未配置或为空，qqdetail 将使用 '/' 和空字符串作为命令前缀。")
        actual_prefixes = ["/", ""]
    else:
        actual_prefixes = list(nb_command_start_cfg)
except (AttributeError, TypeError):
    logger.warning("无法从驱动配置中获取 COMMAND_START，qqdetail 将使用 '/' 和空字符串作为命令前缀。")
    actual_prefixes = ["/", ""]
logger.info(f"nonebot-plugin-qqdetail: 实际使用的 Alconna 前缀 (actual_prefixes): {actual_prefixes}")

# --- common_target_arg 定义 ---
# 使用 (At, str) 并后续在 handler 中对 str 进行正则校验
common_target_arg = Arg(
    "target?", # 可选参数
    value=(
        At,  # 匹配 @用户，结果是 At 对象
        str  # 匹配任意字符串，后续在 handler 中校验格式
    )
)
logger.debug(f"nonebot-plugin-qqdetail: common_target_arg 定义为 value=(At, str): {common_target_arg}")

common_meta = CommandMeta(
    description=__plugin_meta__.description,
    usage=__plugin_meta__.usage,
    example=(
        f"{actual_prefixes[0] if actual_prefixes else ''}detail 1234567\n"
        f"{actual_prefixes[0] if actual_prefixes else ''}info @nickname"
    )
)

alc_detail = Alconna(actual_prefixes, "detail", common_target_arg, meta=common_meta)

async def is_whitelisted(uid: str) -> bool:
    whitelist = getattr(config, 'qqdetail_whitelist', [])
    if not isinstance(whitelist, list): whitelist = []
    return uid in whitelist

async def fetch_qq_detail(uid: str) -> dict:
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
        logger.error(f"HTTP error for {uid}: Status {e.response.status_code}, Response: {e.response.text}")
        error_msg = f"API请求失败: {e.response.status_code}"
        try:
            err_data = e.response.json()
            if isinstance(err_data, dict) and 'msg' in err_data: error_msg += f" - {err_data['msg']}"
        except Exception: pass
        return {"response": {"code": e.response.status_code, "msg": error_msg}}
    except Exception as e:
        logger.exception(f"Unexpected error fetching detail for {uid}: {e}")
        return {"response": {"code": 500, "msg": f"处理API请求时发生内部错误: {type(e).__name__}"}}

async def _handle_qqdetail_logic(
    matcher: AlconnaMatcher,
    bot: Bot,
    event: Union[PrivateMessageEvent, GroupMessageEvent],
    target_match: Match[Union[At, str, None]] # 预期是 At 或 str
):
    parsed_target_value = target_match.result if target_match.available else None
    target_uid: Optional[str] = None

    if parsed_target_value is None: # 无参数情况
        target_uid = str(event.get_user_id())
        logger.info(f"命令无参数，查询发送者: {target_uid}")
    elif isinstance(parsed_target_value, At): # @用户的情况
        uid_from_at = parsed_target_value.target
        if isinstance(uid_from_at, str) and uid_from_at.isdigit() and 5 <= len(uid_from_at) <= 11:
            target_uid = uid_from_at
            logger.info(f"从参数 @用户 '{parsed_target_value}' 解析到 UID: {target_uid}")
        else:
            logger.warning(f"从 @用户 '{parsed_target_value}' 提取的 UID '{uid_from_at}' 格式无效。")
            await matcher.finish(f"@{uid_from_at if isinstance(uid_from_at, str) else '用户'} 解析出的QQ号格式不正确。\n请确保艾特的是有效用户。")
            return
    elif isinstance(parsed_target_value, str): # 纯文本 QQ 号的情况
        # 在这里进行正则表达式校验，因为 Arg value=str 不会做格式校验
        qq_str_candidate = parsed_target_value.strip()
        if re.fullmatch(r"^\d{5,11}$", qq_str_candidate):
            target_uid = qq_str_candidate
            logger.info(f"从文本参数 '{qq_str_candidate}' 解析并验证通过的纯数字 QQ UID: {target_uid}")
        else:
            logger.warning(f"文本参数 '{qq_str_candidate}' 不符合QQ号格式 (5-11位纯数字)。")
            await matcher.finish(f"提供的QQ号 '{qq_str_candidate}' 格式不正确，应为5-11位数字。")
            return
    # 可选：处理意外的 Text 对象，尽管我们期望是 str
    elif isinstance(parsed_target_value, Text) and hasattr(parsed_target_value, 'text'):
        text_content = parsed_target_value.text.strip()
        logger.warning(f"参数被解析为 Text 对象 (内容: '{text_content}'), 将尝试按字符串处理。")
        if re.fullmatch(r"^\d{5,11}$", text_content):
            target_uid = text_content
            logger.debug(f"从 Text 对象内文本 '{text_content}' 解析并验证通过的纯数字 QQ UID: {target_uid}")
        else:
            logger.warning(f"Text 对象内文本 '{text_content}' 不符合QQ号格式。")
            await matcher.finish(f"提供的QQ号 '{text_content}' (来自Text对象) 格式不正确。")
            return
    else:
        logger.error(f"内部错误：未能处理的参数类型 '{type(parsed_target_value)}' ({parsed_target_value})。")
        await matcher.finish("命令参数解析时发生内部错误，请联系管理员。")
        return

    if not target_uid:
        logger.error("内部逻辑错误：target_uid 未能成功赋值。") # 理论上不应到达这里
        await matcher.finish("处理请求时发生内部错误。")
        return

    sender_id = str(event.get_user_id())
    superusers = list(getattr(bot.config, "superusers", set()))
    is_sender_superuser = sender_id in superusers
    logger.info(f"最终查询目标 UID: {target_uid}, 发送者 UID: {sender_id}, 发送者是否为超级用户: {is_sender_superuser}")

    if await is_whitelisted(target_uid) and not is_sender_superuser and sender_id != target_uid:
        await matcher.finish(f"抱歉，您没有权限查询该用户 (UID: {target_uid}) 的信息。")
        return

    api_data = await fetch_qq_detail(target_uid)
    response_data = api_data.get("response")

    if isinstance(response_data, dict) and response_data.get("code") == 200:
        nickname = response_data.get('name', '未知')
        headimg_url = response_data.get('headimg')
        details = [
            f"查询对象：{response_data.get('qq')}", f"昵称：{nickname}",
            f"QID：{response_data.get('qid', '无')}", f"性别：{response_data.get('sex', '未知')}",
            f"年龄：{response_data.get('age', '未知')}", f"IP属地：{response_data.get('ip_city', '未知')}",
            f"等级：Lv.{response_data.get('level', '未知')}", f"等级图标：{response_data.get('icon', '无')}",
            f"能量值：{response_data.get('energy_value', '未知')}",
            f"注册时间：{response_data.get('RegistrationTime', '未知')}",
            f"注册时长：{response_data.get('RegTimeLength', '未知')}",
            f"连续在线天数：{response_data.get('iLoginDays', '未知')}",
            f"总活跃天数：{response_data.get('iTotalActiveDay', '未知')}",
            f"加速状态：{response_data.get('Accelerate', '未知')}",
            f"升到下一级预计天数：{response_data.get('iNextLevelDay', '未知')}",
            f"成长值：{response_data.get('iGrowthValue', '未知')}",
            f"VIP标识：{response_data.get('iVip', '无')}", f"SVIP标识：{response_data.get('iSVip', '无')}",
            f"年费会员：{response_data.get('NVip', '无')}", f"VIP等级：{response_data.get('iVipLevel', '无')}",
            f"VIP到期时间：{response_data.get('sVipExpireTime', '未知')}",
            f"SVIP到期时间：{response_data.get('sSVipExpireTime', '未知')}",
            f"年费到期时间：{response_data.get('sYearExpireTime', '未知')}",
            f"大会员标识：{response_data.get('XVip', '无')}", f"年费大会员标识：{response_data.get('NXVip', '无')}",
            f"大会员等级：{response_data.get('XVipLevel', '无')}",
            f"大会员成长值：{response_data.get('XVipGrowth', '未知')}",
            f"大会员每日成长速度：{response_data.get('XVipSpeed', '未知')}",
            f"昨日在线：{response_data.get('iYesterdayLogin', '未知')}",
            f"今日在线：{response_data.get('iTodayLogin', '未知')}",
            f"今日安卓在线时长：{response_data.get('iMobileQQOnlineTime', '未知')}",
            f"今日电脑在线时长：{response_data.get('iPCQQOnlineTime', '未知')}",
            f"今日已加速天数：{response_data.get('iRealDays', '未知')}",
            f"今日最大可加速天数：{response_data.get('iMaxLvlRealDays', '未知')}",
            f"签名：{response_data.get('sign', '无')}"
        ]
        qq_detail_message_text = "\n".join(filter(None, details))
        message_to_send = Message()
        if headimg_url and isinstance(headimg_url, str) and headimg_url.startswith("http"):
            try: message_to_send.append(MessageSegment.image(headimg_url))
            except Exception as e: logger.warning(f"无法创建头像图片 MessageSegment for {headimg_url}: {e}")
        if qq_detail_message_text.strip(): message_to_send.append(MessageSegment.text(qq_detail_message_text))
        elif not message_to_send:
            await matcher.finish(f"获取到用户 {nickname} (UID: {target_uid}) 的信息为空。")
            return
        if not message_to_send:
            await matcher.finish(f"未能构建有效的回复消息 (UID: {target_uid})。")
            return
        await matcher.finish(message_to_send)
    else:
        error_msg = "未知错误"
        if isinstance(response_data, dict): error_msg = response_data.get('msg', error_msg)
        elif isinstance(api_data, dict) and "msg" in api_data: error_msg = api_data.get('msg', error_msg)
        logger.warning(f"获取 QQ 详细信息失败 (UID: {target_uid}). API Msg: '{error_msg}', Full API Response: {api_data}")
        await matcher.finish(f"获取QQ信息失败 (UID: {target_uid})。\n原因：{error_msg}")

detail_service = on_alconna(
    alc_detail,
    aliases={"info","开"},
    priority=6,
    block=True,
    use_origin=True
)
@detail_service.handle()
async def handle_detail_command(
    matcher: AlconnaMatcher, bot: Bot, event: Union[PrivateMessageEvent, GroupMessageEvent],
    target: Match[Union[At, str, None]], # 注入类型为 At 或 str
    result: Arparma # 保留 Arparma 以便观察
):
    logger.debug(f"--- Detail Handler Triggered (Full Logic) ---")
    logger.debug(f"Arparma.matched: {result.matched}")
    logger.debug(f"Target Match available: {target.available}")
    if target.available: logger.debug(f"Target Match result: '{target.result}' (type: {type(target.result)})")

    if not result.matched: # 理论上 skip_for_unmatch=True (默认) 时不会进入这里
        logger.warning("Detail handler was called but Arparma.matched is False.")
        return
    await _handle_qqdetail_logic(matcher, bot, event, target)