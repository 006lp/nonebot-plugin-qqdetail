import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment, Bot, Event
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from .config import config
from nonebot.matcher import Matcher

__plugin_meta__ = PluginMetadata(
    name="QQ详细信息查询",
    description="让机器人QQ详细信息",
    usage="/qqdetail <uid>或/qqdetail @Nickname",
    type="application",
    homepage="https://github.com/006lp/nonebot-plugin-qqdetail",
    supported_adapters={"~onebot.v11"}
)

# 创建命令处理器
qq_detail = on_command("detail", aliases={"info"}, priority=5)

# 白名单检查函数
async def is_whitelisted(uid: str) -> bool:
    return uid in config.qqdetail_whitelist

# 获取用户的UID
async def get_uid(event: Event) -> str:
    if event.message:
        # 如果是 @用户 的形式
        for segment in event.message:
            if segment.type == "at":
                return segment.data["qq"]
    return str(event.sender.user_id)  # 如果没有提供UID，默认是发送者的UID

# 获取QQ信息的函数
async def fetch_qq_detail(uid: str) -> dict:
    url = f"https://api.yyy001.com/api/qqdetail?qq={uid}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        return data

# 处理 /detail 命令
@qq_detail.handle()
async def handle_info(bot: Bot, event: Event, matcher: Matcher, arg: CommandArg = CommandArg()):
    # ✨ 阻止其他 matcher（包括其他插件）继续处理
    matcher.stop_propagation()  

    # 获取UID，如果没有提供，默认使用发送者的UID
    uid = await get_uid(event)
    
    # 如果UID在白名单内，并且用户不是superuser
    if await is_whitelisted(uid) and str(event.user_id) not in bot.config.superusers:
        if event.user_id != uid:
            await qq_info.finish("你无法查看这个QQ账号的详细信息。")
    
    # 获取QQ信息
    data = await fetch_qq_detail(uid)
    
    if data.get("response", {}).get("code") == 200:
        # 格式化返回信息
        response = data["response"]
        qq_detail_message = (
            f"QQ账号：{response['qq']}\n"
            f"QID：{response['qid']}\n"
            f"昵称：{response['name']}\n"
            f"性别：{response['sex']}\n"
            f"年龄：{response['age']}\n"
            f"头像：{response['headimg']}\n"
            f"等级：{response['level']}\n"
            f"VIP等级：{response['iVipLevel']}\n"
            f"注册时间：{response['RegistrationTime']}\n"
            f"学校：{response['school_label']}\n"
            f"签名：{response['sign']}\n"
            f"IP城市：{response['ip_city']}\n"
        )
        await qq_detail.finish(qq_detail_message)
    else:
        await qq_detail.finish(f"获取QQ信息失败：{data.get('response', {}).get('msg', '未知错误')}")

