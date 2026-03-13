"""
小红书内容抓取模块
用于从小红书平台获取日本相关活动信息
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import time
import random
import json
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class XiaohongshuFetcher:
    """小红书内容抓取器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.xiaohongshu.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        })
        self.base_url = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"

    def search_notes(self, keyword: str, max_count: int = 10) -> List[Dict]:
        """
        搜索小红书笔记

        Args:
            keyword: 搜索关键词
            max_count: 最大获取数量

        Returns:
            笔记列表
        """
        notes = []
        page = 1

        while len(notes) < max_count and page <= 3:
            try:
                # 构造搜索请求
                payload = {
                    "keyword": keyword,
                    "page": page,
                    "page_size": 20,
                    "search_id": f"search_{int(time.time() * 1000)}",
                    "sort": "general",
                    "note_type": 0
                }

                # 使用备用方案：通过搜索引擎获取小红书内容
                search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&type=51"

                # 先尝试直接访问搜索页面
                response = self.session.get(
                    f"https://www.xiaohongshu.com/explore",
                    params={"keyword": keyword},
                    timeout=10
                )

                if response.status_code == 200:
                    # 解析页面内容
                    soup = BeautifulSoup(response.text, "lxml")

                    # 查找笔记卡片
                    cards = soup.select(".note-item") or soup.select(".search-result-item")

                    if not cards:
                        # 尝试其他选择器
                        cards = soup.select('[class*="note"]')

                    for card in cards:
                        try:
                            title_elem = card.select_one("a.title") or card.select_one(".title")
                            if not title_elem:
                                continue

                            title = title_elem.get_text(strip=True)
                            url = title_elem.get("href", "")

                            if not url.startswith("http"):
                                url = f"https://www.xiaohongshu.com{url}"

                            # 获取描述
                            desc_elem = card.select_one(".desc") or card.select_one('[class*="desc"]')
                            description = desc_elem.get_text(strip=True) if desc_elem else ""

                            # 获取作者
                            author_elem = card.select_one(".author") or card.select_one('[class*="author"]')
                            author = author_elem.get_text(strip=True) if author_elem else ""

                            note = {
                                "title": title,
                                "url": url,
                                "description": description,
                                "author": author,
                                "source": "小红书",
                                "fetch_time": datetime.now().isoformat()
                            }

                            notes.append(note)

                            if len(notes) >= max_count:
                                break

                        except Exception:
                            continue

                # 如果页面访问失败，使用备用搜索方法
                if not notes:
                    notes = self._fallback_search(keyword, max_count)

                time.sleep(random.uniform(2, 4))
                page += 1

            except Exception as e:
                print(f"搜索小红书出错: {e}")
                # 使用备用方法
                notes = self._fallback_search(keyword, max_count)
                break

        return notes[:max_count]

    def _fallback_search(self, keyword: str, max_count: int) -> List[Dict]:
        """
        备用搜索方法 - 通过百度/谷歌搜索小红书相关内容

        Args:
            keyword: 搜索关键词
            max_count: 最大获取数量

        Returns:
            笔记列表
        """
        notes = []

        try:
            # 使用百度搜索小红书相关内容
            baidu_url = "https://www.baidu.com/s"
            params = {
                "wd": f"site:xiaohongshu.com {keyword} 活动",
                "pn": 0
            }

            response = self.session.get(baidu_url, params=params, timeout=10)
            response.encoding = "utf-8"

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                results = soup.select(".result c-container")

                for result in results[:max_count]:
                    try:
                        title_elem = result.select_one("h3 a")
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        url = title_elem.get("href", "")

                        # 跳过非小红书链接
                        if "xiaohongshu.com" not in url:
                            continue

                        desc_elem = result.select_one(".c-abstract") or result.select_one(".content-right_8Zs30")
                        description = desc_elem.get_text(strip=True) if desc_elem else ""

                        note = {
                            "title": title,
                            "url": url,
                            "description": description,
                            "source": "小红书",
                            "fetch_time": datetime.now().isoformat()
                        }

                        notes.append(note)

                    except Exception:
                        continue

        except Exception as e:
            print(f"备用搜索出错: {e}")

        return notes

    def fetch_all_japan_notes(self, keywords: List[str] = None) -> List[Dict]:
        """
        获取所有日本相关小红书笔记

        Args:
            keywords: 自定义关键词列表

        Returns:
            活动笔记列表
        """
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

        # 去重
        seen = set()
        unique_notes = []
        for note in all_notes:
            if note["title"] not in seen:
                seen.add(note["title"])
                unique_notes.append(note)

        return unique_notes


def test_fetcher():
    """测试函数"""
    fetcher = XiaohongshuFetcher()
    notes = fetcher.fetch_all_japan_notes()

    print(f"\n获取到 {len(notes)} 条小红书笔记:")
    for i, note in enumerate(notes[:5], 1):
        print(f"{i}. {note['title']}")
        print(f"   来源: {note['source']}")
        print()


if __name__ == "__main__":
    test_fetcher()
