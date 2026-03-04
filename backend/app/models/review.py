# 评分评论 ORM 模型
# 对应数据表：restaurant_review
# 字段：
# - review_id         VARCHAR(50) PK  评论唯一标识
# - restaurant_id     VARCHAR(50) FK  关联餐厅ID
# - user_id           VARCHAR(50)     用户ID（已脱敏）
# - rating_overall    DECIMAL(3,1)    综合评分 (1-5)
# - rating_taste      DECIMAL(3,1)    口味评分
# - rating_environment DECIMAL(3,1)   环境评分
# - rating_service    DECIMAL(3,1)    服务评分
# - review_content    TEXT            评论内容
# - review_time       DATETIME        评论时间
# - like_count        INT             点赞数
# - sentiment_score   DECIMAL(3,2)    情感得分 (-1到1)
# - data_source       VARCHAR(50)     数据来源
# - create_time       DATETIME        创建时间
# 索引：restaurant_id, review_time
