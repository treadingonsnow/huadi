# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

上海美食大数据分析平台 — a full-stack platform for collecting, analyzing, and visualizing Shanghai restaurant data from multiple sources (Dianping, Meituan, Xiaohongshu, government portals).

## 实际开发范围（已裁剪，以 SPEC.md 为准）

**三个页面**：登录页、数据可视化大屏、餐厅搜索页（可选）

**去掉的功能**：Celery 异步任务、Redis 缓存、报告生成、推荐系统、竞争分析、小红书/政府数据爬虫

**数据策略**：优先爬取美团，失败则切换公开数据集，目标 1000-5000 条

## Architecture

```
frontend/ (React 19 + Vite + Ant Design + ECharts)
    ↓ REST API (/api/v1)
backend/ (FastAPI + SQLAlchemy)
    └→ MySQL 8.0 (structured data)

crawler/ (Scrapy + Selenium) → MySQL  [只爬美团]
```

- **backend/** — FastAPI app. Entry: `backend/app/main.py`. Routes in `api/v1/`, ORM models in `models/`, business logic in `services/`. No Celery/Redis in current scope.
- **crawler/** — Scrapy project (`crawler/shanghai_food/`). Only `meituan_spider` is in scope. Data flows through `pipelines.py` (clean → validate → insert MySQL).
- **frontend/** — React SPA using `.jsx` files. Vite dev server proxies `/api` to backend port 8000. State via Zustand, charts via echarts-for-react, maps via ECharts built-in (no AMap key needed). UI components from Ant Design.
- **config/dictionaries/** — Business domain dictionaries (cuisine types, districts, sentiment keywords) used by both crawler pipelines and analysis modules.

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

### Crawler (from `crawler/`)
```bash
pip install -r requirements.txt
scrapy crawl meituan_spider   # 只爬美团
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
- **Crawl rate limit**: 2-3 seconds between requests, random User-Agent. Configured in `crawler/shanghai_food/settings.py`.
- **Data desensitization**: Phone numbers masked before storage. Handled in `crawler/shanghai_food/pipelines.py`.
- **Auth**: JWT tokens (24h expiry), BCrypt password hashing, simple login only (no registration). Implementation in `backend/app/core/security.py`.
- **No Celery/Redis**: All operations are synchronous. Analysis results computed on-demand.
- **Map**: ECharts built-in Shanghai map (no AMap API key required). Download `shanghai.json` from DataV and place in `frontend/public/`.

## Configuration

Copy `.env.example` → `.env` before running. Key env vars: MySQL connection (`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`), `APP_SECRET_KEY`.

## Language

Project documentation and comments are in Chinese (Simplified). Code identifiers and API paths are in English. 在对话中应使用中文。

## Reference Docs

- `SPEC.md` — **当前实际开发规格（以此为准）**，包含页面规格、API 规格、数据策略
- `docs/开发指南.md` — 环境配置、前后端启动、Git 工作流、常见问题
- `docs/分工安排.md` — 五人分工详细任务清单和时间线
- `docs/架构设计与开发指南.md` — 原始架构设计（参考用，部分功能已裁剪）
- `docs/上海美食大数据分析平台-需求分析文档.md` — 原始需求文档（参考用）
