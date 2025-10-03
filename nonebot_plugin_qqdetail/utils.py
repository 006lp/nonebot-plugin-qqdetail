import textwrap
from io import BytesIO
from typing import Optional

import httpx
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot
from PIL import Image

from .config import Config
from .draw import create_image
from .transformers import DataTransformer


class ProfileProcessor:
    """用户资料处理器"""
    
    def __init__(self, config: Config):
        self.config = config
    
    async def get_profile_image(
        self,
        bot: Bot,
        target_id: str,
        group_id: Optional[str] = None
    ) -> bytes:
        """获取用户资料图片"""
        # 获取用户基本信息
        try:
            stranger_info = await bot.get_stranger_info(user_id=int(target_id), no_cache=True)
        except Exception as e:
            logger.error(f"[QQDetail] 获取用户 {target_id} 基本信息失败: {e}")
            raise ValueError("无效的QQ号。")
        
        # 获取群成员信息
        member_info = {}
        if group_id:
            try:
                member_info = await bot.get_group_member_info(
                    user_id=int(target_id),
                    group_id=int(group_id)
                )
            except Exception as e:
                logger.debug(f"[QQDetail] 获取用户 {target_id} 群成员信息失败: {e}")
        
        # 获取头像
        avatar = await self.get_avatar(target_id)
        if not avatar:
            logger.warning(f"[QQDetail] 目标 {target_id} 头像获取失败，使用默认白图。")
            with BytesIO() as buffer:
                Image.new("RGB", (640, 640), (255, 255, 255)).save(buffer, format="PNG")
                avatar = buffer.getvalue()
        
        # 转换信息
        reply = self.transform(stranger_info, member_info)

        # 生成图片
        try:
            image_bytes = create_image(avatar, reply, self.config.qqdetail_image_style_config)
        except Exception as e:
            logger.error(f"[QQDetail] 生成用户资料图片失败: {e}")
            raise ValueError("生成图片失败，请稍后重试。")
        return image_bytes
    
    def transform(self, info: dict, info2: dict) -> list:
        """转换用户信息为显示列表"""
        reply = []
        display_config = self.config.qqdetail_display_config
        
        # QQ号
        if user_id := info.get("user_id"):
            reply.append(f"QQ号：{user_id}")
        
        # 昵称
        if nickname := info.get("nickname"):
            reply.append(f"昵称：{nickname}")
        
        # 群昵称
        if display_config.card:
            if card := info2.get("card"):
                reply.append(f"群昵称：{card}")
        
        # 群头衔
        if display_config.title:
            if title := info2.get("title"):
                reply.append(f"头衔：{title}")
        
        # 性别
        if display_config.sex:
            sex = info.get("sex")
            sex_str = DataTransformer.format_sex(sex)
            if sex_str:
                reply.append(sex_str)
        
        # 生日相关
        birthday_config = display_config.birthday_config
        if birthday_config.enable and info.get("birthday_year") and info.get("birthday_month") and info.get("birthday_day"):
            reply.append(f"生日：{info['birthday_month']}-{info['birthday_day']}")

            if birthday_config.constellation:
                reply.append(f"星座：{DataTransformer.get_constellation(int(info['birthday_month']), int(info['birthday_day']))}")

            if birthday_config.zodiac:
                reply.append(f"生肖：{DataTransformer.get_zodiac(int(info['birthday_year']), int(info['birthday_month']), int(info['birthday_day']))}")

        # 年龄
        if display_config.age:
            if age := info.get("age"):
                reply.append(f"年龄：{age}岁")

        # 手机号码
        if display_config.phone_num:
            if phoneNum := info.get("phoneNum"):
                if phoneNum != "-":
                    reply.append(f"电话：{phoneNum}")

        # 邮箱
        if display_config.email:
            if eMail := info.get("eMail"):
                if eMail != "-":
                    reply.append(f"邮箱：{eMail}")

        # 邮编
        if display_config.post_code:
            if postCode := info.get("postCode"):
                if postCode != "-":
                    reply.append(f"邮编：{postCode}")

        # 现居地
        if display_config.address:
            country = info.get("country")
            province = info.get("province")
            city = info.get("city")
            address = DataTransformer.format_address(country, province, city)
            if address:
                reply.append(address)

        # 家乡
        if display_config.home_town:
            if homeTown := info.get("homeTown"):
                if homeTown != "0-0-0":
                    reply.append(f"来自：{DataTransformer.parse_home_town(homeTown)}")

        # 血型
        if display_config.blood_type:
            if kBloodType := info.get("kBloodType"):
                reply.append(f"血型：{DataTransformer.get_blood_type(int(kBloodType))}")

        # 职业
        if display_config.career:
            if makeFriendCareer := info.get("makeFriendCareer"):
                if makeFriendCareer != "0":
                    reply.append(f"职业：{DataTransformer.get_career(int(makeFriendCareer))}")

        # 备注
        if display_config.remark:
            if remark := info.get("remark"):
                reply.append(f"备注：{remark}")

        # 标签
        if display_config.labels:
            if labels := info.get("labels"):
                reply.append(f"标签：{labels}")

        # 风险账号
        if display_config.unfriendly:
            if info2.get("unfriendly"):
                reply.append("不良记录：有")

        # 机器人账号
        if info2.get("is_robot"):
            reply.append("机器人账号: 是")

        # VIP信息
        vip_config = display_config.vip_config
        if vip_config.enable:
            if info.get("is_vip"):
                reply.append("QQVIP：已开")

            if vip_config.years_vip and info.get("is_years_vip"):
                reply.append("年VIP：已开")

            if vip_config.vip_level and int(info.get("vip_level", 0)) != 0:
                reply.append(f"VIP等级：{info['vip_level']}级")

        # 连续登录天数
        if display_config.login_days:
            if int(info.get("login_days", 0)) != 0:
                reply.append(f"连续登录天数：{info['login_days']}")

        # 群等级
        if display_config.level:
            if level := info2.get("level"):
                reply.append(f"群等级：{int(level)}级")

        # 加群时间
        if display_config.join_time:
            if join_time := info2.get("join_time"):
                reply.append(f"加群时间：{DataTransformer.format_date(join_time)}")

        # QQ等级
        if qqLevel := info.get("qqLevel"):
            reply.append(f"QQ等级：{int(qqLevel)}级")

        # 注册时间
        if reg_time := info.get("reg_time"):
            reply.append(f"注册时间：{DataTransformer.format_timestamp(reg_time)}")

        # 个性签名
        if display_config.long_nick:
            if long_nick := info.get("long_nick"):
                lines = textwrap.wrap(text="签名：" + long_nick, width=15)
                reply.extend(lines)
        
        return reply
    
    @staticmethod
    async def get_avatar(user_id: str) -> Optional[bytes]:
        """获取用户头像"""
        avatar_url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(avatar_url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"[QQDetail] 未能获取目标头像: {e}")
            return None