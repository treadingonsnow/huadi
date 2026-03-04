-- 数据库初始化脚本
-- 功能：创建数据库和核心数据表

CREATE DATABASE IF NOT EXISTS shanghai_food DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE shanghai_food;

-- 餐厅基础信息表
-- 字段详见 backend/app/models/restaurant.py

-- 评分评论表
-- 字段详见 backend/app/models/review.py

-- 菜品信息表
-- 字段详见 backend/app/models/dish.py

-- 用户表
-- 字段详见 backend/app/models/user.py

-- 用户收藏表
-- user_id, restaurant_id, create_time

-- 爬虫任务表
-- 字段详见 backend/app/models/crawl_task.py

-- 爬虫运行日志表
-- log_id, task_id, run_time, status, items_count, error_msg, duration

-- 操作审计日志表
-- log_id, user_id, action, resource, detail, ip, create_time

-- 报告任务表
-- task_id, task_type, params_json, status, progress, file_path, user_id, create_time, finish_time
