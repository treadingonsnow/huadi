# Scrapy 项目配置
# 功能：
# - BOT_NAME, SPIDER_MODULES 等基础配置
# - DOWNLOAD_DELAY = 1.0          遵守采集频率≤1次/秒
# - CONCURRENT_REQUESTS = 8       并发请求数
# - ROBOTSTXT_OBEY = True         遵守 robots.txt
# - DOWNLOADER_MIDDLEWARES        启用代理IP中间件、User-Agent轮换中间件、反爬中间件
# - ITEM_PIPELINES                启用数据清洗Pipeline、数据入库Pipeline
# - RETRY_TIMES = 3               失败重试3次
# - LOG_LEVEL = 'INFO'            日志级别
# - MySQL/Redis 连接配置（从环境变量读取）
