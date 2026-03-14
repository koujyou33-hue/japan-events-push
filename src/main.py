"""
日本活动信息自动推送系统 - 主程序
"""
import sys
import os
from datetime import datetime
from typing import List, Dict

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import config
from src.fetcher import PublicAccountFetcher, XiaohongshuFetcher, WebsiteFetcher
from src.filter import ActivityFilter
from src.notify import PushPlusNotifier


def fetch_all_activities() -> List[Dict]:
    all_activities = []

    print("\n📱 开始采集公众号文章...")
    try:
        fetcher = PublicAccountFetcher()
        items = fetcher.fetch_all_japan_articles()
        all_activities.extend(items)
        print(f"   获取到 {len(items)} 篇公众号文章")
    except Exception as e:
        print(f"   公众号采集出错: {e}")

    print("\n📕 开始采集小红书...")
    try:
        fetcher = XiaohongshuFetcher()
        items = fetcher.fetch_all_japan_notes(
            keywords=config.XIAOHONGSHU.get("keywords", [])
        )
        all_activities.extend(items)
        print(f"   获取到 {len(items)} 条小红书笔记")
    except Exception as e:
        print(f"   小红书采集出错: {e}")

    print("\n🌐 开始采集网站活动...")
    try:
        fetcher = WebsiteFetcher()
        items = fetcher.fetch_all_website_events()
        all_activities.extend(items)
        print(f"   获取到 {len(items)} 个网站活动")
    except Exception as e:
        print(f"   网站采集出错: {e}")

    return all_activities


def main():
    print("=" * 60)
    print("  日本活动信息自动推送系统")
    print(f"  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if not config.PUSHPLUS_TOKEN:
        print("\n⚠️  警告: 未配置 PUSHPLUS_TOKEN 环境变量")

    print("\n📥 第一步：采集活动信息...")
    all_activities = fetch_all_activities()
    print(f"\n总计获取到 {len(all_activities)} 条原始活动信息")

    print("\n🔍 第二步：筛选活动...")
    filter_engine = ActivityFilter()
    filtered_activities = filter_engine.filter_activities(all_activities)
    print(f"筛选后剩余 {len(filtered_activities)} 条符合条件的活动")

    print("\n📤 第三步：推送消息...")
    hour = datetime.now().hour
    if hour < 12:
        push_time = "早间"
    elif hour < 18:
        push_time = "下午"
    else:
        push_time = "晚间"

    notifier = PushPlusNotifier()
    if config.PUSHPLUS_TOKEN:
        success = notifier.send_daily_report(filtered_activities, push_time)
        if success:
            filter_engine.add_to_history(filtered_activities)
            print("\n✅ 推送完成！")
        else:
            print("\n❌ 推送失败，请检查日志")
    else:
        print("\n📋 消息预览（未实际推送）:")
        message = notifier.format_activity_message(filtered_activities, push_time)
        print(message["content"])

    print("\n" + "=" * 60)
    print("  执行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
