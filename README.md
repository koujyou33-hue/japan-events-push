# 日本活动信息自动推送系统
# Japan Events Auto-Push System

定时抓取日本相关活动信息，推送到微信

## 功能特点

- 多源采集：公众号、小红书、各大网站
- 智能筛选：日本相关、北京/线上活动
- 定时推送：每天8:00和16:00自动推送
- 微信通知：通过PushPlus推送

## 快速开始

### 1. 配置PushPlus

1. 访问 [PushPlus](https://www.pushplus.plus/) 注册账号
2. 获取 TOKEN 并添加到 GitHub Secrets
3. 在 GitHub 仓库设置中添加 secrets：`PUSHPLUS_TOKEN`

### 2. 配置采集源（可选）

编辑 `src/config.py` 修改：
- 公众号列表
- 小红书搜索关键词
- 自定义网站RSS源

### 3. 部署

项目托管在 GitHub Actions，自动每天8:00和16:00执行

## 目录结构

```
.
├── .github/workflows/    # GitHub Actions配置
├── src/
│   ├── fetcher/         # 信息采集模块
│   ├── filter/          # 筛选引擎
│   ├── notify/          # 推送服务
│   ├── config.py        # 配置文件
│   └── main.py          # 主程序
├── data/                # 数据存储
├── requirements.txt     # Python依赖
└── README.md
```

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export PUSHPLUS_TOKEN="your_token_here"

# 运行
python src/main.py
```

## 注意事项

- 请确保采集行为符合目标网站的服务条款
- 建议合理设置请求间隔，避免对目标网站造成压力
- 定期清理 data/activities.json 避免文件过大
