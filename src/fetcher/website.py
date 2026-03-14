"""
网站内容抓取模块
采用三路搜索引擎并发：百度、搜狗微信、必应
关键词覆盖中文/英文/日文，不限地点，只要与日本相关的讲座活动就抓
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
import time
import random
import sys
import os
import re
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src import config

CURRENT_YEAR = datetime.now().year
CURRENT_MONTH = datetime.now().month
EXPIRE_CUTOFF = datetime.now() - timedelta(days=7)


def _make_headers(referer: str = "") -> Dict:
    ua_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    ]
    headers = {
        "User-Agent": random.choice(ua_list),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def _is_likely_expired(text: str) -> bool:
    """
    判断文本中的日期是否已过期（超过7天）
    无法解析日期则返回 False（保留该条目）
    """
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
                    # 判断是否可能是明年
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


class WebsiteFetcher:
    """三路搜索引擎并发抓取器"""

    def __init__(self):
        self.session = requests.Session()

    # ----------------------------------------------------------------
    # 路径1：百度搜索（中文关键词）
    # ----------------------------------------------------------------
    def search_baidu(self, keyword: str, max_count: int = 8) -> List[Dict]:
        results = []
        try:
            resp = requests.get(
                "https://www.baidu.com/s",
                params={"wd": keyword, "rn": 10, "pn": 0},
                headers=_make_headers("https://www.baidu.com/"),
                timeout=15
            )
            resp.encoding = "utf-8"
            if resp.status_code != 200:
                return results

            soup = BeautifulSoup(resp.text, "lxml")
            items = (
                soup.select(".result.c-container") or
                soup.select("[class*='result'][tpl]") or
                soup.select(".result")
            )

            for item in items[:max_count]:
                try:
                    title_elem = item.select_one("h3 a") or item.select_one("h3")
                    if not title_elem:
                        continue
                    title = re.sub(r"<[^>]+>", "", title_elem.get_text(strip=True))
                    href = title_elem.get("href", "")

                    desc_elem = (
                        item.select_one(".c-abstract") or
                        item.select_one("span[class*='abstract']") or
                        item.select_one("p")
                    )
                    desc = desc_elem.get_text(strip=True)[:200] if desc_elem else ""

                    if _is_likely_expired(title + " " + desc):
                        continue

                    if title:
                        results.append({
                            "title": title,
                            "url": href,
                            "description": desc,
                            "source": "百度搜索",
                            "fetch_time": datetime.now().isoformat()
                        })
                except Exception:
                    continue

        except Exception as e:
            print(f"  ⚠ 百度搜索出错 [{keyword}]: {e}")

        return results

    # ----------------------------------------------------------------
    # 路径2：搜狗微信搜索（公众号文章）
    # ----------------------------------------------------------------
    def search_sogou_weixin(self, keyword: str, max_count: int = 8) -> List[Dict]:
        results = []
        try:
            resp = requests.get(
                "https://weixin.sogou.com/weixin",
                params={"query": keyword, "type": 2, "page": 1},
                headers=_make_headers("https://weixin.sogou.com/"),
                timeout=15
            )
            resp.encoding = "utf-8"
            if resp.status_code != 200:
                return results

            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.select("div.news-list li") or soup.select(".news-list > li")

            for item in items[:max_count]:
                try:
                    title_elem = (
                        item.select_one("h3 a") or
                        item.select_one(".txt-box h3 a")
                    )
                    if not title_elem:
                        continue
                    title = re.sub(r"<[^>]+>", "", title_elem.get_text(strip=True))
                    href = title_elem.get("href", "")
                    if href and not href.startswith("http"):
                        href = "https://weixin.sogou.com" + href

                    desc_elem = (
                        item.select_one("p.txt-info") or
                        item.select_one(".txt-box p")
                    )
                    desc = desc_elem.get_text(strip=True)[:200] if desc_elem else ""

                    time_elem = (
                        item.select_one("span.s2") or
                        item.select_one(".account-detail span")
                    )
                    pub_time = time_elem.get_text(strip=True) if time_elem else ""

                    if _is_likely_expired(title + " " + desc + " " + pub_time):
                        continue

                    if title:
                        results.append({
                            "title": title,
                            "url": href,
                            "description": desc,
                            "publish_date": pub_time,
                            "source": "搜狗微信",
                            "fetch_time": datetime.now().isoformat()
                        })
                except Exception:
                    continue

        except Exception as e:
            print(f"  ⚠ 搜狗微信出错 [{keyword}]: {e}")

        return results

    # ----------------------------------------------------------------
    # 路径3：必应搜索（英文/日文关键词）
    # ----------------------------------------------------------------
    def search_bing(self, keyword: str, max_count: int = 8) -> List[Dict]:
        results = []
        try:
            resp = requests.get(
                "https://www.bing.com/search",
                params={"q": keyword, "count": 10},
                headers=_make_headers("https://www.bing.com/"),
                timeout=15
            )
            resp.encoding = "utf-8"
            if resp.status_code != 200:
                return results

            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.select(".b_algo") or soup.select("li.b_algo")

            for item in items[:max_count]:
                try:
                    title_elem = item.select_one("h2 a") or item.select_one("h2")
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get("href", "")

                    desc_elem = item.select_one(".b_caption p") or item.select_one("p")
                    desc = desc_elem.get_text(strip=True)[:200] if desc_elem else ""

                    if _is_likely_expired(title + " " + desc):
                        continue

                    try:
                        domain = urlparse(href).netloc
                    except Exception:
                        domain = "网页"

                    if title:
                        results.append({
                            "title": title,
                            "url": href,
                            "description": desc,
                            "source": f"必应·{domain}",
                            "fetch_time": datetime.now().isoformat()
                        })
                except Exception:
                    continue

        except Exception as e:
            print(f"  ⚠ 必应搜索出错 [{keyword}]: {e}")

        return results

    # ----------------------------------------------------------------
    # 路径4：豆瓣同城
    # ----------------------------------------------------------------
    def fetch_douban_events(self, keyword: str = "日本", max_count: int = 10) -> List[Dict]:
        events = []
        try:
            resp = self.session.get(
                "https://www.douban.com/location/beijing/events/rec/",
                params={"tag": keyword},
                headers=_make_headers("https://www.douban.com/"),
                timeout=15
            )
            resp.encoding = "utf-8"

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "lxml")
                items = (
                    soup.select(".events-list li") or
                    soup.select(".event-item") or
                    soup.select("li.tb")
                )
                for item in items[:max_count]:
                    try:
                        title_elem = (
                            item.select_one("h3 a") or
                            item.select_one(".title a") or
                            item.select_one("a")
                        )
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)
                        href = title_elem.get("href", "")

                        time_elem = item.select_one(".when-where") or item.select_one(".time")
                        time_text = time_elem.get_text(strip=True) if time_elem else ""

                        if _is_likely_expired(time_text):
                            continue

                        events.append({
                            "title": title,
                            "url": href,
                            "description": time_text,
                            "source": "豆瓣同城",
                            "fetch_time": datetime.now().isoformat()
                        })
                    except Exception:
                        continue

            # 豆瓣被墙时用必应补充
            if not events:
                results = self.search_bing(
                    f"site:douban.com/event {keyword} 讲座 OR 活动 {CURRENT_YEAR}",
                    max_count=max_count
                )
                for r in results:
                    r["source"] = "豆瓣同城"
                events = results

        except Exception as e:
            print(f"  ⚠ 豆瓣同城出错: {e}")

        return events

    # ----------------------------------------------------------------
    # 主入口：三路并发
    # ----------------------------------------------------------------
    def fetch_all_website_events(self) -> List[Dict]:
        all_events = []
        seen = set()

        def add_events(new_events: List[Dict]):
            for ev in new_events:
                key = ev.get("title", "").strip()
                if key and key not in seen:
                    seen.add(key)
                    all_events.append(ev)

        # 1. 百度（中文关键词）
        print("=" * 40)
        print("🔍 [路径1] 百度搜索（中文）")
        for kw in config.BAIDU_SEARCH_KEYWORDS:
            print(f"  搜索: {kw}")
            evs = self.search_baidu(kw, max_count=6)
            print(f"  → {len(evs)} 条")
            add_events(evs)
            time.sleep(random.uniform(2, 3.5))

        # 2. 搜狗微信（公众号文章）
        print("=" * 40)
        print("💬 [路径2] 搜狗微信（公众号）")
        for kw in config.SOGOU_WEIXIN_KEYWORDS:
            print(f"  搜索: {kw}")
            evs = self.search_sogou_weixin(kw, max_count=6)
            print(f"  → {len(evs)} 条")
            add_events(evs)
            time.sleep(random.uniform(2, 3.5))

        # 3. 必应（英文/日文关键词）
        print("=" * 40)
        print("🌐 [路径3] 必应搜索（英文/日文）")
        for kw in config.BING_SEARCH_KEYWORDS:
            print(f"  搜索: {kw}")
            evs = self.search_bing(kw, max_count=6)
            print(f"  → {len(evs)} 条")
            add_events(evs)
            time.sleep(random.uniform(2, 3.5))

        # 4. 豆瓣同城
        print("=" * 40)
        print("🎭 [路径4] 豆瓣同城")
        for kw in ["日本", "日语", "东亚"]:
            print(f"  搜索: {kw}")
            evs = self.fetch_douban_events(kw, max_count=8)
            print(f"  → {len(evs)} 条")
            add_events(evs)
            time.sleep(random.uniform(2, 3))

        print(f"\n✅ 网站模块共获取 {len(all_events)} 条去重活动")
        return all_events


def test_fetcher():
    fetcher = WebsiteFetcher()
    events = fetcher.fetch_all_website_events()
    print(f"\n最终获取到 {len(events)} 个活动:")
    for i, event in enumerate(events[:10], 1):
        print(f"{i}. [{event['source']}] {event['title']}")
        if event.get("description"):
            print(f"   {event['description'][:80]}")
        print()


if __name__ == "__main__":
    test_fetcher()
