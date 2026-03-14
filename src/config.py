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
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")

# ============ 推送时间配置 ============
PUSH_TIMES = [8, 16]

# ============ 关键词配置 ============

# 日本/东亚相关关键词（满足任一即匹配）
JAPAN_KEYWORDS = [
    "日本", "东亚", "东京", "日本文化", "日本历史", "日本思想",
    "日本文学", "日本社会", "日本政治", "日本经济", "日本哲学",
    "日本美术", "日本电影", "日本建筑",
    "日语", "日文",
    "日本留学", "赴日", "日中", "中日", "日本研究", "东亚研究",
    "茶道", "花道", "和服", "日本传统", "和风", "禅",
    "Japan", "Japanese", "Tokyo", "Kyoto", "East Asia",
]

# 活动类型关键词
ACTIVITY_KEYWORDS = [
    "讲座", "沙龙", "分享会", "研讨会", "论坛", "工作坊",
    "活动", "展览", "展会", "演出", "音乐会", "电影放映",
    "体验课", "公开课", "开放日", "见面会", "读书会",
    "预告", "活动预告", "学术活动", "会议", "年会",
    "workshop", "seminar", "lecture", "forum", "event",
    "講座", "レクチャー", "セミナー", "イベント", "勉強会",
]

# 报名/通知关键词
REGISTRATION_KEYWORDS = [
    "报名", "扫码", "二维码", "免费", "参会", "入场",
    "海报", "招募", "加入", "欢迎报名",
    "register", "sign up", "ticket", "free",
]

# ============ 研究方法关键词配置 ============
RESEARCH_METHOD_KEYWORDS = [
    "研究方法", "研究设计", "方法论", "质性研究", "量化研究",
    "混合方法", "田野调查", "民族志", "案例研究", "文献综述",
    "访谈方法", "问卷设计", "话语分析", "内容分析", "比较研究",
    "文本分析", "档案研究", "口述历史", "数字人文",
    "学术写作", "论文写作", "投稿技巧", "期刊发表",
    "research method", "methodology", "qualitative", "quantitative",
    "ethnography", "fieldwork", "discourse analysis",
]

# ============ 重点账号配置 ============
TRUSTED_SOURCES = [
    "公众号·东亚视界",
    "公众号·谓无名",
    "公众号·北大文科",
    "小红书·日々一点勉強",
    "小红书·日本人文学爱好者",
    "小红书·日语渔老师",
    "小红书·北京文艺活动资讯",
]

# ============ 地点筛选配置 ============
OFFLINE_CITIES = ["北京", "Beijing", "BJ", "beijing"]

ONLINE_KEYWORDS = [
    "线上", "online", "直播", "腾讯会议", "zoom",
    "bilibili", "B站", "云端", "网络", "远程",
]

ONLY_BEIJING_ONLINE = True

# ============ 信息来源配置 ============
PUBLIC_ACCOUNTS = [
    {"name": "东亚视界", "id": ""},
    {"name": "谓无名", "id": ""},
    {"name": "北大文科", "id": ""},
]

XIAOHONGSHU = {
    "enabled": True,
    "keywords": ["日本文化讲座", "东亚研究 活动", "日语讲座", "日本留学分享"],
    "search_limit": 20
}

EVENT_PLATFORMS = [
    {
        "name": "豆瓣同城·日本",
        "url": "https://www.douban.com/location/beijing/events/rec/?tag=%E6%97%A5%E6%9C%AC",
        "type": "douban"
    },
    {
        "name": "活动行·日本文化",
        "url": "https://www.huodongxing.com/search?k=%E6%97%A5%E6%9C%AC%E6%96%87%E5%8C%96&city=1",
        "type": "huodongxing"
    },
]

# ============ 三路搜索引擎关键词 ============

# 百度专用（中文为主）
BAIDU_SEARCH_KEYWORDS = [
    "日本 讲座 2026",
    "日本文化 讲座 报名",
    "日本历史 讲座",
    "日本文学 讲座 分享会",
    "东亚研究 讲座 2026",
    "日语 公开课 报名",
    "日本思想 研讨会",
    "日本社会 学术讲座",
    "日本艺术 讲座 活动",
    "研究方法 讲座 2026",
    "质性研究 方法论 讲座",
    "学术写作 讲座 报名",
    "数字人文 讲座",
]

# 必应专用（英文+日文）
BING_SEARCH_KEYWORDS = [
    "Japan lecture 2026",
    "Japanese culture lecture event",
    "Japan history seminar 2026",
    "East Asia lecture series",
    "Japanese literature talk",
    "Japan studies workshop 2026",
    "Japanese language lecture free",
    "research methodology lecture 2026",
    "qualitative research workshop",
    "academic writing seminar",
    "日本 講座 2026",
    "日本文化 レクチャー",
    "東アジア 講演会 2026",
    "日本語 公開講座",
    "日本史 講座 無料",
]

# 搜狗微信专用（公众号文章）
SOGOU_WEIXIN_KEYWORDS = [
    "日本 讲座 报名",
    "日本文化 活动预告",
    "东亚研究 讲座预告",
    "日语 公开课",
    "日本 研讨会 2026",
    "研究方法 讲座",
    "学术写作 工作坊",
]

# 兼容旧版
WEB_SEARCH_KEYWORDS = BAIDU_SEARCH_KEYWORDS + BING_SEARCH_KEYWORDS[:5]

# ============ 采集配置 ============
REQUEST_DELAY = 2
MAX_PUSH_COUNT = 10
DEDUP_DAYS = 3

# ============ 日志配置 ============
LOG_LEVEL = "INFO"
LOG_FILE = BASE_DIR / "push.log"
