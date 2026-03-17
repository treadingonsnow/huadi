# 上海美食大数据分析平台 — 项目规格文档

> 版本：v1.0 | 日期：2026-03-17 | 状态：已确认

---

## 一、项目背景与目标

**课程作业/毕业设计展示项目**，面向老师评审。

核心目标：
- 展示完整的大数据平台技术栈（爬虫 → 存储 → 分析 → 可视化）
- 提供真实或高质量的上海餐厅数据（1000-5000 条）
- 视觉效果专业，图表丰富，交互流畅

---

## 二、功能范围（已裁剪）

### 必做（MVP）

| 页面 | 功能 |
|------|------|
| 登录页 | 用户名+密码登录，JWT 认证，登录后跳转大屏 |
| 数据可视化大屏 | 多维度图表展示上海餐厅数据 |
| 餐厅搜索页 | 关键词+筛选条件搜索餐厅，展示列表和详情 |

### 砍掉（不做）

- ~~报告生成（PDF/Word）~~
- ~~Celery 异步任务队列~~
- ~~推荐系统~~
- ~~竞争分析~~
- ~~用户注册~~
- ~~小红书/政府数据爬虫~~
- ~~Redis 缓存~~（可选，有时间再加）

---

## 三、页面详细规格

### 3.1 登录页

**路由**：`/login`

**功能**：
- 用户名 + 密码表单
- 点击登录 → 调用 `POST /api/v1/auth/login`
- 登录成功 → 保存 JWT token 到 localStorage → 跳转 `/dashboard`
- 登录失败 → 显示错误提示

**预置账号**（硬编码在数据库初始化脚本中）：
- admin / admin123
- analyst / analyst123

**视觉**：美食主题暗色风，背景图或渐变色，居中卡片

---

### 3.2 数据可视化大屏

**路由**：`/dashboard`

**布局**：全屏暗色大屏，顶部标题栏，主体 3 列网格布局

**图表列表**（6-8 个图表）：

| 图表 | 类型 | 数据来源 |
|------|------|---------|
| 上海各区餐厅分布 | ECharts 上海地图（区域着色） | `GET /api/v1/analysis/area-distribution` |
| 菜系分布 | 饼图/环形图 | `GET /api/v1/analysis/cuisine-distribution` |
| 价格区间分布 | 柱状图 | `GET /api/v1/analysis/price-distribution` |
| 评分分布 | 柱状图或直方图 | `GET /api/v1/analysis/rating-distribution` |
| 口碑分析（好评/差评关键词） | 词云图 | `GET /api/v1/analysis/review-keywords` |
| 各区平均消费对比 | 横向柱状图 | `GET /api/v1/analysis/area-avg-price` |
| 数据概览（总数/平均分/平均价格） | 数字卡片 | `GET /api/v1/analysis/overview` |

**视觉风格**：
- 背景：深色（`#0d1117` 或 `#1a1a2e`）
- 主色：红色 `#e63946` + 金色 `#ffd700`
- 图表配色：ECharts 暗色主题
- 字体：白色/浅灰

---

### 3.3 餐厅搜索页

**路由**：`/search`

**功能**：
- 顶部搜索栏：关键词输入
- 筛选条件：菜系（下拉）、区域（下拉）、价格区间（下拉）、评分（下拉）
- 结果列表：卡片形式，显示餐厅名、菜系、区域、均价、评分
- 点击卡片 → 展开详情（弹窗或侧边栏）：地址、电话（脱敏）、评价摘要

**API**：`GET /api/v1/restaurants/search?keyword=&cuisine=&district=&price_min=&price_max=&rating_min=&page=1&page_size=20`

---

## 四、数据模型

### 核心表（MySQL）

```sql
-- 餐厅信息表
CREATE TABLE restaurant_info (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(200) NOT NULL,
    address     VARCHAR(500),
    phone       VARCHAR(50),          -- 脱敏存储
    cuisine_type VARCHAR(50),
    district    VARCHAR(50),          -- 区域（浦东新区、黄浦区等）
    business_area VARCHAR(100),       -- 商圈
    latitude    DECIMAL(10,7),
    longitude   DECIMAL(10,7),
    avg_price   DECIMAL(10,2),        -- 人均消费
    rating      DECIMAL(3,1),         -- 综合评分
    review_count INT DEFAULT 0,
    data_source VARCHAR(50),          -- meituan / dataset
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 评价表（可选，有数据再建）
CREATE TABLE restaurant_review (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    restaurant_id   BIGINT NOT NULL,
    rating          DECIMAL(3,1),
    content         TEXT,
    sentiment_score DECIMAL(4,3),     -- 情感分数 0-1
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurant_info(id)
);

-- 用户表
CREATE TABLE sys_user (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    username    VARCHAR(50) UNIQUE NOT NULL,
    password    VARCHAR(200) NOT NULL,  -- BCrypt hash
    role        VARCHAR(20) DEFAULT 'user',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 五、API 规格

### 统一响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

### 认证

```
POST /api/v1/auth/login
Body: { "username": "admin", "password": "admin123" }
Response: { "code": 200, "data": { "access_token": "...", "token_type": "bearer" } }
```

所有非登录接口需要 Header：`Authorization: Bearer <token>`

### 餐厅搜索

```
GET /api/v1/restaurants/search
Query: keyword, cuisine, district, price_min, price_max, rating_min, page, page_size
Response: { "code": 200, "data": { "total": 1234, "items": [...] } }

