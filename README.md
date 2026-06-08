# 🚀 JobPilot — 求职追踪器

> 海投不迷路，用数据拿下 Offer。

JobPilot 是一个求职全流程管理工具，帮助你追踪每一次投递、面试，并通过数据分析优化求职策略。

**技术栈：** FastAPI · SQLAlchemy · SQLite · Jinja2 · ECharts · SortableJS

## ✨ 功能

- 📋 **Kanban 看板** — 拖拽式管理投递状态（已投递→测评→面试→等结果→Offer→已挂）
- 📅 **面试日程** — 面试安排管理 + 1小时前邮件提醒 + 浏览器通知
- 📝 **面经库** — 记录面试问答 + 复盘反思 + 标签分类搜索
- 📈 **求职洞察（核心亮点）** — 5维数据分析：转化漏斗、渠道效率、时间趋势、公司维度、AI洞察总结
- 📊 **数据统计** — ECharts 可视化图表（饼图、柱状图、漏斗图、折线图）
- 📥 **数据导出** — 一键导出 CSV
- 🔐 **JWT 认证** — 注册/登录 + 邀请码机制
- 📧 **邮件提醒** — 可配置 SMTP，面试前自动发送提醒
- 📱 **响应式** — 手机端也能用

## 🎯 核心亮点 — 数据分析引擎

纯 SQLAlchemy 手写聚合查询（不依赖 pandas），5个分析维度帮你回答：

| 维度 | 你关心的 | JobPilot 告诉你 |
|------|---------|----------------|
| 转化漏斗 | 哪个环节掉最多？ | 投递→测评→面试→Offer 各阶段转化率 |
| 渠道ROI | 哪个渠道最靠谱？ | BOSS直聘、内推、猎聘... 面试率/Offer率对比 |
| 时间趋势 | 什么时候是旺季？ | 按月/周统计投递和面试趋势 |
| 公司分析 | 哪些公司给机会？ | 每家公司的投递次数、面试轮次、最终状态 |
| AI洞察 | 有什么优化建议？ | 自动生成文字总结，指明改进方向 |

## 🚀 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/yourname/jobpilot.git
cd jobpilot

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动
python main.py
# 访问 http://127.0.0.1:8000
```

## 📁 项目结构

```
jobpilot/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置中心
│   ├── database.py          # 数据库引擎
│   ├── auth.py              # JWT 认证依赖
│   ├── models/              # ORM 模型（User, Application, Interview, InterviewNote）
│   ├── routers/             # API 路由（8个模块）
│   │   ├── auth.py          # 认证
│   │   ├── applications.py  # 投递CRUD
│   │   ├── interviews.py    # 面试管理
│   │   ├── notes.py         # 面经库
│   │   ├── analytics.py     # 🆕 数据分析
│   │   ├── settings.py      # 系统设置
│   │   └── pages.py         # 页面路由
│   ├── services/
│   │   ├── email_service.py       # 邮件发送
│   │   ├── interview_reminder.py  # 后台提醒
│   │   └── analytics_engine.py    # 🆕 分析引擎
│   ├── templates/           # Jinja2 模板
│   └── static/              # CSS/JS
├── tests/                   # pytest 测试（21个用例）
├── main.py                  # 启动入口
└── requirements.txt
```

## 🧪 运行测试

```bash
pytest tests/ -v
```

## ⚙️ 环境变量

复制 `.env.example` 为 `.env` 并修改：

```bash
SECRET_KEY=your-secret-key-here
```

## 📄 License

MIT
