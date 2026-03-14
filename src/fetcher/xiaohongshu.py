"""
小红书内容抓取模块
重点爬取指定博主的笔记，同时广泛搜索日本相关活动内容
由于小红书有反爬机制，采用百度/必应搜索引擎间接获取内容
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import time
import random
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


# ========== 重点关注的小红书博主 ==========
FOCUSED_BLOGGERS = [
    {
        "name": "日々一点勉強",
        "keywords": ["日々一点勉強 日本", "日々一点勉強 活动", "日々一点勉強 讲座"]
    },
    {
        "name": "日本人文学爱好者",
        "keywords": ["日本人文学爱好者 活动", "日本人文学爱好者 讲座", "日本人文学爱好者"]
    },
    {
        "name": "日语渔老师",
        "keywords": ["日语渔老师 日本活动", "日语渔老师 讲座", "日语渔老师"]
    },
    {
        "name": "北京文艺活动资讯",
        "keywords": ["北京文艺活动资讯 日本", "北京文艺活动资讯 讲座", "北京文艺活动资讯 展览", "北京文艺活动资讯"]
    }
]

# 广泛搜索关键词（兜底）
BROAD_KEYWORDS = [
    "日本活动 北京 小红书",
    "日本文化讲座 小红书",
    "日语角活动 小红书",
    "日本留学分享会 小红书",
    "东京活动 中国人 小红书"
]


class XiaohongshuFetcher:
    """小红书内容抓取器（通过搜索引擎间接抓取）"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7",
        })

    def search_blogger_notes(self, blogger_name: str, extra_keywords: List[str],
                              max_count: int = 8) -> List[Dict]:
        notes = []
        seen_titles = set()

        for keyword in extra_keywords:
            if len(notes) >= max_count:
                break

            batch = self._baidu_search_xhs(keyword, max_count=5)
            for note in batch:
                title = note["title"].strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    note["source"] = f"小红书·{blogger_name}"
                    notes.append(note)

            time.sleep(random.uniform(1.5, 3))

        return notes[:max_count]

    def _baidu_search_xhs(self, keyword: str, max_count: int = 10) -> List[Dict]:
        notes = []
        try:
            baidu_url = "https://www.baidu.com/s"
            params = {
                "wd": f"site:xiaohongshu.com {keyword}",
                "rn": 10,
                "pn": 0
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/122.0.0.0 Safari/537.36",
                "Referer": "https://www.baidu.com/"
            }

            resp = requests.get(baidu_url, params=params, headers=headers, timeout=15)
            resp.encoding = "utf-8"

            if resp.status_code != 200:
                return self._bing_search_xhs(keyword, max_count)

            soup = BeautifulSoup(resp.text, "lxml")

            results = (
                soup.select(".result.c-container") or
                soup.select("[class*='result'][tpl]") or
                soup.select(".result")
            )

            for result in results[:max_count]:
                try:
                    title_elem = result.select_one("h3 a") or result.select_one("h3")
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    url = title_elem.get("href", "")

                    if not url:
                        continue

                    desc_elem = (
                        result.select_one(".c-abstract") or
                        result.select_one("span[class*='abstract']") or
                        result.select_one(".content-right") or
                        result.select_one("p")
                    )
                    description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""

                    if title:
                        notes.append({
                            "title": title,
                            "url": url,
                            "description": description,
                            "source": "小红书",
                            "fetch_time": datetime.now().isoformat()
                        })

                except Exception:
                    continue

            if not notes:
                return self._bing_search_xhs(keyword, max_count)

        except Exception as e:
            print(f"  ⚠ 百度搜索出错: {e}")
            return self._bing_search_xhs(keyword, max_count)

        return notes

    def _bing_search_xhs(self, keyword: str, max_count: int = 10) -> List[Dict]:
        notes = []
        try:
            bing_url = "https://www.bing.com/search"
            params = {"q": f"site:xiaohongshu.com {keyword}", "count": 10}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9"
            }

            resp = requests.get(bing_url, params=params, headers=headers, timeout=15)
            resp.encoding = "utf-8"

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "lxml")
                results = soup.select(".b_algo") or soup.select("li.b_algo")

                for result in results[:max_count]:
                    try:
                        title_elem = result.select_one("h2 a") or result.select_one("h2")
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        url = title_elem.get("href", "")

                        desc_elem = result.select_one(".b_caption p") or result.select_one("p")
                        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""

                        if title:
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
            print(f"  ⚠ 必应搜索出错: {e}")

        return notes

    def search_broad_keywords(self, keywords: List[str], max_per_keyword: int = 5) -> List[Dict]:
        notes = []
        seen_titles = set()

        for keyword in keywords:
            print(f"🔍 搜索小红书关键词: {keyword}")
            batch = self._baidu_search_xhs(keyword, max_count=max_per_keyword)

            for note in batch:
                title = note["title"].strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    notes.append(note)

            time.sleep(random.uniform(1.5, 3))

        return notes

    def fetch_all_japan_notes(self, keywords: List[str] = None) -> List[Dict]:
        all_notes = []
        seen_titles = set()

        # 第一步：重点抓取指定博主
        for blogger in FOCUSED_BLOGGERS:
            print(f"👤 抓取重点博主: {blogger['name']}")
            notes = self.search_blogger_notes(
                blogger["name"],
                blogger["keywords"],
                max_count=8
            )
            print(f"   获取到 {len(notes)} 条笔记")

            for note in notes:
                title = note["title"].strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_notes.append(note)

            time.sleep(random.uniform(2, 4))

        # 第二步：广泛关键词补充
        broad_kws = keywords if keywords else BROAD_KEYWORDS
        print("🌐 广泛关键词补充搜索...")
        broad_notes = self.search_broad_keywords(broad_kws, max_per_keyword=5)

        for note in broad_notes:
            title = note["title"].strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                all_notes.append(note)

        print(f"\n✅ 小红书共获取 {len(all_notes)} 条去重笔记")
        return all_notes


def test_fetcher():
    fetcher = XiaohongshuFetcher()
    notes = fetcher.fetch_all_japan_notes()

    print(f"\n获取到 {len(notes)} 条小红书笔记:")
    for i, note in enumerate(notes[:5], 1):
        print(f"{i}. {note['title']}")
        print(f"   来源: {note['source']}")
        print()


if __name__ == "__main__":
    test_fetcher()
