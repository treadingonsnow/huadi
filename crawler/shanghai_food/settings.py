BOT_NAME = "shanghai_food"

SPIDER_MODULES = ["shanghai_food.spiders"]
NEWSPIDER_MODULE = "shanghai_food.spiders"

# 开启MySQL管道
ITEM_PIPELINES = {}

# MySQL配置（替换为你的实际信息）
MYSQL_CONFIG = {
    "host": "192.168.54.99",
    "user": "team",
    "password": "team123456",
    "database": "shanghai_food",
    "charset": "utf8mb4"
}

# 开启随机UA中间件
DOWNLOADER_MIDDLEWARES = {
    "shanghai_food.middlewares.RandomUserAgentMiddleware": 543,
}

# 基础请求头
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.meituan.com/",
}

# 爬虫基础配置
ROBOTSTXT_OBEY = False
DOWNLOAD_TIMEOUT = 10
