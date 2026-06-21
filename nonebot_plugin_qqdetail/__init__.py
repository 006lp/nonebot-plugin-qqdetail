from nonebot import require
from nonebot.plugin import PluginMetadata
from . import command as command
from .config import Config

require("nonebot_plugin_alconna")

__plugin_meta__ = PluginMetadata(
    name="QQ 详细信息查询",
    description="通过 OneBot V11 查询 QQ 用户公开资料与群成员资料",
    usage="发送 /qqdetail [QQ号]、/qqinfo [QQ号]，或在命令后 At 用户查询资料",
    type="application",
    config=Config,
    supported_adapters={"~onebot.v11"},
)
