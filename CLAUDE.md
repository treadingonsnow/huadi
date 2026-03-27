# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

上海美食大数据分析平台 — 一个全栈数据分析平台，采集、分析并可视化上海餐厅数据（来源：大众点评爬虫 + 公开数据集）。

## 实际开发范围

**三个页面**：登录页、数据可视化大屏、餐厅搜索页

**已实现功能**：JWT 认证、数据大屏（7 个图表）、餐厅搜索/详情、数据导入（CSV/Excel）、数据清洗日志、报告导出、ML 预测接口

**去掉的功能**：Celery 异步任务、Redis 缓存（配置保留但未使用）、推荐系统、竞争分析、小红书/政府数据爬虫

**数据策略**：大众点评自定义爬虫（`spider/`），失败则切换公开数据集导入，目标 1000-5000 条

## Architecture

```
frontend/ (React 19 + Vite + Ant Design 5 + ECharts 5)
    ↓ REST API (/api/v1)  [Vite proxy: /api → localhost:8000]
backend/ (FastAPI + SQLAlchemy 2.0 + PyMySQL)
    └→ MySQL 8.0 (structured data)

spider/ (自定义爬虫，非 Scrapy) → MySQL  [爬大众点评]
```

- **backend/** — FastAPI app. Entry: `backend/app/main.py`. Routes in `api/v1/`, ORM models in `models/`, business logic in `services/`. 同步架构，无 Celery/Redis。
- **spider/** — 自定义爬虫（非 Scrapy），针对大众点评。支持加密请求处理和字体反爬。数据落地支持 MySQL/CSV/MongoDB。Entry: `spider/main.py`，控制器: `spider/utils/spider_controller.py`。
- **frontend/** — React SPA，`.jsx` 文件。Vite dev server 代理 `/api` 到后端 8000 端口。状态管理用 Zustand，图表用 echarts-for-react，地图用 ECharts + `public/shanghai.geojson`（无需高德 key）。UI 组件用 Ant Design 暗色主题。
- **config/dictionaries/** — 业务字典（菜系、区域、情感词、场景），供爬虫管道和分析模块使用。

## Commands

### Frontend (from `frontend/`)
```bash
npm install
npm run dev          # Vite dev server on port 3000
npm run build        # Production build to dist/
npm run lint         # ESLint
```

### Backend (from `backend/`)
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Spider (from `spider/`)
```bash
pip install -r requirements.txt
python main.py       # 大众点评爬虫
```

### Docker (full stack)
```bash
docker compose up -d --build
# or
bash scripts/deploy.sh
```

### Database
```bash
mysql -u root -p < scripts/init_db.sql
```

## Key Design Decisions

- **Single API version prefix**: All endpoints under `/api/v1/`. Unified response format: `{"code": 200, "message": "success", "data": {...}}`.
- **爬虫目标**：大众点评（非美团）。自定义爬虫处理加密请求和字体反爬，非 Scrapy 框架。
- **Crawl rate limit**: 请求间隔可配置，随机 User-Agent。配置在 `spider/config.ini` 和 `spider/utils/spider_config.py`。
- **Data desensitization**: 手机号存储前打码（`138****1234`）。
- **Auth**: JWT tokens（24h 过期），BCrypt 密码哈希，支持登录和注册。实现在 `backend/app/core/security.py`。
- **No Celery/Redis**: 所有操作同步执行，分析结果按需计算。Redis 配置保留但未实际使用。
- **Map**: ECharts + `frontend/public/shanghai.geojson`（DataV 格式，无需高德 API key）。
- **Mock 开关**: 前端各接口文件顶部有 `USE_MOCK` 开关，后端未就绪时可用 mock 数据开发。

## Configuration

`.env` 已存在，无需从 `.env.example` 复制。Key env vars: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `APP_SECRET_KEY`.

## Database Tables

| 表 | 用途 |
|---|---|
| `restaurant_info` | 餐厅主数据（名称、地址、评分、均价、菜系、区域、经纬度） |
| `restaurant_review` | 评论（内容、情感分、各维度评分） |
| `sys_user` | 用户账号（admin/user 两种角色，默认 admin/admin123） |
| `user_favorites` | 用户收藏（多对多） |
| `clean_log` | 数据清洗日志 |
| `crawl_task` | 爬虫任务记录 |

## Language

项目文档和注释用中文（简体）。代码标识符和 API 路径用英文。在对话中应使用中文。

## Reference Docs

- `docs/开发指南.md` — 环境配置、前后端启动、Git 工作流、常见问题
- `docs/分工安排.md` — 五人分工详细任务清单和时间线
- `docs/前端开发指导文档.md` — 前端规范、组件结构、ECharts 用法、Ant Design 主题
