"""
网站内容抓取模块
采用三路搜索引擎并发：百度、搜狗微信、必应/Google
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

# 当前年份，用于过滤明显过期内容
CURRENT_YEAR = datetime.now().year
CURRENT_MONTH = datetime.now().month

# 过期日期判断：抓到的内容如果日期明确早于"今天-7天"，就丢弃
EXPIRE_CUTOFF = datetime.now() - timedelta(days=7)


def _make_headers(referer: str = "") -> Dict:
    """生成随机 UA 请求头"""
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
    判断文章/标题里的日期是否已过期
    策略：提取所有可识别的日期，取最晚的一个来判断
    - 最晚日期超过7天前 → 过期
    - 无法解析任何日期 → 保留（不丢弃）
    """
    if not text:
        return False

    now = datetime.now()
    cutoff = now - timedelta(days=7)
    candidates = []

    # 模式1：年月日
    for m in re.findall(r"(\d{4})[年\-/.](\d{1,2})[月\-/.](\d{1,2})", text):
        try:
            y, mo, d = int(m[0]), int(m[1]), int(m[2])
            if 2020 <= y <= 2035 and 1 <= mo <= 12 and 1 <= d <= 31:
                candidates.append(datetime(y, mo, d))
        except Exception:
            pass

    # 模式2：月日（无年份）
    for m in re.findall(r"(\d{1,2})[月](\d{1,2})[日号]", text):
        try:
            mo, d = int(m[0]), int(m[1])
            if 1 <= mo <= 12 and 1 <= d <= 31:
                dt_this = datetime(now.year, mo, d)
                if dt_this < cutoff:
                    # 今年已过期，试试是否是明年的
                    dt_next = datetime(now.year + 1, mo, d)
                    candidates.append(dt_next)
                else:
                    candidates.append(dt_this)
        except Exception:
            pass

    if not candidates:
        return False  # 无日期信息，保留

    # 取最晚日期来判断
    latest = max(candidates)
    return latest < cutoff


