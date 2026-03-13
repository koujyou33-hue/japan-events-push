"""
网站内容抓取模块
用于从各大活动网站、RSS源获取日本相关活动信息
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import feedparser
import time
import random
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class WebsiteFetcher:
    """网站活动信息抓取器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        })

    def fetch_rss(self, rss_url: str, max_count: int = 10) -> List[Dict]:
        """
        获取RSS订阅源内容

        Args:
            rss_url: RSS源地址
            max_count: 最大获取数量

        Returns:
            文章列表
        """
        articles = []

        try:
            response = self.session.get(rss_url, timeout=15)
            response.encoding = "utf-8"

            if response.status_code == 200:
                feed = feedparser.parse(response.text)

                for entry in feed.entries[:max_count]:
                    title = entry.get("title", "")
                    link = entry.get("link", "")
                    description = self._clean_html(entry.get("summary", ""))
                    pub_date = entry.get("published", "")

                    article = {
                        "title": title,
                        "url": link,
                        "description": description,
                        "publish_date": pub_date,
                        "source": feed.feed.get("title", "RSS"),
                        "fetch_time": datetime.now().isoformat()
                    }

                    articles.append(article)

        except Exception as e:
            print(f"获取RSS出错 {rss_url}: {e}")

        return articles

    def fetch_web_page(self, url: str, selector: str = None) -> List[Dict]:
        """
        抓取网页内容

        Args:
            url: 网页地址
            selector: CSS选择器（可选）

        Returns:
            内容列表
        """
        articles = []

        try:
            response = self.session.get(url, timeout=15)
            response.encoding = "utf-8"

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")

                # 尝试查找活动列表
                if selector:
                    items = soup.select(selector)
                else:
                    # 尝试常见的选择器
                    items = (
                        soup.select(".event-item") or
                        soup.select(".activity-item") or
                        soup.select("article") or
                        soup.select(".list-item") or
                        soup.select("li")
                    )

                for item in items[:10]:
                    try:
                        # 尝试提取标题和链接
                        link_elem = item.select_one("a") or item
                        title = ""

                        # 尝试多种方式获取标题
                        title_elem = (
                            item.select_one("h2") or
                            item.select_one("h3") or
                            item.select_one(".title") or
                            item.select_one("a")
                        )

                        if title_elem:
                            title = title_elem.get_text(strip=True)
                        else:
                            title = item.get_text(strip=True)[:100]

                        url = link_elem.get("href", "") if link_elem else ""
                        if url and not url.startswith("http"):
                            from urllib.parse import urlparse
                            parsed = urlparse(url)
                            url = f"{parsed.scheme}://{parsed.netloc}{url}" if parsed.netloc else url

                        # 获取描述
                        desc_elem = item.select_one(".desc") or item.select_one(".description") or item.select_one("p")
                        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""

                        if title and len(title) > 5:
                            article = {
                                "title": title,
                                "url": url,
                                "description": description,
                                "source": urlparse(url).netloc if url else "网站",
                                "fetch_time": datetime.now().isoformat()
                            }
                            articles.append(article)

                    except Exception:
                        continue

        except Exception as e:
            print(f"抓取网页出错 {url}: {e}")

        return articles

    def search_baidu_events(self, keyword: str, max_count: int = 10) -> List[Dict]:
        """
        通过百度搜索获取活动信息

        Args:
            keyword: 搜索关键词
            max_count: 最大获取数量

        Returns:
            活动列表
        """
        articles = []

        try:
            # 搜索活动行
            huodongxing_url = "https://www.huodongxing.com/search"
            params = {"k": keyword}

            response = self.session.get(huodongxing_url, params=params, timeout=15)
            response.encoding = "utf-8"

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")

                # 查找活动卡片
                items = (
                    soup.select(".event-item") or
                    soup.select(".activity-item") or
                    soup.select(".item")
                )

                for item in items[:max_count]:
                    try:
                        title_elem = (
                            item.select_one(".title a") or
                            item.select_one("h3 a") or
                            item.select_one(".name a")
                        )

                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        url = title_elem.get("href", "")

                        if not url.startswith("http"):
                            url = f"https://www.huodongxing.com{url}"

                        # 获取时间
                        time_elem = item.select_one(".time") or item.select_one('[class*="time"]')
                        event_time = time_elem.get_text(strip=True) if time_elem else ""

                        # 获取地点
                        location_elem = item.select_one(".location") or item.select_one('[class*="location"]')
                        location = location_elem.get_text(strip=True) if location_elem else ""

                        description = f"时间: {event_time} | 地点: {location}"

                        article = {
                            "title": title,
                            "url": url,
                            "description": description,
                            "source": "活动行",
                            "fetch_time": datetime.now().isoformat()
                        }

                        articles.append(article)

                    except Exception:
                        continue

            time.sleep(random.uniform(1, 3))

        except Exception as e:
            print(f"搜索活动行出错: {e}")

        return articles[:max_count]

    def fetch_all_website_events(self) -> List[Dict]:
        """
        从各网站获取日本相关活动

        Returns:
            活动列表
        """
        all_events = []

        # 定义搜索任务
        search_tasks = [
            # 活动行搜索
            {"type": "search", "keyword": "日本文化", "max": 8},
            {"type": "search", "keyword": "日语活动", "max": 8},
            {"type": "search", "keyword": "日本留学", "max": 8},
            {"type": "search", "keyword": "北京日本展会", "max": 8},
        ]

        for task in search_tasks:
            if task["type"] == "search":
                print(f"搜索网站: {task['keyword']}")
                events = self.search_baidu_events(task["keyword"], task["max"])
                all_events.extend(events)
                time.sleep(random.uniform(2, 4))

        # 去重
        seen = set()
        unique_events = []
        for event in all_events:
            # 使用标题和URL组合去重
            key = f"{event['title']}_{event['url']}"
            if key not in seen and len(event['title']) > 5:
                seen.add(key)
                unique_events.append(event)

        return unique_events

    @staticmethod
    def _clean_html(html_str: str) -> str:
        """清理HTML标签"""
        if not html_str:
            return ""
        soup = BeautifulSoup(html_str, "lxml")
        return soup.get_text(strip=True)[:200]


def test_fetcher():
    """测试函数"""
    fetcher = WebsiteFetcher()
    events = fetcher.fetch_all_website_events()

    print(f"\n获取到 {len(events)} 个网站活动:")
    for i, event in enumerate(events[:5], 1):
        print(f"{i}. {event['title']}")
        print(f"   来源: {event['source']}")
        print()


if __name__ == "__main__":
    test_fetcher()
