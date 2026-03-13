"""
配置文件 - 日本活动信息自动推送系统
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ============ PushPlus配置 ============
# 从环境变量获取PushPlus TOKEN
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")

# ============ 推送时间配置 ============
# 推送时间（小时，24小时制）
PUSH_TIMES = [8, 16]

# ============ 关键词配置 ============
# 日本相关关键词（满足任一即匹配）
JAPAN_KEYWORDS = [
    "日本", "日本文化", "日本经济", "日本社会", "日本历史",
    "日本思想", "日本教育", "日本留学", "日语", "日本料理",
    "和风", "和服", "茶道", "花道", "剑道", "空手道",
    " Samurai", "Tokyo", "Kyoto", "Osaka",
    "二次元", "动漫", "J-POP", "杰尼斯",
    "日本签证", "赴日", "日本旅行", "东京大学", "早稻田大学"
]

# 活动类型关键词
ACTIVITY_KEYWORDS = [
    "活动", "讲座", "沙龙", "分享会", "展览", "展会",
    "音乐会", "演唱会", "戏剧", "电影", "见面会",
    "工作坊", "体验课", "公开课", "研讨会", "论坛",
    "招募", "报名", "的海报", "宣传", "开幕", "开幕"
]

# 报名/海报关键词（用于筛选有报名链接的活动）
REGISTRATION_KEYWORDS = [
    "报名", "报名链接", "报名通道", "二维码", "扫码",
    "海报", "活动海报", "宣传海报", "报名费",
    "link", "报名表", "加入我们", "参会",
    "ticket", "register", "sign up"
]

# ============ 地点筛选配置 ============
# 线下活动限定城市
OFFLINE_CITIES = ["北京", "Beijing", "BJ", "beijing"]

# 线上活动关键词（包含任一即匹配）
ONLINE_KEYWORDS = [
    "线上", "online", "直播", "LIVE", "腾讯会议",
    "zoom", "bilibili", "B站", "直播间", "云端"
]

# 是否只推送北京/线上活动
ONLY_BEIJING_ONLINE = True

# ============ 信息来源配置 ============
# 公众号配置
PUBLIC_ACCOUNTS = [
    {"name": "日本物语", "id": ""},
    {"name": "日本通", "id": ""},
    {"name": "东京生活指南", "id": ""},
    # 添加更多公众号名称
]

# 小红书配置
XIAOHONGSHU = {
    "enabled": True,
    "keywords": ["日本活动", "北京日本活动", "日本文化讲座", "日语活动", "日本沙龙"],
    "search_limit": 20  # 每次搜索获取数量
}

# 网站RSS源配置
RSS_SOURCES = [
    {"name": "豆瓣同城-日本文化", "url": "https://www.douban.com/location/events?tag=%E6%97%A5%E6%9C%AC&city=%E5%8C%97%E4%BA%AC"},
    {"name": "活动行-日本", "url": "https://www.huodongxing.com/search?k=%E6%97%A5%E6%9C%AC"},
    # 添加更多RSS源
]

# ============ 采集配置 ============
# 请求间隔（秒），避免被封
REQUEST_DELAY = 2

# 单次最大推送活动数量
MAX_PUSH_COUNT = 10

# 去重时间（天），相同活动在N天内不重复推送
DEDUP_DAYS = 3

# ============ 日志配置 ============
LOG_LEVEL = "INFO"
LOG_FILE = BASE_DIR / "push.log"
