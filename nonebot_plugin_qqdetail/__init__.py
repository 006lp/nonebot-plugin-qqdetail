import httpx
import nonebot
import re  # 需要正则表达式
from nonebot import on_command
from nonebot.log import logger
from typing import Union, Optional
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Bot, Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from .config import config, Config
from nonebot.matcher import Matcher

__plugin_meta__ = PluginMetadata(
    name="QQ详细信息查询",
    description="让机器人查询QQ详细信息",
    usage="/detail <QQ号(5-11位)> 或 /detail @用户\n/info <QQ号(5-11位)> 或 /info @用户",
    type="application",
    homepage="https://github.com/006lp/nonebot-plugin-qqdetail",
    supported_adapters={"~onebot.v11"}
)

# 创建命令处理器
qq_detail = on_command("detail", aliases={"info"}, priority=5, block=True)

# --- 辅助函数 ---

async def is_whitelisted(uid: str) -> bool:
    """检查 UID 是否在白名单内"""
    whitelist = getattr(config, 'qqdetail_whitelist', []) or []
    return uid in whitelist

# 再次修改 get_uid，优先使用 event.raw_message
async def get_uid(event: Event, arg: Message) -> Optional[str]:
    """
    获取目标用户的 UID，优先从原始消息字符串解析 @。
    优先级: 原始消息(@) > CommandArg(纯数字QQ) > 仅命令(自己) > 错误
    返回: UID 字符串 或 None (表示格式错误或无效)
    """
    logger.debug(f"开始解析 UID: CommandArg={arg!r}, Event Type={type(event)}")

    # --- 优先级 1: 尝试从 event.raw_message 解析 @mention ---
    try:
        # 检查 event 是否有 raw_message 属性且为字符串
        raw_message_str = getattr(event, 'raw_message', None)
        if isinstance(raw_message_str, str):
            logger.debug(f"获取到 event.raw_message: '{raw_message_str}'")

            # 正则表达式匹配命令后紧跟一个 CQ:at 并允许末尾有空格
            # \s+ 匹配命令和 @ 之间的空格
            # (\d{5,11}) 捕获 5-11 位 QQ 号
            # \s*$ 匹配结尾的任意空格
            pattern = r"/(?:detail|info)\s+\[CQ:at,qq=(\d{5,11})\]\s*$" # $表示字符串结尾
            match = re.match(pattern, raw_message_str.strip()) # 使用 match 匹配开头, strip()去除首尾空格

            if match:
                uid = match.group(1)
                logger.info(f"从 raw_message 严格匹配到 @mention UID: {uid}")
                return uid
            else:
                logger.debug("raw_message 未能严格匹配 '命令 + @用户' 格式。")
                # 如果 raw_message 包含 @ 但格式不对，也应视为错误，这里不返回，让后续逻辑处理

        else:
            logger.debug("event.raw_message 不可用或类型不是字符串。")

    except Exception as e:
        logger.error(f"解析 event.raw_message 时发生异常: {e}", exc_info=True)
        # 发生异常时，不应继续，可能意味着解析逻辑有误或事件结构异常

    # --- 优先级 2: 如果 raw_message 未成功解析 @, 则检查 CommandArg 是否为纯数字 QQ ---
    logger.debug("未从 raw_message 成功解析 @mention，继续检查 CommandArg。")
    plain_text_arg = arg.extract_plain_text().strip()

    # 检查是否为 5-11 位纯数字
    if re.fullmatch(r"\d{5,11}", plain_text_arg):
        # 确保 arg 中只包含纯文本段，并且组合起来就是这个数字
        is_purely_text = True
        combined_text = ""
        for seg in arg:
            if seg.is_text():
                combined_text += seg.data.get("text", "")
            else:
                is_purely_text = False
                break
        
        if is_purely_text and combined_text.strip() == plain_text_arg:
            logger.info(f"从 CommandArg 纯文本提取到有效 QQ UID: {plain_text_arg}")
            return plain_text_arg
        else:
            logger.warning(f"CommandArg 文本为有效 QQ，但混杂非文本段或多余文本: {arg!r}")
            return None # 格式错误

    # --- 优先级 3: 检查是否仅发送了命令 (arg 为空) ---
    # 仅当 arg 为空，并且上面 raw_message 解析也没成功时执行
    if not arg:
        sender_id = str(event.get_user_id())
        logger.info(f"未提供有效参数 (@ 或纯数字 QQ)，默认查询发送者 UID: {sender_id}")
        return sender_id

    # --- 优先级 4: 其他所有情况视为格式错误 ---
    logger.warning(f"无法识别的命令参数格式: raw_message 解析失败且 CommandArg 内容无效: {arg!r}")
    return None