class WebsiteFetcher:
    """三路搜索引擎并发抓取器"""

    def __init__(self):
        self.session = requests.Session()

    # ----------------------------------------------------------------
    # 路径1：百度搜索（中文关键词为主）
    # ----------------------------------------------------------------
    def search_baidu(self, keyword: str, max_count: int = 8) -> List[Dict]:
        """百度搜索（限定近3个月结果）"""
        results = []
        try:
            url = "https://www.baidu.com/s"
            params = {
                "wd": keyword,
                "rn": 10,
                "pn": 0,
                "tbs": "qdr:m3",   # 只返回最近3个月内的结果
            }
            resp = requests.get(
                url, params=params,
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

                    # 时效性过滤
                    combined = title + " " + desc
                    if _is_likely_expired(combined):
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
    # 路径2：搜狗微信搜索（公众号文章，中文）
    # ----------------------------------------------------------------
    def search_sogou_weixin(self, keyword: str, max_count: int = 8) -> List[Dict]:
        """搜狗微信搜索（限定近3个月文章）"""
        results = []
        try:
            url = "https://weixin.sogou.com/weixin"
            params = {
                "query": keyword,
                "type": 2,
                "page": 1,
                "tsn": 3,   # 时间过滤：3=近3个月
            }
            resp = requests.get(
                url, params=params,
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
                    title_elem = item.select_one("h3 a") or item.select_one(".txt-box h3 a")
                    if not title_elem:
                        continue
                    title = re.sub(r"<[^>]+>", "", title_elem.get_text(strip=True))
                    href = title_elem.get("href", "")
                    if href and not href.startswith("http"):
                        href = "https://weixin.sogou.com" + href

                    desc_elem = item.select_one("p.txt-info") or item.select_one(".txt-box p")
                    desc = desc_elem.get_text(strip=True)[:200] if desc_elem else ""

                    # 发布时间
                    time_elem = item.select_one("span.s2") or item.select_one(".account-detail span")
                    pub_time = time_elem.get_text(strip=True) if time_elem else ""

                    combined = title + " " + desc + " " + pub_time
                    if _is_likely_expired(combined):
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
    # 路径3：必应搜索（英文/日文关键词为主）
    # ----------------------------------------------------------------
    def search_bing(self, keyword: str, max_count: int = 8) -> List[Dict]:
        """必应搜索（限定近3个月结果）"""
        results = []
        try:
            url = "https://www.bing.com/search"
            params = {
                "q": keyword,
                "count": 10,
                "filters": "ex1%3a%22ez3%22",  # 近3个月时间过滤
            }
            resp = requests.get(
                url, params=params,
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

                    # 时效性过滤
                    combined = title + " " + desc
                    if _is_likely_expired(combined):
                        continue

                    # 提取域名
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
    # 路径4：豆瓣同城（活动质量高，直接抓）
    # ----------------------------------------------------------------
    def fetch_douban_events(self, keyword: str = "日本", max_count: int = 10) -> List[Dict]:
        """豆瓣同城搜索，失败时用搜索引擎补充"""
        events = []
        try:
            url = "https://www.douban.com/location/beijing/events/rec/"
            params = {"tag": keyword}
            resp = self.session.get(
                url, params=params,
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

            if not events:
                # 豆瓣被墙或反爬时，用必应补充
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
    # 主入口：三路并发，按关键词组分批搜索
    # ----------------------------------------------------------------
    def fetch_all_website_events(self) -> List[Dict]:
        """
        三路搜索引擎并发抓取，聚合去重后返回
        
        路径分配：
        - 百度：中文关键词（BAIDU_SEARCH_KEYWORDS）
        - 搜狗微信：微信公众号文章（SOGOU_WEIXIN_KEYWORDS）
        - 必应：英文/日文关键词（BING_SEARCH_KEYWORDS）
        - 豆瓣同城：直接抓取活动（日本/日语/东亚）
        """
        all_events = []
        seen = set()

        def add_events(new_events: List[Dict]):
            for ev in new_events:
                key = ev.get("title", "").strip()
                if key and key not in seen:
                    seen.add(key)
                    all_events.append(ev)

        # ---- 1. 百度搜索（中文关键词） ----
        print("=" * 40)
        print("🔍 [路径1] 百度搜索（中文关键词）")
        for kw in config.BAIDU_SEARCH_KEYWORDS:
            print(f"  搜索: {kw}")
            evs = self.search_baidu(kw, max_count=6)
            print(f"  → 获取 {len(evs)} 条")
            add_events(evs)
            time.sleep(random.uniform(2, 3.5))

        # ---- 2. 搜狗微信搜索 ----
        print("=" * 40)
        print("💬 [路径2] 搜狗微信搜索（公众号文章）")
        for kw in config.SOGOU_WEIXIN_KEYWORDS:
            print(f"  搜索: {kw}")
            evs = self.search_sogou_weixin(kw, max_count=6)
            print(f"  → 获取 {len(evs)} 条")
            add_events(evs)
            time.sleep(random.uniform(2, 3.5))

        # ---- 3. 必应搜索（英文/日文关键词） ----
        print("=" * 40)
        print("🌐 [路径3] 必应搜索（英文/日文关键词）")
        for kw in config.BING_SEARCH_KEYWORDS:
            print(f"  搜索: {kw}")
            evs = self.search_bing(kw, max_count=6)
            print(f"  → 获取 {len(evs)} 条")
            add_events(evs)
            time.sleep(random.uniform(2, 3.5))

        # ---- 4. 豆瓣同城 ----
        print("=" * 40)
        print("🎭 [路径4] 豆瓣同城")
        for kw in ["日本", "日语", "东亚"]:
            print(f"  搜索: {kw}")
            evs = self.fetch_douban_events(kw, max_count=8)
            print(f"  → 获取 {len(evs)} 条")
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
