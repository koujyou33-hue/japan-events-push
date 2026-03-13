"""
Server酱推送服务模块
用于将活动信息推送到微信
"""
import requests
from datetime import datetime
from typing import List, Dict, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src import config


class ServerChanNotifier:
    """Server酱微信推送器"""

    def __init__(self, sckey: str = None):
        """
        初始化推送器

        Args:
            sckey: Server酱的SCKEY，从环境变量或参数获取
        """
        self.sckey = sckey or config.SERVERCHAN_KEY
        self.api_url = f"https://sc.ftqq.com/{self.sckey}.send"

    def send(self, title: str, content: str, desp: str = "") -> bool:
        """
        发送推送消息

        Args:
            title: 消息标题
            content: 消息内容摘要
            desp: 详细信息（可选）

        Returns:
            是否发送成功
        """
        if not self.sckey:
            print("错误: 未配置Server酱SCKEY")
            return False

        try:
            data = {
                "text": title,
                "desp": desp or content
            }

            response = requests.post(self.api_url, data=data, timeout=10)

            if response.status_code == 200:
                result = response.json()

                if result.get("errno") == 0 or result.get("code") == 0:
                    print(f"✓ 推送成功: {title}")
                    return True
                else:
                    print(f"✗ 推送失败: {result.get('message', '未知错误')}")
                    return False
            else:
                print(f"✗ HTTP错误: {response.status_code}")
                return False

        except requests.RequestException as e:
            print(f"✗ 请求出错: {e}")
            return False
        except Exception as e:
            print(f"✗ 未知错误: {e}")
            return False

    def format_activity_message(self, activities: List[Dict], push_time: str = "早间") -> Dict:
        """
        格式化活动消息

        Args:
            activities: 活动列表
            push_time: 推送时段（早间/午间/晚间）

        Returns:
            包含标题和内容的字典
        """
        now = datetime.now()
        date_str = now.strftime("%Y年%m月%d日")

        # 构建标题
        title = f"【日本活动精选】{push_time}简报 {date_str}"

        # 构建内容
        content_lines = []

        # 添加统计信息
        content_lines.append(f"📊 今日精选 **{len(activities)}** 个活动\n")
        content_lines.append("---")

        # 添加每个活动
        for i, activity in enumerate(activities[:config.MAX_PUSH_COUNT], 1):
            title_text = activity.get("title", "无标题")
            url = activity.get("url", "")
            description = activity.get("description", "")[:100]
            source = activity.get("source", "未知来源")

            content_lines.append(f"\n**{i}. {title_text}**")
            content_lines.append(f"📝 来源：{source}")

            if description:
                content_lines.append(f"📋 {description}")

            if url:
                content_lines.append(f"🔗 [查看详情]({url})")

            content_lines.append("\n---")

        # 添加底部信息
        content_lines.append("\n")
        content_lines.append("💡 提示：点击链接查看完整信息并报名")
        content_lines.append(f"⏰ 更新时间：{now.strftime('%H:%M')}")
        content_lines.append("\n")
        content_lines.append("> 由日本活动推送机器人自动生成")

        content = "\n".join(content_lines)

        return {
            "title": title,
            "content": content,
            "desp": content
        }

    def send_daily_report(self, activities: List[Dict], push_time: str = "早间") -> bool:
        """
        发送每日活动报告

        Args:
            activities: 活动列表
            push_time: 推送时段

        Returns:
            是否发送成功
        """
        if not activities:
            # 没有活动时发送空报告
            now = datetime.now()
            date_str = now.strftime("%Y年%m月%d日")
            title = f"【日本活动精选】{push_time}简报 {date_str}"
            content = f"📊 {push_time}简报 {date_str}\n\n暂无新的日本相关活动推荐\n\n⏰ 更新时间：{now.strftime('%H:%M')}"

            return self.send(title, content)

        message = self.format_activity_message(activities, push_time)
        return self.send(message["title"], message["content"], message["desp"])

    def test_connection(self) -> bool:
        """
        测试Server酱连接

        Returns:
            是否连接成功
        """
        return self.send("🧪 测试消息", "这是一条测试消息，日本活动推送系统已正常运行")


def test_notifier():
    """测试推送功能"""
    notifier = ServerChanNotifier()

    # 测试消息
    test_activities = [
        {
            "title": "【北京】日本文化讲座 - 茶道体验",
            "url": "https://example.com/1",
            "description": "时间：2026年3月20日 地点：北京朝阳区 报名链接：...",
            "source": "公众号"
        },
        {
            "title": "日本留学分享会 - 申请日本名校",
            "url": "https://example.com/2",
            "description": "线上直播 时间：本周六",
            "source": "小红书"
        }
    ]

    print("发送测试消息...")
    result = notifier.send_daily_report(test_activities, "测试")
    print(f"发送结果: {'成功' if result else '失败'}")


if __name__ == "__main__":
    test_notifier()