async def fetch_qq_detail(uid: str) -> dict:
    """调用 API 获取 QQ 详细信息 (保持不变)"""
    url = f"https://api.yyy001.com/api/qqdetail?qq={uid}"
    headers = {'User-Agent': 'NoneBot-Plugin-QQDetail/1.2'}
    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
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
        return {"response": {"code": e.response.status_code, "msg": f"API请求失败: {e.response.status_code}"}}
    except Exception as e:
        logger.exception(f"Unexpected error fetching detail for {uid}: {e}")
        return {"response": {"code": 500, "msg": f"处理API请求时发生内部错误"}}

# --- 主处理器 (保持不变) ---
@qq_detail.handle()
async def handle_info(bot: Bot, event: Union[PrivateMessageEvent, GroupMessageEvent], matcher: Matcher, arg: Message = CommandArg()):
    logger.debug(f"Received event (ID: {event.message_id}) type: {event.get_event_name()}")
    # 仍然记录这些，即使它们可能不准确，以供对比
    logger.debug(f"Handler看到 Raw Message Obj: {event.get_message()!r}")
    logger.debug(f"Handler看到 Command Argument (arg): {arg!r}")
    try:
        logger.debug(f"Handler看到 Event Raw Message Attr: {getattr(event, 'raw_message', 'N/A')}")
    except: pass

    # 获取目标 UID，使用最新的 get_uid 逻辑
    target_uid = await get_uid(event, arg)

    # 检查格式错误
    if target_uid is None:
        usage_message = __plugin_meta__.usage or "/detail <QQ号(5-11位)> 或 /detail @用户"
        await qq_detail.finish(f"命令格式错误、QQ号无效或包含多余参数。\n请使用：\n{usage_message}\n/detail (查询自己)")
        return

    # --- 后续逻辑 (白名单、API调用、发送结果) 保持不变 ---
    sender_id = str(event.get_user_id())
    superusers = getattr(bot.config, "superusers", set())
    is_sender_superuser = sender_id in superusers

    logger.debug(f"Query Target UID: {target_uid}, Sender UID: {sender_id}, Is Superuser: {is_sender_superuser}")

    if await is_whitelisted(target_uid) and not is_sender_superuser:
        if sender_id != target_uid:
            await qq_detail.finish(f"抱歉，您没有权限查询受保护用户 (UID: {target_uid}) 的信息。")

    data = await fetch_qq_detail(target_uid)

    response_data = data.get("response")
    if isinstance(response_data, dict) and response_data.get("code") == 200:
        nickname = response_data.get('name', '未知')
        headimg_url = response_data.get('headimg')
        details = [
            f"查询对象：{response_data.get('qq', 'N/A')}", f"昵称：{nickname}",
            f"QID：{response_data.get('qid', '未设置')}", f"性别：{response_data.get('sex', '未知')}",
            f"年龄：{response_data.get('age', '未知')}", f"等级：Lv.{response_data.get('level', 'N/A')}",
            f"VIP等级：{response_data.get('iVipLevel', 'N/A')}", f"注册时间：{response_data.get('RegistrationTime', '未知')}",
            f"签名：{response_data.get('sign', '无')}", f"IP城市：{response_data.get('ip_city', '未知')}"
        ]
        qq_detail_message_text = "\n".join(details)
        message_to_send = Message()
        if headimg_url:
            try: message_to_send.append(MessageSegment.image(headimg_url))
            except Exception as e: logger.warning(f"无法创建头像图片 for {headimg_url}: {e}")
        message_to_send.append(MessageSegment.text(qq_detail_message_text))
        await qq_detail.finish(message_to_send)
    else:
        error_msg = "未知错误"
        if isinstance(response_data, dict): error_msg = response_data.get('msg', error_msg)
        elif isinstance(data, dict) and "msg" in data: error_msg = data.get('msg', error_msg)
        logger.warning(f"获取 QQ 详细信息失败 UID {target_uid}. API Msg: {error_msg}")
        await qq_detail.finish(f"获取QQ信息失败 (UID: {target_uid})。\n原因：{error_msg}")