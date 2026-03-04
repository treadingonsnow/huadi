# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

上海美食大数据分析平台 — a full-stack platform for collecting, analyzing, and visualizing Shanghai restaurant data from multiple sources (Dianping, Meituan, Xiaohongshu, government portals).

## Architecture

Four independent modules sharing a MySQL database:

```
frontend/ (React 19 + Vite + Ant Design + ECharts)
    ↓ REST API (/api/v1)
backend/ (FastAPI + SQLAlchemy + Celery)
    ├→ MySQL 8.0 (structured data)
    ├→ Redis (cache + Celery broker)
    └→ analysis/ (Pandas + Scikit-learn + NLP)

crawler/ (Scrapy + Selenium) → MySQL
```

- **backend/** — FastAPI app. Entry: `backend/app/main.py`. Routes in `api/v1/`, ORM models in `models/`, business logic in `services/`. Async report generation via Celery.
- **crawler/** — Scrapy project (`crawler/shanghai_food/`). Four spiders (dianping, meituan, xiaohongshu, gov_data). Data flows through `pipelines.py` (clean → validate → insert MySQL). Config in `settings.py`.
- **analysis/** — Pure Python analysis modules consumed by backend services. Submodules: `nlp/` (jieba + SnowNLP sentiment), `recommend/` (collaborative filtering, content-based, scene-based).
- **frontend/** — React SPA using `.jsx` files. Vite dev server proxies `/api` to backend port 8000. State via Zustand, charts via echarts-for-react, maps via AMap JS API. UI components from Ant Design.
- **config/dictionaries/** — Business domain dictionaries (cuisine types, districts, sentiment keywords) used by both crawler pipelines and analysis modules. Edit these to add new cuisines, districts, or keywords without changing code logic.

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

### Celery Worker (from `backend/`)
```bash
celery -A app.main worker --loglevel=info
```

### Crawler (from `crawler/`)
```bash
pip install -r requirements.txt
scrapy crawl dianping_spider
scrapy crawl meituan_spider
scrapy crawl xiaohongshu_spider
scrapy crawl gov_data_spider
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
- **Crawl rate limit**: 1 request/second max, respects robots.txt. Configured in `crawler/shanghai_food/settings.py`.
- **Data desensitization**: Phone numbers and user IDs must be masked before storage. Handled in `crawler/shanghai_food/pipelines.py`.
- **Auth**: JWT tokens (24h expiry), BCrypt password hashing, RBAC with four roles (admin/analyst/editor/user). Implementation in `backend/app/core/security.py` and `backend/app/core/deps.py`.
- **Async tasks**: Report generation and heavy analysis run as Celery tasks, not in request handlers.
- **Analysis caching**: Analysis results cached in Redis with TTL matching data update frequency (T+1 daily).

## Configuration

Copy `.env.example` → `.env` and `config/config.example.yaml` → `config/config.yaml` before running. Key env vars: MySQL/Redis connections, `AMAP_API_KEY`, `APP_SECRET_KEY`.

## Language

Project documentation and comments are in Chinese (Simplified). Code identifiers and API paths are in English.

## Reference Docs

- `docs/架构设计与开发指南.md` — Detailed architecture walkthrough with data flow diagrams, module explanations, and onboarding guide (Chinese)
- `docs/上海美食大数据分析平台-需求分析文档.md` — Functional and non-functional requirements, data model DDL, API specs
- `docs/上海美食大数据分析平台-需求调研报告.md` — Business use cases, data source inventory, domain dictionaries
