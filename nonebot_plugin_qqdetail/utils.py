import textwrap
from datetime import datetime
from io import BytesIO
from typing import Optional

import httpx
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot
from PIL import Image

from .config import Config
from .draw import create_image


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
            image_bytes = create_image(avatar, reply)
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
            if sex == "male":
                reply.append("性别：男")
            elif sex == "female":
                reply.append("性别：女")
        
        # 生日相关
        birthday_config = display_config.birthday_config
        if birthday_config.enable and info.get("birthday_year") and info.get("birthday_month") and info.get("birthday_day"):
            reply.append(f"生日：{info['birthday_month']}-{info['birthday_day']}")
            
            if birthday_config.constellation:
                reply.append(f"星座：{self.get_constellation(int(info['birthday_month']), int(info['birthday_day']))}")
            
            if birthday_config.zodiac:
                reply.append(f"生肖：{self.get_zodiac(int(info['birthday_year']), int(info['birthday_month']), int(info['birthday_day']))}")
        
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
            if country == "中国" and (province or city):
                reply.append(f"现居：{province or ''}-{city or ''}")
            elif country:
                reply.append(f"现居：{country}")
        
        # 家乡
        if display_config.home_town:
            if homeTown := info.get("homeTown"):
                if homeTown != "0-0-0":
                    reply.append(f"来自：{self.parse_home_town(homeTown)}")
        
        # 血型
        if display_config.blood_type:
            if kBloodType := info.get("kBloodType"):
                reply.append(f"血型：{self.get_blood_type(int(kBloodType))}")
        
        # 职业
        if display_config.career:
            if makeFriendCareer := info.get("makeFriendCareer"):
                if makeFriendCareer != "0":
                    reply.append(f"职业：{self.get_career(int(makeFriendCareer))}")
        
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
                reply.append(f"加群时间：{datetime.fromtimestamp(join_time).strftime('%Y-%m-%d')}")
        
        # QQ等级
        if qqLevel := info.get("qqLevel"):
            reply.append(f"QQ等级：{int(qqLevel)}级")
        
        # 注册时间
        if reg_time := info.get("reg_time"):
            reply.append(f"注册时间：{datetime.fromtimestamp(reg_time).strftime('%Y-%m-%d %H:%M:%S')}")
        
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
    
    @staticmethod
    def get_constellation(month: int, day: int) -> str:
        """根据生日获取星座"""
        constellations = {
            "白羊座": ((3, 21), (4, 19)),
            "金牛座": ((4, 20), (5, 20)),
            "双子座": ((5, 21), (6, 20)),
            "巨蟹座": ((6, 21), (7, 22)),
            "狮子座": ((7, 23), (8, 22)),
            "处女座": ((8, 23), (9, 22)),
            "天秤座": ((9, 23), (10, 22)),
            "天蝎座": ((10, 23), (11, 21)),
            "射手座": ((11, 22), (12, 21)),
            "摩羯座": ((12, 22), (1, 19)),
            "水瓶座": ((1, 20), (2, 18)),
            "双鱼座": ((2, 19), (3, 20)),
        }
        
        for constellation, ((start_month, start_day), (end_month, end_day)) in constellations.items():
            if (month == start_month and day >= start_day) or (month == end_month and day <= end_day):
                return constellation
            if start_month > end_month:
                if (month == start_month and day >= start_day) or (month == end_month + 12 and day <= end_day):
                    return constellation
        return f"星座{month}-{day}"
    
    @staticmethod
    def get_zodiac(year: int, month: int, day: int) -> str:
        """根据生日获取生肖"""
        base_year = 2024
        zodiacs = ["龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪", "鼠", "牛", "虎", "兔"]
        
        if (month == 1) or (month == 2 and day < 4):
            zodiac_year = year - 1
        else:
            zodiac_year = year
        
        zodiac_index = (zodiac_year - base_year) % 12
        return zodiacs[zodiac_index]
    
    @staticmethod
    def get_career(num: int) -> str:
        """根据代码获取职业"""
        career = {
            1: "计算机/互联网/通信",
            2: "生产/工艺/制造",
            3: "医疗/护理/制药",
            4: "金融/银行/投资/保险",
            5: "商业/服务业/个体经营",
            6: "文化/广告/传媒",
            7: "娱乐/艺术/表演",
            8: "律师/法务",
            9: "教育/培训",
            10: "公务员/行政/事业单位",
            11: "模特",
            12: "空姐",
            13: "学生",
            14: "其他",
        }
        return career.get(num, f"职业{num}")
    
    @staticmethod
    def get_blood_type(num: int) -> str:
        """根据代码获取血型"""
        blood_types = {1: "A型", 2: "B型", 3: "O型", 4: "AB型", 5: "其他"}
        return blood_types.get(num, f"血型{num}")
    
    @staticmethod
    def parse_home_town(home_town_code: str) -> str:
        """解析家乡代码"""
        country_map = {
            "49": "中国",
            "250": "俄罗斯",
            "222": "特里尔",
            "217": "法国",
        }
        province_map = {
            "98": "北京",
            "99": "天津/辽宁",
            "100": "冀/沪/吉",
            "101": "苏/豫/晋/黑/渝",
            "102": "浙/鄂/蒙/川",
            "103": "皖/湘/黔/陕",
            "104": "闽/粤/滇/甘/台",
            "105": "赣/桂/藏/青/港",
            "106": "鲁/琼/陕/宁/澳",
            "107": "新疆",
        }
        
        country_code, province_code, _ = home_town_code.split("-")
        country = country_map.get(country_code, f"外国{country_code}")
        
        if country_code == "49":  # 中国
            if province_code != "0":
                province = province_map.get(province_code, f"{province_code}省")
                return province
            else:
                return country
        else:
            return country