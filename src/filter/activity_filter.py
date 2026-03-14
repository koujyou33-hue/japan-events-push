"""
活动筛选引擎模块
"""
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src import config


class ActivityFilter:

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
        if not text:
            return False
        text_lower = text.lower()
        for keyword in config.JAPAN_KEYWORDS:
            if keyword.lower() in text_lower:
                return True
        return False

    def has_activity_info(self, text: str) -> bool:
        if not text:
            return False
        text_lower = text.lower()
        for keyword in config.ACTIVITY_KEYWORDS + config.REGISTRATION_KEYWORDS:
            if keyword.lower() in text_lower:
                return True
        return False

    def is_beijing_or_online(self, text: str) -> bool:
        if not config.ONLY_BEIJING_ONLINE:
            return True
        if not text:
            return False
        text_lower = text.lower()
        for city in config.OFFLINE_CITIES:
            if city.lower() in text_lower:
                return True
        for keyword in config.ONLINE_KEYWORDS:
            if keyword.lower() in text_lower:
                return True
        return False

    def is_duplicate(self, activity: Dict) -> bool:
        title = activity.get("title", "")
        if not title:
            return False
        for old in self.history.get("activities", []):
            old_title = old.get("title", "")
            if self._similarity(title, old_title) > 0.8:
                fetch_time = old.get("fetch_time", "")
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
        filtered = []
        for activity in activities:
            text = f"{activity.get('title', '')} {activity.get('description', '')}"
            if not self.is_japan_related(text):
                continue
            if not self.has_activity_info(text):
                continue
            if not self.is_beijing_or_online(text):
                continue
            if self.is_duplicate(activity):
                continue
            filtered.append(activity)
        return filtered

    def add_to_history(self, activities: List[Dict]):
        if "activities" not in self.history:
            self.history["activities"] = []
        self.history["activities"].extend(activities)
        cutoff = datetime.now() - timedelta(days=30)
        self.history["activities"] = [
            a for a in self.history["activities"]
            if a.get("fetch_time") and datetime.fromisoformat(a["fetch_time"]) > cutoff
        ]
        self._save_history()
