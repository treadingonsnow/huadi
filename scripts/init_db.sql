-- ============================================================
-- 上海美食大数据分析平台 — 数据库初始化脚本
-- 执行方式：mysql -h <host> -u root -p < scripts/init_db.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS shanghai_food
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE shanghai_food;

-- ─────────────────────────────────────────────
-- 1. 餐厅基础信息表
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS restaurant_info (
    restaurant_id   VARCHAR(50)     NOT NULL COMMENT '餐厅唯一标识（美团ID或UUID）',
    restaurant_name VARCHAR(200)    NOT NULL COMMENT '餐厅名称',
    address         VARCHAR(500)    DEFAULT NULL COMMENT '餐厅地址',
    phone           VARCHAR(20)     DEFAULT NULL COMMENT '联系电话（已脱敏，如138****1234）',
    business_hours  VARCHAR(100)    DEFAULT NULL COMMENT '营业时间',
    avg_price       DECIMAL(10,2)   DEFAULT 0.00 COMMENT '人均消费（元）',
    rating_overall  DECIMAL(3,1)    DEFAULT 0.0  COMMENT '综合评分（1-5）',
    review_count    INT             DEFAULT 0    COMMENT '评论总数',
    cuisine_type    VARCHAR(50)     DEFAULT NULL COMMENT '菜系类型',
    district        VARCHAR(50)     DEFAULT NULL COMMENT '所属行政区（如浦东新区）',
    business_area   VARCHAR(100)    DEFAULT NULL COMMENT '所属商圈（如陆家嘴）',
    latitude        DECIMAL(10,6)   DEFAULT NULL COMMENT '纬度',
    longitude       DECIMAL(10,6)   DEFAULT NULL COMMENT '经度',
    subway_distance INT             DEFAULT NULL COMMENT '最近地铁距离（米）',
    data_source     VARCHAR(50)     DEFAULT 'meituan' COMMENT '数据来源',
    crawl_time      DATETIME        DEFAULT NULL COMMENT '采集时间',
    create_time     DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time     DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (restaurant_id),
    INDEX idx_district      (district),
    INDEX idx_cuisine       (cuisine_type),
    INDEX idx_business_area (business_area),
    INDEX idx_avg_price     (avg_price),
    INDEX idx_rating        (rating_overall),
    INDEX idx_latlng        (latitude, longitude)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='餐厅基础信息表';

-- ─────────────────────────────────────────────
-- 2. 评分评论表
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS restaurant_review (
    review_id            VARCHAR(50)   NOT NULL COMMENT '评论唯一标识',
    restaurant_id        VARCHAR(50)   NOT NULL COMMENT '关联餐厅ID',
    user_id              VARCHAR(50)   DEFAULT NULL COMMENT '用户ID（已脱敏）',
    rating_overall       DECIMAL(3,1)  DEFAULT NULL COMMENT '综合评分（1-5）',
    rating_taste         DECIMAL(3,1)  DEFAULT NULL COMMENT '口味评分',
    rating_environment   DECIMAL(3,1)  DEFAULT NULL COMMENT '环境评分',
    rating_service       DECIMAL(3,1)  DEFAULT NULL COMMENT '服务评分',
    review_content       TEXT          DEFAULT NULL COMMENT '评论内容',
    review_time          DATETIME      DEFAULT NULL COMMENT '评论时间',
    like_count           INT           DEFAULT 0    COMMENT '点赞数',
    sentiment_score      DECIMAL(3,2)  DEFAULT NULL COMMENT '情感得分（-1到1，正数为正面）',
    data_source          VARCHAR(50)   DEFAULT 'meituan' COMMENT '数据来源',
    create_time          DATETIME      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (review_id),
    INDEX idx_restaurant_id (restaurant_id),
    INDEX idx_review_time   (review_time),
    CONSTRAINT fk_review_restaurant
        FOREIGN KEY (restaurant_id) REFERENCES restaurant_info(restaurant_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评分评论表';

-- ─────────────────────────────────────────────
-- 3. 用户表
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sys_user (
    user_id       INT           NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    username      VARCHAR(50)   NOT NULL COMMENT '用户名',
    password_hash VARCHAR(128)  NOT NULL COMMENT '密码哈希（BCrypt）',
    email         VARCHAR(100)  DEFAULT NULL COMMENT '邮箱',
    role          VARCHAR(20)   NOT NULL DEFAULT 'user' COMMENT '角色（admin/user）',
    is_active     TINYINT(1)    NOT NULL DEFAULT 1 COMMENT '是否启用（1启用 0禁用）',
    create_time   DATETIME      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    last_login    DATETIME      DEFAULT NULL COMMENT '最后登录时间',
    PRIMARY KEY (user_id),
    UNIQUE KEY uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统用户表';

-- ─────────────────────────────────────────────
-- 3.5 用户收藏表
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_favorites (
    user_id       INT           NOT NULL COMMENT '用户ID',
    restaurant_id VARCHAR(50)   NOT NULL COMMENT '餐厅ID',
    create_time   DATETIME      DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
    PRIMARY KEY (user_id, restaurant_id),
    CONSTRAINT fk_fav_user
        FOREIGN KEY (user_id) REFERENCES sys_user(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_fav_restaurant
        FOREIGN KEY (restaurant_id) REFERENCES restaurant_info(restaurant_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户收藏表';

-- ─────────────────────────────────────────────
-- 4. 数据清洗日志表
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS clean_log (
    id           INT           NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    task_name    VARCHAR(200)  NOT NULL COMMENT '任务名称',
    stage        VARCHAR(50)   DEFAULT NULL COMMENT '清洗阶段（load/dedup/normalize/validate/insert/hdfs/hive）',
    level        VARCHAR(20)   NOT NULL DEFAULT 'INFO' COMMENT '日志级别（INFO/WARNING/ERROR）',
    message      TEXT          NOT NULL COMMENT '日志内容',
    record_count INT           DEFAULT NULL COMMENT '影响记录数',
    create_time  DATETIME      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    INDEX idx_task_name  (task_name),
    INDEX idx_level      (level),
    INDEX idx_create_time(create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据清洗日志表';

-- ─────────────────────────────────────────────
-- 5. 爬虫任务表
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS crawl_task (
    task_id       INT           NOT NULL AUTO_INCREMENT COMMENT '任务ID',
    task_name     VARCHAR(200)  NOT NULL COMMENT '任务名称',
    data_source   VARCHAR(50)   NOT NULL DEFAULT 'meituan' COMMENT '数据源',
    task_type     VARCHAR(20)   NOT NULL DEFAULT 'full' COMMENT '任务类型（full全量/incremental增量）',
    status        VARCHAR(20)   NOT NULL DEFAULT 'pending' COMMENT '状态（pending/running/success/failed）',
    total_count   INT           DEFAULT 0 COMMENT '累计采集数量',
    success_rate  DECIMAL(5,2)  DEFAULT NULL COMMENT '采集成功率（%）',
    error_msg     TEXT          DEFAULT NULL COMMENT '错误信息',
    start_time    DATETIME      DEFAULT NULL COMMENT '开始时间',
    end_time      DATETIME      DEFAULT NULL COMMENT '结束时间',
    create_time   DATETIME      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (task_id),
    INDEX idx_status      (status),
    INDEX idx_data_source (data_source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='爬虫任务表';

-- ─────────────────────────────────────────────
-- 5. 预置账号（密码均为 BCrypt hash）
--    admin    → 明文密码: admin123
--    analyst  → 明文密码: analyst123
-- ─────────────────────────────────────────────
INSERT IGNORE INTO sys_user (username, password_hash, role, is_active) VALUES
('admin',   '$2b$12$r9iD.quLuqy87On1w4aZ9.paglgIOtEJwtzEbztH5oOXdRwXgQcYa', 'admin', 1),
('analyst', '$2b$12$aBvV/iKePlWU2CWX091XCu6/3FP1JgzoTNSMaDJTdPCecrp48AG96', 'user',  1);

-- ─────────────────────────────────────────────
-- 注意：如果用户已存在（INSERT IGNORE 跳过），
-- 需要用 UPDATE 强制刷新密码：
--
--   UPDATE sys_user SET password_hash='$2b$12$r9iD.quLuqy87On1w4aZ9.paglgIOtEJwtzEbztH5oOXdRwXgQcYa' WHERE username='admin';
--   UPDATE sys_user SET password_hash='$2b$12$aBvV/iKePlWU2CWX091XCu6/3FP1JgzoTNSMaDJTdPCecrp48AG96' WHERE username='analyst';
-- ─────────────────────────────────────────────
