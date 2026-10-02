from nonebot import require
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="QQ 资料卡片",
    description="通过 OneBot V11 查询 QQ 公开资料，支持卡片、通知与撤回",
    usage="qqdetail [QQ号/@用户 ...] [--text|--image]；未指定目标时查询自己",
    type="application",
    homepage="https://github.com/006lp/nonebot-plugin-qqdetail",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

require("nonebot_plugin_alconna")

from . import handlers as handlers
