from datetime import datetime
from typing import Dict, Optional


class DataTransformer:
    """数据转换工具类"""

    CAREER_MAP = {
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

    BLOOD_TYPE_MAP = {1: "A型", 2: "B型", 3: "O型", 4: "AB型", 5: "其他"}

    CONSTELLATIONS = {
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

    COUNTRY_MAP = {
        "49": "中国",
        "250": "俄罗斯",
        "222": "特里尔",
        "217": "法国",
    }

    PROVINCE_MAP = {
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

    @staticmethod
    def get_constellation(month: int, day: int) -> str:
        """根据生日获取星座"""
        for constellation, ((start_month, start_day), (end_month, end_day)) in DataTransformer.CONSTELLATIONS.items():
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
        return DataTransformer.CAREER_MAP.get(num, f"职业{num}")

    @staticmethod
    def get_blood_type(num: int) -> str:
        """根据代码获取血型"""
        return DataTransformer.BLOOD_TYPE_MAP.get(num, f"血型{num}")

    @staticmethod
    def parse_home_town(home_town_code: str) -> str:
        """解析家乡代码"""
        country_code, province_code, _ = home_town_code.split("-")
        country = DataTransformer.COUNTRY_MAP.get(country_code, f"外国{country_code}")

        if country_code == "49":  # 中国
            if province_code != "0":
                province = DataTransformer.PROVINCE_MAP.get(province_code, f"{province_code}省")
                return province
            else:
                return country
        else:
            return country

    @staticmethod
    def format_sex(sex: Optional[str]) -> str:
        """格式化性别"""
        if sex == "male":
            return "性别：男"
        elif sex == "female":
            return "性别：女"
        return ""

    @staticmethod
    def format_address(country: Optional[str], province: Optional[str], city: Optional[str]) -> str:
        """格式化地址"""
        if country == "中国" and (province or city):
            return f"现居：{province or ''}-{city or ''}"
        elif country:
            return f"现居：{country}"
        return ""

    @staticmethod
    def format_timestamp(timestamp: int) -> str:
        """格式化时间戳"""
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def format_date(timestamp: int) -> str:
        """格式化日期"""
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')