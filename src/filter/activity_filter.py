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
        """判断内容是否与日本/东亚相关"""
        if not text:
            return False
        text = text.lower()
        for keyword in config.JAPAN_KEYWORDS:
            if keyword.lower() in text:
                return True
        return False

    def has_activity_info(self, text: str) -> bool:
        """判断内容是否包含活动信息（讲座、报名等）"""
        if not text:
            return False
        text = text.lower()
        for keyword in config.ACTIVITY_KEYWORDS + config.REGISTRATION_KEYWORDS:
            if keyword.lower() in text:
                return True
        return False

    def is_beijing_or_online(self, text: str) -> bool:
        """判断活动是否为北京线下或线上参与"""
        if not config.ONLY_BEIJING_ONLINE:
            return True
        if not text:
            return False
        text = text.lower()
        for city in config.OFFLINE_CITIES:
            if city.lower() in text:
                return True
        for keyword in config.ONLINE_KEYWORDS:
            if keyword.lower() in text:
                return True
        return False

    def is_online(self, text: str) -> bool:
        """判断是否为线上活动"""
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
        """
        if not text:
            return False
        text_lower = text.lower()
        for keyword in config.RESEARCH_METHOD_KEYWORDS:
            if keyword.lower() in text_lower:
                return True
        return False

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

    def is_expired(self, activity: Dict) -> bool:
        """判断活动是否已过期"""
        text = activity.get("description", "") + activity.get("title", "")
        if not text:
            return False

        date_patterns = [
            r"(\d{1,2})[月\-/](\d{1,2})",
            r"(\d{4})[月\-/](\d{1,2})[月\-/](\d{1,2})",
        ]

        now = datetime.now()

        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    if len(match) == 2:
                        month, day = int(match[0]), int(match[1])
                        year = now.year
                        if month < now.month or (month == now.month and day < now.day):
                            year += 1
                        activity_date = datetime(year, month, day)
                    else:
                        year, month, day = int(match[0]), int(match[1]), int(match[2])
                        activity_date = datetime(year, month, day)

                    if activity_date < (now - timedelta(days=3)):
                        return True

                except Exception:
                    continue

        return False

    def is_duplicate(self, activity: Dict) -> bool:
        """判断活动是否为重复推送"""
        title = activity.get("title", "")
        if not title:
            return False

        for old_activity in self.history.get("activities", []):
            old_title = old_activity.get("title", "")
            if self._similarity(title, old_title) > 0.8:
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
        s1_set = set(s1)
        s2_set = set(s2)
        intersection = len(s1_set & s2_set)
        union = len(s1_set | s2_set)
        return intersection / union if union > 0 else 0.0

    def filter_activities(self, activities: List[Dict]) -> List[Dict]:
        """
        筛选符合条件的活动

        筛选逻辑（4条路径，满足任一即通过）：

        路径A — 日本/东亚相关 + 线上：
            含日本词 AND 含活动词 AND 含线上词
            → 线上讲座不限地点，全球均可

        路径B — 日本/东亚相关 + 北京线下：
            含日本词 AND 含活动词 AND 含"北京"
            → 北京线下日本相关活动

        路径C — 研究方法讲座（不要求日本相关）：
            含研究方法词 AND 含活动词 AND (线上 OR 北京)
            → 方法论/学术写作讲座，不限主题

        路径D — 重点账号文章：
            来自信任来源 AND 含日本词 AND 含活动词
            → 东亚视界等重点账号，不限地点
        """
        filtered = []

        for activity in activities:
            text = f"{activity.get('title', '')} {activity.get('description', '')}"

            # 通用检查：过期 / 重复
            if self.is_expired(activity):
                continue
            if self.is_duplicate(activity):
                continue

            # 必须是活动，而非普通文章
            if not self.has_activity_info(text):
                continue

            is_japan    = self.is_japan_related(text)
            is_online   = self.is_online(text)
            is_beijing  = "北京" in text or "beijing" in text.lower()
            is_research = self.is_research_method_related(text)
            is_trusted  = self.is_trusted_source(activity)

            # 路径A：日本相关 + 线上 → 通过
            if is_japan and is_online:
                filtered.append(activity)
                continue

            # 路径B：日本相关 + 北京线下 → 通过
            if is_japan and is_beijing:
                filtered.append(activity)
                continue

            # 路径C：研究方法讲座 + 线上或北京 → 通过（不要求日本相关）
            if is_research and (is_online or is_beijing):
                filtered.append(activity)
                continue

            # 路径D：重点账号 + 日本相关 → 通过（不限地点）
            if is_trusted and is_japan:
                filtered.append(activity)
                continue

        return filtered

    def add_to_history(self, activities: List[Dict]):
        """将活动添加到历史记录"""
        if "activities" not in self.history:
            self.history["activities"] = []

        self.history["activities"].extend(activities)

        # 清理超过30天的历史
        cutoff_date = datetime.now() - timedelta(days=30)
        self.history["activities"] = [
            a for a in self.history["activities"]
            if a.get("fetch_time")
            and datetime.fromisoformat(a["fetch_time"]) > cutoff_date
        ]

        self._save_history()


def test_filter():
    """测试筛选器"""
    test_activities = [
        {
            "title": "【北京】日本文化讲座 - 带你了解日本茶道",
            "description": "时间：2026年4月20日 地点：北京朝阳区 报名链接：...",
            "source": "公众号"
        },
        {
            "title": "日本留学分享会 - 申请日本名校",
            "description": "线上直播 时间：本周六",
            "source": "小红书"
        },
        {
            "title": "质性研究方法论工作坊",
            "description": "腾讯会议 线上 免费报名 2026年4月",
            "source": "网站"
        },
        {
            "title": "学术写作与期刊投稿技巧讲座",
            "description": "北京大学 现场参与 2026年4月",
            "source": "网站"
        },
        {
            "title": "上海日本料理节",
            "description": "上海展览馆",
            "source": "活动行"
        },
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
