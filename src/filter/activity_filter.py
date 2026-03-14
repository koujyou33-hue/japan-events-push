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
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"activities": [], "last_update": ""}
        return {"activities": [], "last_update": ""}

    def _save_history(self):
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
        """判断内容是否与研究方法/学术方法论相关"""
        if not text:
            return False
        text_lower = text.lower()
        for keyword in config.RESEARCH_METHOD_KEYWORDS:
            if keyword.lower() in text_lower:
                return True
        return False

    def is_trusted_source(self, activity: Dict) -> bool:
        """判断是否来自重点关注的账号"""
        source = activity.get("source", "")
        for trusted in config.TRUSTED_SOURCES:
            if trusted in source:
                return True
        return False

    def is_expired(self, activity: Dict) -> bool:
        """判断活动是否已过期（超过7天）"""
        text = activity.get("description", "") + activity.get("title", "")
        if not text:
            return False

        now = datetime.now()
        cutoff = now - timedelta(days=7)

        # 匹配 年月日
        for m in re.findall(r"(\d{4})[年\-/.](\d{1,2})[月\-/.](\d{1,2})", text):
            try:
                y, mo, d = int(m[0]), int(m[1]), int(m[2])
                if 2020 <= y <= 2030:
                    if datetime(y, mo, d) < cutoff:
                        return True
            except Exception:
                pass

        # 匹配 月日（无年份）
        for m in re.findall(r"(\d{1,2})[月](\d{1,2})[日号]", text):
            try:
                mo, d = int(m[0]), int(m[1])
                if 1 <= mo <= 12 and 1 <= d <= 31:
                    dt = datetime(now.year, mo, d)
                    if dt < cutoff:
                        try:
                            dt_next = datetime(now.year + 1, mo, d)
                            if dt_next > now:
                                return False
                        except Exception:
                            pass
                        return True
            except Exception:
                pass

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
                        if (datetime.now() - fetch_date).days < config.DEDUP_DAYS:
                            return True
                    except Exception:
                        pass
        return False

    @staticmethod
    def _similarity(s1: str, s2: str) -> float:
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

            # 路径A：日本相关 → 直接通过，完全不限地点
            if is_japan:
                filtered.append(activity)
                continue

            # 路径B：研究方法讲座 + 线上或北京 → 通过
            if is_research and (is_online or is_beijing):
                filtered.append(activity)
                continue

            # 路径C：重点账号 → 直接通过
            if is_trusted:
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
    test_activities = [
        {
            "title": "日本文学讲座：村上春树与当代日本",
            "description": "线上直播 2026年4月20日 免费报名",
            "source": "搜狗微信"
        },
        {
            "title": "Japan History Seminar: Meiji Restoration",
            "description": "Online event, April 2026, free registration",
            "source": "必应·eventbrite.com"
        },
        {
            "title": "质性研究方法论工作坊",
            "description": "腾讯会议 线上 免费报名 2026年4月",
            "source": "百度搜索"
        },
        {
            "title": "日本料理节",
            "description": "上海展览馆 已结束 2026年1月",
            "source": "活动行"
        },
    ]

    filter_engine = ActivityFilter()
    filtered = filter_engine.filter_activities(test_activities)

    print(f"原始: {len(test_activities)} 条  筛选后: {len(filtered)} 条\n")
    for a in filtered:
        print(f"✓ [{a['source']}] {a['title']}")


if __name__ == "__main__":
    test_filter()
