"""
公众号文章抓取模块
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
from src import config


class PublicAccountFetcher:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://weixin.sogou.com/"
        })
        self.base_url = "https://weixin.sogou.com/weixin"

    def search_articles(self, keyword: str, max_count: int = 10) -> List[Dict]:
        articles = []
        page = 1

        while len(articles) < max_count and page <= 5:
            try:
                params = {"query": keyword, "type": 2, "page": page}
                response = self.session.get(self.base_url, params=params, timeout=10)
                response.encoding = "utf-8"

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    items = soup.select("div.news-list li")

                    for item in items:
                        try:
                            title_elem = item.select_one("h3 a")
                            if not title_elem:
                                continue
                            title = title_elem.get_text(strip=True)
                            url = title_elem.get("href", "")
                            desc_elem = item.select_one("p.txt-info")
                            description = desc_elem.get_text(strip=True) if desc_elem else ""
                            time_elem = item.select_one("span.s2")
                            pub_date = time_elem.get_text(strip=True) if time_elem else ""
                            articles.append({
                                "title": title,
                                "url": url,
                                "description": description,
                                "publish_date": pub_date,
                                "source": "公众号",
                                "fetch_time": datetime.now().isoformat()
                            })
                            if len(articles) >= max_count:
                                break
                        except Exception:
                            continue

                time.sleep(random.uniform(1, 3))
                page += 1

            except Exception as e:
                print(f"搜索公众号文章出错: {e}")
                break

        return articles[:max_count]

    def fetch_all_japan_articles(self) -> List[Dict]:
        all_articles = []
        keywords = [
            "日本活动 北京",
            "日本文化讲座 北京",
            "日本留学分享",
            "日语角 北京",
            "日本展会 北京"
        ]

        for keyword in keywords:
            print(f"搜索关键词: {keyword}")
            articles = self.search_articles(keyword, max_count=5)
            all_articles.extend(articles)
            time.sleep(random.uniform(2, 4))

        seen = set()
        unique_articles = []
        for article in all_articles:
            if article["title"] not in seen:
                seen.add(article["title"])
                unique_articles.append(article)

        return unique_articles
