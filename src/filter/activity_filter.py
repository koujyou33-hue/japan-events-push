"""
活动筛选引擎模块
用于过滤和筛选符合条件的日本相关活动
"""
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src import config


class ActivityFilter:
    """活动筛选器"""

    def __init__(self, data_file: Path = None):
        """
        初始化筛选器

        Args:
            data_file: 历史活动数据存储文件
        """
        if data_file is None:
            data_file = config.DATA_DIR / "activities.json"

        self.data_file = data_file
        self.history = self._load_history()

    def _load_history(self) -> Dict:
        """加载历史活动记录"""
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"activities": [], "last_update": ""}
        return {"activities": [], "last_update": ""}

    def _save_history(self):
        """保存历史活动记录"""
        self.history["last_update"] = datetime.now().isoformat()
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录出错: {e}")

    def is_japan_related(self, text: str) -> bool:
        """
        判断内容是否与日本相关

        Args:
            text: 待检测文本（标题+描述）

        Returns:
            是否匹配
        """
        if not text:
            return False

        text = text.lower()

        # 检查是否包含日本相关关键词
        for keyword in config.JAPAN_KEYWORDS:
            if keyword.lower() in text:
                return True

        return False

    def has_activity_info(self, text: str) -> bool:
        """
        判断内容是否包含活动信息（海报、报名等）

        Args:
            text: 待检测文本

        Returns:
            是否匹配
        """
        if not text:
            return False

        text = text.lower()

        # 检查是否包含活动类型关键词或报名信息
        for keyword in config.ACTIVITY_KEYWORDS + config.REGISTRATION_KEYWORDS:
            if keyword.lower() in text:
                return True

        return False

    def is_beijing_or_online(self, text: str) -> bool:
        """
        判断活动是否为北京线下或线上参与

        Args:
            text: 待检测文本

        Returns:
            是否符合地点要求
        """
        if not config.ONLY_BEIJING_ONLINE:
            return True

        if not text:
            return False

        text = text.lower()

        # 检查是否包含北京
        for city in config.OFFLINE_CITIES:
            if city.lower() in text:
                return True

        # 检查是否为线上活动
        for keyword in config.ONLINE_KEYWORDS:
            if keyword.lower() in text:
                return True

        return False

    def is_expired(self, activity: Dict) -> bool:
        """
        判断活动是否已过期

        策略：
        - 提取文本中所有可解析的日期，取最晚（最新）的一个来判断
        - 只有当"最晚的日期"早于今天，才认为活动过期（今天及以后的活动保留）
        - 无法解析任何日期时，默认为有效（不丢弃）

        Args:
            activity: 活动信息

        Returns:
            是否已过期
        """
        text = activity.get("description", "") + " " + activity.get("title", "")
        if not text.strip():
            return False

        now = datetime.now()
        # 今天零点：今天及以后的活动保留，昨天及更早的视为过期
        today = datetime(now.year, now.month, now.day)
        candidates = []

        # 模式1：年月日（优先级高）
        for m in re.findall(r"(\d{4})[年\-/.](\d{1,2})[月\-/.](\d{1,2})", text):
            try:
                y, mo, d = int(m[0]), int(m[1]), int(m[2])
                if 2020 <= y <= 2035 and 1 <= mo <= 12 and 1 <= d <= 31:
                    candidates.append(datetime(y, mo, d))
            except Exception:
                pass

        # 模式2：月日（无年份）
        for m in re.findall(r"(\d{1,2})[月](\d{1,2})[日号]", text):
            try:
                mo, d = int(m[0]), int(m[1])
                if 1 <= mo <= 12 and 1 <= d <= 31:
                    # 先假设今年
                    dt_this = datetime(now.year, mo, d)
                    # 若今年的日期已过去，再试明年（可能是明年的活动）
                    if dt_this < today:
                        dt_next = datetime(now.year + 1, mo, d)
                        candidates.append(dt_next)
                    else:
                        candidates.append(dt_this)
            except Exception:
                pass

        if not candidates:
            return False  # 无日期信息，保留

        # 取所有候选日期中最晚的一个，如果仍早于今天则过期
        latest = max(candidates)
        return latest < today

    def is_duplicate(self, activity: Dict) -> bool:
        """
        判断活动是否为重复推送

        Args:
            activity: 活动信息

        Returns:
            是否重复
        """
        title = activity.get("title", "")
        if not title:
            return False

        # 检查标题是否在历史记录中
        for old_activity in self.history.get("activities", []):
            old_title = old_activity.get("title", "")

            # 简单去重：标题相似度超过80%
            if self._similarity(title, old_title) > 0.8:
                # 检查是否在去重期内
                fetch_time = old_activity.get("fetch_time", "")
                if fetch_time:
                    try:
                        fetch_date = datetime.fromisoformat(fetch_time)
                        days_diff = (datetime.now() - fetch_date).days

                        if days_diff < config.DEDUP_DAYS:
                            return True
                    except Exception:
                        pass

        return False

    @staticmethod
    def _similarity(s1: str, s2: str) -> float:
        """计算两个字符串的相似度"""
        if not s1 or not s2:
            return 0.0

        # 简单的字符级相似度
        s1_set = set(s1)
        s2_set = set(s2)

        intersection = len(s1_set & s2_set)
        union = len(s1_set | s2_set)

        return intersection / union if union > 0 else 0.0

    def is_trusted_source(self, activity: Dict) -> bool:
        """
        判断是否来自重点关注的账号
        重点账号的文章不强制要求含"北京"地点信息
        """
        source = activity.get("source", "")
        for trusted in config.TRUSTED_SOURCES:
            if trusted in source:
                return True
        return False

    def is_online(self, text: str) -> bool:
        """
        判断是否为线上活动

        Args:
            text: 待检测文本

        Returns:
            是否包含线上关键词
        """
        if not text:
            return False
        text_lower = text.lower()
        for keyword in config.ONLINE_KEYWORDS:
            if keyword.lower() in text_lower:
                return True
        return False

    def is_research_method_related(self, text: str) -> bool:
        """
        判断内容是否与研究方法/学术方法论相关

        含研究方法词的讲座不要求与日本/东亚相关，直接通过主题筛选

        Args:
            text: 待检测文本

        Returns:
            是否匹配研究方法关键词
        """
        if not text:
            return False
        text_lower = text.lower()
        for keyword in config.RESEARCH_METHOD_KEYWORDS:
            if keyword.lower() in text_lower:
                return True
        return False

    def filter_activities(self, activities: List[Dict]) -> List[Dict]:
        """
        筛选符合条件的活动

        筛选逻辑（3条路径，满足任一即通过）：

        路径A — 日本/东亚相关讲座（不限任何地点）：
            含日本词 AND 含活动词
            → 线上线下均可，全国/全球皆推

        路径B — 研究方法讲座（不要求日本相关）：
            含研究方法词 AND 含活动词 AND (线上 OR 北京)
            → 方法论/学术写作讲座，限线上或北京

        路径C — 重点账号文章（来源可信，直接通过）：
            来自信任来源 AND 含活动词
            → 东亚视界、谓无名等，不限主题和地点

        Args:
            activities: 原始活动列表

        Returns:
            筛选后的活动列表
        """
        filtered = []

        for activity in activities:
            text = f"{activity.get('title', '')} {activity.get('description', '')}"

            # 先做通用检查：是否已过期 / 是否重复推送
            if self.is_expired(activity):
                continue
            if self.is_duplicate(activity):
                continue

            is_activity = self.has_activity_info(text)
            if not is_activity:
                continue  # 无论哪条路径，都必须是"活动"而非普通文章

            is_japan = self.is_japan_related(text)
            is_online = self.is_online(text)
            is_beijing = "北京" in text or "beijing" in text.lower()
            is_research = self.is_research_method_related(text)
            is_trusted = self.is_trusted_source(activity)

            # 路径A：日本相关 → 直接通过，完全不限地点
            if is_japan:
                filtered.append(activity)
                continue

            # 路径B：研究方法讲座 + 线上或北京 → 通过（不要求日本相关）
            if is_research and (is_online or is_beijing):
                filtered.append(activity)
                continue

            # 路径C：重点账号文章 → 直接通过（来源可信）
            if is_trusted:
                filtered.append(activity)
                continue

        return filtered

    def add_to_history(self, activities: List[Dict]):
        """
        将活动添加到历史记录

        Args:
            activities: 活动列表
        """
        if "activities" not in self.history:
            self.history["activities"] = []

        self.history["activities"].extend(activities)

        # 清理过期的历史记录（超过30天）
        cutoff_date = datetime.now() - timedelta(days=30)
        self.history["activities"] = [
            a for a in self.history["activities"]
            if a.get("fetch_time")
            and datetime.fromisoformat(a["fetch_time"]) > cutoff_date
        ]

        self._save_history()


def test_filter():
    """测试筛选器"""
    # 模拟活动数据
    test_activities = [
        {
            "title": "【北京】日本文化讲座 - 带你了解日本茶道",
            "url": "https://example.com/1",
            "description": "时间：2026年3月20日 地点：北京朝阳区 报名链接：...",
            "source": "公众号"
        },
        {
            "title": "日本留学分享会 - 申请日本名校",
            "url": "https://example.com/2",
            "description": "线上直播 时间：本周六",
            "source": "小红书"
        },
        {
            "title": "日本料理美食节",
            "url": "https://example.com/3",
            "description": "上海世博展览馆",
            "source": "网站"
        },
        {
            "title": "日本动漫展会",
            "url": "https://example.com/4",
            "description": "北京国家会议中心 2026年4月",
            "source": "活动行"
        }
    ]

    filter_engine = ActivityFilter()
    filtered = filter_engine.filter_activities(test_activities)

    print(f"原始活动数: {len(test_activities)}")
    print(f"筛选后活动数: {len(filtered)}")

    for activity in filtered:
        print(f"\n✓ {activity['title']}")
        print(f"  来源: {activity['source']}")


if __name__ == "__main__":
    test_filter()
