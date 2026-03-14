"""
小红书内容抓取模块
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import time
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class XiaohongshuFetcher:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.xiaohongshu.com/",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        })

    def _fallback_search(self, keyword: str, max_count: int) -> List[Dict]:
        notes = []
        try:
            baidu_url = "https://www.baidu.com/s"
            params = {"wd": f"site:xiaohongshu.com {keyword} 活动", "pn": 0}
            response = self.session.get(baidu_url, params=params, timeout=10)
            response.encoding = "utf-8"

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                results = soup.select(".result")

                for result in results[:max_count]:
                    try:
                        title_elem = result.select_one("h3 a")
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)
                        url = title_elem.get("href", "")
                        if "xiaohongshu.com" not in url and "xhslink" not in url:
                            continue
                        desc_elem = result.select_one(".c-abstract")
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        notes.append({
                            "title": title,
                            "url": url,
                            "description": description,
                            "source": "小红书",
                            "fetch_time": datetime.now().isoformat()
                        })
                    except Exception:
                        continue
        except Exception as e:
            print(f"备用搜索出错: {e}")
        return notes

    def search_notes(self, keyword: str, max_count: int = 10) -> List[Dict]:
        notes = self._fallback_search(keyword, max_count)
        time.sleep(random.uniform(2, 4))
        return notes[:max_count]

    def fetch_all_japan_notes(self, keywords: List[str] = None) -> List[Dict]:
        if keywords is None:
            keywords = [
                "日本活动 北京",
                "日本文化讲座",
                "日语角活动",
                "日本留学分享会",
                "北京日本展会"
            ]

        all_notes = []
        for keyword in keywords:
            print(f"搜索小红书关键词: {keyword}")
            notes = self.search_notes(keyword, max_count=8)
            all_notes.extend(notes)
            time.sleep(random.uniform(2, 4))

        seen = set()
        unique_notes = []
        for note in all_notes:
            if note["title"] not in seen:
                seen.add(note["title"])
                unique_notes.append(note)

        return unique_notes
