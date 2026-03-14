"""
配置文件 - 日本活动信息自动推送系统
"""
import os
from pathlib import Path
from datetime import datetime

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 动态年月，用于搜索关键词
_now = datetime.now()
_YEAR = _now.year
_MONTH = _now.month
_YM = f"{_YEAR}年{_MONTH}月"        # 例：2026年3月
_YM_EN = f"{_YEAR}-{_MONTH:02d}"    # 例：2026-03

# ============ PushPlus配置 ============
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")

# ============ 推送时间配置 ============
PUSH_TIMES = [8, 16]

# ============ 关键词配置 ============

# 日本/东亚相关关键词（满足任一即匹配）
# 聚焦学术、文化、人文方向
JAPAN_KEYWORDS = [
    # 国家/地区
    "日本", "东亚", "东京", "日本文化", "日本历史", "日本思想",
    "日本文学", "日本社会", "日本政治", "日本经济", "日本哲学",
    "日本美术", "日本电影", "日本建筑",
    # 语言
    "日语", "日文",
    # 留学/交流
    "日本留学", "赴日", "日中", "中日", "日本研究", "东亚研究",
    # 文化体验
    "茶道", "花道", "和服", "日本传统", "和风", "禅",
    # 英文
    "Japan", "Japanese", "Tokyo", "Kyoto", "East Asia",
]

# 活动类型关键词 —— 判断是否是"活动/讲座"而非普通文章
ACTIVITY_KEYWORDS = [
    "讲座", "沙龙", "分享会", "研讨会", "论坛", "工作坊",
    "活动", "展览", "展会", "演出", "音乐会", "电影放映",
    "体验课", "公开课", "开放日", "见面会", "读书会",
    "预告", "活动预告", "学术活动", "会议", "年会",
    "workshop", "seminar", "lecture", "forum", "event",
]

# 报名/通知关键词
REGISTRATION_KEYWORDS = [
    "报名", "扫码", "二维码", "免费", "参会", "入场",
    "海报", "招募", "加入", "欢迎报名",
    "register", "sign up", "ticket", "free",
]

# ============ 研究方法关键词配置 ============
# 含这些词的讲座，不要求与日本/东亚相关，直接通过主题筛选
# 只需满足：含研究方法词 + 含活动词 + (线上 或 北京)
RESEARCH_METHOD_KEYWORDS = [
    # 方法论通称
    "研究方法", "研究设计", "方法论", "质性研究", "量化研究",
    "混合方法", "田野调查", "民族志", "案例研究", "文献综述",
    # 具体方法
    "访谈方法", "问卷设计", "话语分析", "内容分析", "比较研究",
    "文本分析", "档案研究", "口述历史", "数字人文",
    # 写作/发表
    "学术写作", "论文写作", "投稿技巧", "期刊发表",
    # 英文
    "research method", "methodology", "qualitative", "quantitative",
    "ethnography", "fieldwork", "discourse analysis",
]

# ============ 重点账号配置 ============
# 这些账号的文章不强制要求含"北京"，直接通过地点筛选
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
# 线下活动限定城市
OFFLINE_CITIES = ["北京", "Beijing", "BJ", "beijing"]

# 线上活动关键词
ONLINE_KEYWORDS = [
    "线上", "online", "直播", "腾讯会议", "zoom",
    "bilibili", "B站", "云端", "网络", "远程",
]

# 是否只推送北京/线上活动（对非重点账号生效）
ONLY_BEIJING_ONLINE = True

# ============ 信息来源配置 ============
PUBLIC_ACCOUNTS = [
    {"name": "东亚视界", "id": ""},
    {"name": "谓无名", "id": ""},
    {"name": "北大文科", "id": ""},
]

XIAOHONGSHU = {
    "enabled": True,
    "keywords": ["日本文化讲座 北京", "东亚研究 活动", "日语讲座", "日本留学分享"],
    "search_limit": 20
}

# 真实活动平台（直接抓取）
EVENT_PLATFORMS = [
    {
        "name": "豆瓣同城·北京日本文化",
        "url": "https://www.douban.com/location/beijing/events/rec/?tag=%E6%97%A5%E6%9C%AC",
        "type": "douban"
    },
    {
        "name": "活动行·日本文化",
        "url": "https://www.huodongxing.com/search?k=%E6%97%A5%E6%9C%AC%E6%96%87%E5%8C%96&city=1",
        "type": "huodongxing"
    },
    {
        "name": "活动行·日语讲座",
        "url": "https://www.huodongxing.com/search?k=%E6%97%A5%E8%AF%AD%E8%AE%B2%E5%BA%A7&city=1",
        "type": "huodongxing"
    },
]

# ============ 搜索引擎关键词 ============
# 三语覆盖（中文/英文/日文），不限地点，只要跟日本相关的讲座就抓

# 百度/搜狗专用关键词（中文为主）
BAIDU_SEARCH_KEYWORDS = [
    # 中文：日本相关讲座（带当前年月）
    f"日本 讲座 {_YM}",
    f"日本文化 讲座 {_YM}",
    f"日本 讲座 {_YEAR}",
    "日本文化 讲座 报名",
    "日本历史 讲座",
    "日本文学 讲座 分享会",
    f"东亚研究 讲座 {_YM}",
    "日语 公开课 报名",
    "日本思想 研讨会",
    "日本社会 学术讲座",
    "日本艺术 讲座 活动",
    # 中文：研究方法
    f"研究方法 讲座 {_YM}",
    "质性研究 方法论 讲座",
    "学术写作 讲座 报名",
    "数字人文 讲座",
]

# 必应/Google专用关键词（英文/日文为主）
BING_SEARCH_KEYWORDS = [
    # 英文：日本相关讲座（带当前年月）
    f"Japan lecture {_YM_EN}",
    f"Japan lecture {_YEAR}",
    "Japanese culture lecture event",
    f"Japan history seminar {_YEAR}",
    "East Asia lecture series",
    "Japanese literature talk",
    f"Japan studies workshop {_YEAR}",
    "Japanese language lecture free",
    # 英文：研究方法
    f"research methodology lecture {_YEAR}",
    "qualitative research workshop",
    "academic writing seminar",
    # 日文：日本相关讲座（带当前年）
    f"日本 講座 {_YEAR}",
    "日本文化 レクチャー",
    f"東アジア 講演会 {_YEAR}",
    "日本語 公開講座",
    "日本史 講座 無料",
]

# 搜狗微信文章专用关键词
SOGOU_WEIXIN_KEYWORDS = [
    f"日本 讲座 {_YM}",
    "日本文化 活动预告",
    "东亚研究 讲座预告",
    "日语 公开课",
    f"日本 研讨会 {_YM}",
    "研究方法 讲座",
    "学术写作 工作坊",
]

# 兼容旧版（合并三组）
WEB_SEARCH_KEYWORDS = BAIDU_SEARCH_KEYWORDS + BING_SEARCH_KEYWORDS[:5]

# ============ 采集配置 ============
REQUEST_DELAY = 2
MAX_PUSH_COUNT = 10
DEDUP_DAYS = 3

# ============ 日志配置 ============
LOG_LEVEL = "INFO"
LOG_FILE = BASE_DIR / "push.log"
