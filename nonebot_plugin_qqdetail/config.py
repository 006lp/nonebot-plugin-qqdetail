from typing import List, Optional
from pydantic import BaseModel, Field


class BirthdayConfig(BaseModel):
    """生日显示配置"""
    enable: bool = Field(default=True, description="显示用户生日")
    constellation: bool = Field(default=True, description="显示用户星座")
    zodiac: bool = Field(default=True, description="显示用户生肖")


class VipConfig(BaseModel):
    """VIP显示配置"""
    enable: bool = Field(default=True, description="是否显示用户VIP信息")
    years_vip: bool = Field(default=True, description="是否显示用户年VIP信息")
    vip_level: bool = Field(default=True, description="是否显示用户VIP等级")


class DisplayConfig(BaseModel):
    """显示配置"""
    card: bool = Field(default=True, description="显示用户群昵称")
    title: bool = Field(default=True, description="显示用户群头衔")
    sex: bool = Field(default=True, description="显示用户性别")
    birthday_config: BirthdayConfig = Field(default_factory=BirthdayConfig)
    age: bool = Field(default=True, description="显示用户年龄")
    phone_num: bool = Field(default=True, description="显示用户手机号码")
    email: bool = Field(default=True, description="显示用户电子邮箱")
    post_code: bool = Field(default=True, description="显示用户邮政编码")
    home_town: bool = Field(default=True, description="显示用户家乡城市")
    address: bool = Field(default=True, description="显示用户现居城市")
    blood_type: bool = Field(default=True, description="显示用户血型")
    career: bool = Field(default=True, description="显示用户职业")
    remark: bool = Field(default=True, description="显示用户备注")
    labels: bool = Field(default=True, description="显示用户个性标签")
    unfriendly: bool = Field(default=True, description="显示用户是否为风险账号")
    vip_config: VipConfig = Field(default_factory=VipConfig)
    login_days: bool = Field(default=True, description="显示用户连续登录天数")
    level: bool = Field(default=True, description="显示用户群等级")
    join_time: bool = Field(default=True, description="显示用户加群时间")
    long_nick: bool = Field(default=True, description="显示用户个性签名")


class AutoBoxConfig(BaseModel):
    """自动获取配置"""
    increase_box: bool = Field(default=False, description="自动获取新进群的用户信息")
    decrease_box: bool = Field(default=False, description="自动获取退群用户的信息")
    white_groups: List[str] = Field(default_factory=list, description="群聊白名单")


class RateLimitConfig(BaseModel):
    """速率限制配置"""
    time: int = Field(default=0, description="速率限制时间(分钟)，0表示不限制")
    white_groups: List[str] = Field(default_factory=list, description="群聊白名单")
    white_users: List[str] = Field(default_factory=list, description="用户白名单")


class Config(BaseModel):
    """插件配置"""
    qqdetail_only_admin: bool = Field(default=False, description="仅管理员可用")
    qqdetail_box_blacklist: List[str] = Field(default_factory=list, description="信息保护用户")
    qqdetail_whitelist_groups: List[str] = Field(default_factory=list, description="群聊白名单")
    qqdetail_auto_box_config: AutoBoxConfig = Field(default_factory=AutoBoxConfig)
    qqdetail_rate_limit_config: RateLimitConfig = Field(default_factory=RateLimitConfig)
    qqdetail_display_config: DisplayConfig = Field(default_factory=DisplayConfig)
