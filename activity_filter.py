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

        Args:
            activity: 活动信息

        Returns:
            是否已过期
        """
        # 如果没有时间信息，默认为有效
        text = activity.get("description", "") + activity.get("title", "")
        if not text:
            return False

        # 尝试提取日期
        date_patterns = [
            r"(\d{1,2})[月\-/](\d{1,2})",  # 月日
            r"(\d{4})[月\-/](\d{1,2})[月\-/](\d{1,2})",  # 年月日
        ]

        now = datetime.now()

        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    if len(match) == 2:  # 月日
                        month, day = int(match[0]), int(match[1])
                        # 假设是今年或明年
                        year = now.year
                        if month < now.month or (month == now.month and day < now.day):
                            year += 1
                        activity_date = datetime(year, month, day)
                    else:  # 年月日
                        year, month, day = int(match[0]), int(match[1]), int(match[2])
                        activity_date = datetime(year, month, day)

                    # 如果活动日期已过期（超过3天）
                    if activity_date < (now - timedelta(days=3)):
                        return True

                except Exception:
                    continue

        return False

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

    def filter_activities(self, activities: List[Dict]) -> List[Dict]:
        """
        筛选符合条件的活动

        Args:
            activities: 原始活动列表

        Returns:
            筛选后的活动列表
        """
        filtered = []

        for activity in activities:
            # 合并标题和描述进行检测
            text = f"{activity.get('title', '')} {activity.get('description', '')}"

            # 1. 检查是否与日本相关
            if not self.is_japan_related(text):
                continue

            # 2. 检查是否包含活动信息
            if not self.has_activity_info(text):
                continue

            # 3. 检查地点（北京/线上）
            if not self.is_beijing_or_online(text):
                continue

            # 4. 检查是否已过期
            if self.is_expired(activity):
                continue

            # 5. 检查是否重复
            if self.is_duplicate(activity):
                continue

            # 添加来源标签
            filtered.append(activity)

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
