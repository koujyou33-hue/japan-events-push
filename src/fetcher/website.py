"""
网站内容抓取模块
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import time
import random
import sys
import os
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class WebsiteFetcher:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        })

    def search_huodongxing(self, keyword: str, max_count: int = 10) -> List[Dict]:
        articles = []
        try:
            url = "https://www.huodongxing.com/search"
            params = {"k": keyword}
            response = self.session.get(url, params=params, timeout=15)
            response.encoding = "utf-8"

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                items = soup.select(".event-item") or soup.select(".item")

                for item in items[:max_count]:
                    try:
                        title_elem = item.select_one(".title a") or item.select_one("h3 a")
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get("href", "")
                        if not link.startswith("http"):
                            link = f"https://www.huodongxing.com{link}"
                        time_elem = item.select_one(".time")
                        location_elem = item.select_one(".location")
                        event_time = time_elem.get_text(strip=True) if time_elem else ""
                        location = location_elem.get_text(strip=True) if location_elem else ""
                        articles.append({
                            "title": title,
                            "url": link,
                            "description": f"时间: {event_time} | 地点: {location}",
                            "source": "活动行",
                            "fetch_time": datetime.now().isoformat()
                        })
                    except Exception:
                        continue
            time.sleep(random.uniform(1, 3))
        except Exception as e:
            print(f"搜索活动行出错: {e}")
        return articles[:max_count]

    def fetch_all_website_events(self) -> List[Dict]:
        all_events = []
        keywords = ["日本文化 北京", "日语活动 北京", "日本留学分享", "北京日本展会"]

        for keyword in keywords:
            print(f"搜索网站: {keyword}")
            events = self.search_huodongxing(keyword, 8)
            all_events.extend(events)
            time.sleep(random.uniform(2, 4))

        seen = set()
        unique_events = []
        for event in all_events:
            key = f"{event['title']}_{event['url']}"
            if key not in seen and len(event["title"]) > 5:
                seen.add(key)
                unique_events.append(event)

        return unique_events
