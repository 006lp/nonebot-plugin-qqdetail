from nonebot.plugin import PluginMetadata, inherit_supported_adapters, require

require("nonebot_plugin_alconna")
require("nonebot_plugin_localstore")

from . import matchers as matchers
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="QQ资料查询",
    description="查询QQ用户的详细资料信息，支持头像、昵称、等级等多种信息展示",
    usage="""
指令：
/box [QQ号/@用户]  - 查询指定用户资料（不指定则查询自己）

功能：
- 支持查询QQ用户详细资料
- 自动获取新入群/退群用户信息
- 可配置显示项目和权限控制
- 速率限制防止滥用
    """.strip(),
    type="application",
    homepage="https://github.com/006lp/nonebot-plugin-qqdetail",
    config=Config,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna")
)