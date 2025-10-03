import math
from datetime import datetime, timedelta
from typing import Dict, Optional
from threading import Lock

from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot
from nonebot.permission import SUPERUSER

from .config import Config


class RateLimitService:
    """速率限制服务"""

    def __init__(self):
        self._lock = Lock()
        self._last_command_time: Dict[str, datetime] = {}

    def check_rate_limit(self, user_id: str, group_id: Optional[str], config: Config) -> Optional[str]:
        """检查速率限制"""
        rate_config = config.qqdetail_rate_limit_config

        # 如果速率为0，表示不限制
        if rate_config.time <= 0:
            return None

        # 检查用户是否在白名单中
        if user_id in rate_config.white_users:
            return None

        # 检查群聊是否在白名单中
        if group_id and group_id in rate_config.white_groups:
            return None

        # 检查速率限制
        user_key = f"{user_id}_{group_id or 'private'}"
        current_time = datetime.now()

        with self._lock:
            if user_key in self._last_command_time:
                last_time = self._last_command_time[user_key]
                time_diff = current_time - last_time

                if time_diff < timedelta(minutes=rate_config.time):
                    remaining_minutes = rate_config.time - time_diff.total_seconds() / 60
                    return f"请求过于频繁，请等待 {math.ceil(remaining_minutes)} 分钟后再试。"

            # 更新最后使用时间
            self._last_command_time[user_key] = current_time
            return None


class PermissionService:
    """权限检查服务"""

    @staticmethod
    async def check_admin_permission(
        bot: Bot,
        user_id: str,
        group_id: Optional[str],
        only_admin: bool,
        target_id: str,
        is_superuser: bool = False
    ) -> Optional[str]:
        """检查管理员权限"""
        if not only_admin or target_id == user_id:
            return None

        # 检查是否为超级用户
        if is_superuser:
            return None

        # 检查群管理员权限
        if group_id:
            try:
                member_info = await bot.get_group_member_info(
                    group_id=int(group_id),
                    user_id=int(user_id)
                )
                if member_info.get("role") in ["admin", "owner"]:
                    return None
            except Exception as e:
                logger.warning(f"检查管理员权限失败: {e}")
                return "权限检查失败"

        return f"您(ID: {user_id})的权限不足以使用此指令。"


class QQDetailService:
    """QQ资料服务"""

    def __init__(self, config: Config):
        self.config = config

    def is_in_blacklist(self, user_id: str) -> bool:
        """检查是否在黑名单中"""
        return user_id in self.config.qqdetail_box_blacklist

    def is_group_whitelisted(self, group_id: str) -> bool:
        """检查群聊是否在白名单中"""
        if not self.config.qqdetail_whitelist_groups:
            return True
        return group_id in self.config.qqdetail_whitelist_groups

    def should_auto_box_increase(self, group_id: str) -> bool:
        """检查是否自动获取入群用户信息"""
        auto_config = self.config.qqdetail_auto_box_config
        if not auto_config.increase_box:
            return False
        if auto_config.white_groups and group_id not in auto_config.white_groups:
            return False
        return True

    def should_auto_box_decrease(self, group_id: str) -> bool:
        """检查是否自动获取退群用户信息"""
        auto_config = self.config.qqdetail_auto_box_config
        if not auto_config.decrease_box:
            return False
        if auto_config.white_groups and group_id not in auto_config.white_groups:
            return False
        return True