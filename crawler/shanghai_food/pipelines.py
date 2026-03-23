# Scrapy Pipeline
# 功能：数据清洗和入库
# 包含：



import pymysql
from itemadapter import ItemAdapter

class ShanghaiFoodPipeline:
    def __init__(self, mysql_config):
        self.mysql_config = mysql_config
        self.conn = None
        self.cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        # 从settings读取MySQL配置
        return cls(mysql_config=crawler.settings.getdict("MYSQL_CONFIG"))

    def open_spider(self, spider):
        """爬虫启动时连接MySQL"""
        try:
            self.conn = pymysql.connect(
                host=self.mysql_config["host"],
                user=self.mysql_config["user"],
                password=self.mysql_config["password"],
                database=self.mysql_config["database"],
                charset="utf8mb4"
            )
            self.cursor = self.conn.cursor()
            spider.logger.warning("✅ MySQL连接成功")
        except Exception as e:
            spider.logger.error(f"❌ MySQL连接失败: {e}")
            raise  # 连接失败直接终止爬虫

    def process_item(self, item, spider):
        """写入restaurant_info表"""
        adapter = ItemAdapter(item)
        sql = """
        INSERT INTO restaurant_info (name, address, cuisine, avg_price, score, area, crawl_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        try:
            self.cursor.execute(sql, (
                adapter.get("name"),
                adapter.get("address"),
                adapter.get("cuisine"),
                adapter.get("avg_price"),
                adapter.get("score"),
                adapter.get("area"),
                adapter.get("crawl_time")
            ))
            self.conn.commit()
        except Exception as e:
            spider.logger.error(f"❌ 数据写入失败: {e}")
            self.conn.rollback()
        return item

    def close_spider(self, spider):
        """爬虫关闭时断开MySQL连接"""
        if self.conn:
            self.cursor.close()
            self.conn.close()
            spider.logger.warning("✅ MySQL连接已关闭")