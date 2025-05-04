from nonebot.plugin import get_plugin_config
from pydantic import BaseSettings

class Config(BaseSettings):
    # 白名单配置
    qqdetail_whitelist: list[str] = []

config = get_plugin_config(Config)
