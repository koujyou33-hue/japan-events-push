"""
公众号文章抓取模块
重点爬取「东亚视界」「谓无名」「北大文科」公众号在 wxredian.com 上的镜像文章
同时通过搜狗搜索补充其他日本相关公众号文章
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import time
import random
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src import config


# ========== 重点关注的公众号配置 ==========
# wxredian.com 上的公众号 author ID
FOCUSED_ACCOUNTS = [
    {
        "name": "东亚视界",
        "wxredian_id": "gh_0a8b3c4d5e6f",
        "search_name": "东亚视界",
        "keywords": ["学术活动", "活动预告", "研究资讯", "讲座", "会议"]
    },
    {
        "name": "谓无名",
        "wxredian_id": "gh_23be5cc3234b",
        "search_name": "谓无名",
        "keywords": ["活动", "讲座", "直播", "预告", "分享会"]
    },
    {
        "name": "北大文科",
        "wxredian_id": "",
        "search_name": "北大文科",
        "keywords": ["活动预告", "讲座", "学术活动", "研讨会", "日本"]
    }
]

# 广泛搜索关键词（兜底）
BROAD_KEYWORDS = [
    "日本活动 北京",
    "日本文化讲座",
    "日本留学分享",
    "日语角 北京",
    "东亚研究 活动预告"
]


class PublicAccountFetcher:
    """微信公众号文章抓取器（基于 wxredian.com 镜像站）"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7",
            "Referer": "https://wxredian.com/"
        })

    def fetch_wxredian_by_account(self, account_name: str, max_count: int = 10) -> List[Dict]:
        articles = []
        try:
            search_url = "https://wxredian.com/search"
            params = {"keyword": account_name, "type": "author"}

            resp = self.session.get(search_url, params=params, timeout=15)
            resp.encoding = "utf-8"

            if resp.status_code != 200:
                print(f"  ⚠ wxredian搜索失败(状态码{resp.status_code})，尝试备用方案")
                return self._fetch_wxredian_via_baidu(account_name, max_count)

            soup = BeautifulSoup(resp.text, "lxml")

            author_links = soup.select("a[href*='/author']")
            author_url = None
            for link in author_links:
                if account_name in link.get_text():
                    author_url = "https://wxredian.com" + link.get("href", "")
                    break

            if not author_url:
                print(f"  ⚠ 未找到{account_name}的主页，尝试备用方案")
                return self._fetch_wxredian_via_baidu(account_name, max_count)

            articles = self._fetch_author_articles(author_url, account_name, max_count)

        except Exception as e:
            print(f"  ⚠ wxredian抓取出错: {e}，尝试备用方案")
            articles = self._fetch_wxredian_via_baidu(account_name, max_count)

        return articles

    def _fetch_author_articles(self, author_url: str, account_name: str, max_count: int) -> List[Dict]:
        articles = []
        try:
            resp = self.session.get(author_url, timeout=15)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")

            items = (
                soup.select(".article-item") or
                soup.select(".news-item") or
                soup.select("article") or
                soup.select(".art-item") or
                soup.select("li.item")
            )

            for item in items[:max_count]:
                try:
                    title_elem = (
                        item.select_one("h2 a") or
                        item.select_one("h3 a") or
                        item.select_one(".title a") or
                        item.select_one("a.title") or
                        item.select_one("a")
                    )
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    href = title_elem.get("href", "")
                    if not href.startswith("http"):
                        href = "https://wxredian.com" + href

                    desc_elem = item.select_one(".desc") or item.select_one(".summary") or item.select_one("p")
                    description = desc_elem.get_text(strip=True)[:150] if desc_elem else ""

                    date_elem = item.select_one(".date") or item.select_one("time") or item.select_one(".time")
                    pub_date = date_elem.get_text(strip=True) if date_elem else ""

                    articles.append({
                        "title": title,
                        "url": href,
                        "description": description,
                        "publish_date": pub_date,
                        "source": f"公众号·{account_name}",
                        "fetch_time": datetime.now().isoformat()
                    })

                except Exception:
                    continue

        except Exception as e:
            print(f"  ⚠ 抓取主页文章出错: {e}")

        return articles

    def _fetch_wxredian_via_baidu(self, account_name: str, max_count: int) -> List[Dict]:
        articles = []
        try:
            baidu_url = "https://www.baidu.com/s"
            params = {
                "wd": f'site:wxredian.com "{account_name}" 活动 OR 讲座 OR 预告',
                "rn": 10
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/122.0.0.0 Safari/537.36",
                "Referer": "https://www.baidu.com/"
            }

            resp = requests.get(baidu_url, params=params, headers=headers, timeout=15)
            resp.encoding = "utf-8"

            if resp.status_code == 200:
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
                        url = title_elem.get("href", "")

                        if "wxredian.com" not in url and "weixin" not in url:
                            continue

                        desc_elem = (
                            result.select_one(".c-abstract") or
                            result.select_one(".content-right") or
                            result.select_one("span[class*='abstract']")
                        )
                        description = desc_elem.get_text(strip=True)[:150] if desc_elem else ""

                        articles.append({
                            "title": title,
                            "url": url,
                            "description": description,
                            "publish_date": "",
                            "source": f"公众号·{account_name}",
                            "fetch_time": datetime.now().isoformat()
                        })

                    except Exception:
                        continue

        except Exception as e:
            print(f"  ⚠ 百度备用搜索出错: {e}")

        return articles

    def search_sogou(self, keyword: str, max_count: int = 5) -> List[Dict]:
        articles = []
        try:
            url = "https://weixin.sogou.com/weixin"
            params = {"query": keyword, "type": 2, "page": 1}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/122.0.0.0 Safari/537.36",
                "Referer": "https://weixin.sogou.com/"
            }

            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.encoding = "utf-8"

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "lxml")
                items = soup.select("div.news-list li")

                for item in items[:max_count]:
                    try:
                        title_elem = item.select_one("h3 a")
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        href = title_elem.get("href", "")

                        desc_elem = item.select_one("p.txt-info")
                        description = desc_elem.get_text(strip=True)[:150] if desc_elem else ""

                        time_elem = item.select_one("span.s2")
                        pub_date = time_elem.get_text(strip=True) if time_elem else ""

                        articles.append({
                            "title": title,
                            "url": href,
                            "description": description,
                            "publish_date": pub_date,
                            "source": "公众号",
                            "fetch_time": datetime.now().isoformat()
                        })

                    except Exception:
                        continue

        except Exception as e:
            print(f"  ⚠ 搜狗搜索出错: {e}")

        return articles

    def fetch_all_japan_articles(self) -> List[Dict]:
        all_articles = []

        # 第一步：重点抓取指定公众号
        for account in FOCUSED_ACCOUNTS:
            print(f"📰 抓取重点公众号: {account['name']}")
            articles = self.fetch_wxredian_by_account(account["name"], max_count=8)
            print(f"   获取到 {len(articles)} 篇文章")
            all_articles.extend(articles)
            time.sleep(random.uniform(2, 4))

        # 第二步：广泛关键词搜索（通过搜狗补充）
        for keyword in BROAD_KEYWORDS:
            print(f"🔍 搜狗搜索: {keyword}")
            articles = self.search_sogou(keyword, max_count=5)
            print(f"   获取到 {len(articles)} 篇文章")
            all_articles.extend(articles)
            time.sleep(random.uniform(2, 4))

        # 去重
        seen = set()
        unique_articles = []
        for article in all_articles:
            key = article["title"].strip()
            if key and key not in seen:
                seen.add(key)
                unique_articles.append(article)

        print(f"\n✅ 公众号共获取 {len(unique_articles)} 篇去重文章")
        return unique_articles


def test_fetcher():
    fetcher = PublicAccountFetcher()
    articles = fetcher.fetch_all_japan_articles()

    print(f"\n获取到 {len(articles)} 篇文章:")
    for i, article in enumerate(articles[:5], 1):
        print(f"{i}. {article['title']}")
        print(f"   来源: {article['source']}")
        print()


if __name__ == "__main__":
    test_fetcher()
