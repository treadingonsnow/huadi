# 爬虫任务 ORM 模型
# 对应数据表：crawl_task
# 字段：
# - task_id        INT PK AUTO_INCREMENT  任务ID
# - task_name      VARCHAR(200)           任务名称
# - data_source    VARCHAR(50)            数据源（dianping/meituan/xiaohongshu/gov）
# - task_type      VARCHAR(20)            任务类型（full/incremental 全量/增量）
# - cron_expr      VARCHAR(50)            调度表达式
# - status         VARCHAR(20)            状态（pending/running/success/failed）
# - config_json    JSON                   爬虫配置（目标URL、采集规则等）
# - last_run_time  DATETIME               上次运行时间
# - total_count    INT                    累计采集数量
# - success_rate   DECIMAL(5,2)           采集成功率
# - create_time    DATETIME               创建时间
# - update_time    DATETIME               更新时间
#
# 关联表：crawl_log（爬虫运行日志）
# - log_id, task_id, run_time, status, items_count, error_msg, duration