GET /api/v1/restaurants/{id}
Response: { "code": 200, "data": { ...restaurant detail... } }
```

### 分析接口

```
GET /api/v1/analysis/overview
Response: { "total_count": 3000, "avg_rating": 4.2, "avg_price": 85.5, "district_count": 16 }

GET /api/v1/analysis/area-distribution
Response: { "districts": [{"name": "浦东新区", "count": 450}, ...] }

GET /api/v1/analysis/cuisine-distribution
Response: { "cuisines": [{"name": "川菜", "count": 320, "percentage": 10.7}, ...] }

GET /api/v1/analysis/price-distribution
Response: { "ranges": [{"label": "50元以下", "count": 200}, ...] }

GET /api/v1/analysis/rating-distribution
Response: { "ratings": [{"range": "4.5-5.0", "count": 500}, ...] }

GET /api/v1/analysis/review-keywords
Response: { "positive": [{"word": "好吃", "count": 1200}, ...], "negative": [...] }

GET /api/v1/analysis/area-avg-price
Response: { "districts": [{"name": "黄浦区", "avg_price": 120.5}, ...] }
```

---

## 六、技术栈（最终确认）

| 层 | 技术 | 备注 |
|----|------|------|
| 前端 | React 19 + Vite + Ant Design + ECharts | 已有骨架 |
| 后端 | FastAPI + SQLAlchemy + MySQL | 去掉 Celery/Redis |
| 爬虫 | Scrapy + Selenium | 只爬美团 |
| 数据库 | MySQL 8.0 | 共享一台服务器 |
| 认证 | JWT + BCrypt | 简单登录，无注册 |
| 地图 | ECharts 内置上海地图 | 无需 API Key |

---

## 七、数据策略

### 主方案：爬取美团

- 目标：上海各区餐厅基本信息（名称、地址、菜系、均价、评分）
- 工具：Scrapy + Selenium（处理 JS 渲染）
- 目标数量：1000-5000 条
- 反爬应对：随机 User-Agent、请求间隔 1-3 秒、代理池（可选）

### 备用方案：公开数据集

如果美团爬虫失败，立即切换：
1. 搜索 Kaggle / GitHub 上的上海餐厅数据集
2. 关键词：`Shanghai restaurant dataset`、`大众点评 数据集`
3. 数据清洗后导入 MySQL（字段映射到 `restaurant_info` 表）

### 数据清洗要求

- 去重（按餐厅名+地址）
- 脱敏（电话号码替换为 `138****1234` 格式）
- 标准化区域名（统一为 16 个区的标准名称）
- 菜系归类（参考 `config/dictionaries/cuisine_dict.py`）
- 缺失值处理（均价缺失填 0，评分缺失填 0）

---

## 八、风险与应对

| 风险 | 概率 | 应对 |
|------|------|------|
| 美团爬虫被封 | 高 | 立即切换备用数据集，不要在爬虫上浪费超过 3 天 |
| 前后端接口不一致 | 中 | 先定好 API 规格（本文档），前端先用 mock 数据开发 |
| 环境配置问题 | 中 | 统一用 Docker Compose 启动 MySQL，见开发指南 |
| 时间不够 | 高 | 搜索页可以砍掉，大屏图表可以减少到 4 个 |
| Git 冲突 | 低 | 各人负责不同目录，减少冲突 |

---

## 九、验收标准

- [ ] 登录页可以正常登录，跳转大屏
- [ ] 大屏展示至少 4 个图表，数据来自真实数据库
- [ ] 上海地图区域着色正确
- [ ] 搜索页可以搜索和筛选餐厅（如果做了）
- [ ] 数据库中有 1000+ 条真实/高质量数据
- [ ] 项目可以在本地一键启动

---

## 十、不在范围内（明确排除）

- 报告生成（PDF/Word）
- Celery 异步任务
- Redis 缓存
- 推荐系统
- 竞争分析
- 用户注册/权限管理
- 小红书/政府数据爬虫
- 趋势预测
