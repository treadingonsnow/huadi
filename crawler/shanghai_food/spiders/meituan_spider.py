# 美团爬虫
# 数据源：meituan.com
# 采集内容：
# - 餐厅基础信息：店名、地址、电话、营业时间、人均消费
# - 销量数据：月销量、团购销量、外卖销量
# - 优惠信息：团购套餐、优惠券、满减活动
# - 用户评价：评论内容、评分、晒图数量
# - 配送信息：配送范围、配送费、预计送达时间
# 采集方式：Scrapy + API逆向
# 更新策略：每日增量采集


import scrapy
import random
from datetime import datetime
from ..items import RestaurantItem


class MeituanSpider(scrapy.Spider):
    name = "meituan_spider"
    allowed_domains = ["meituan.com"]
    start_urls = ["https://www.meituan.com/meishi/c17/"]  # 上海美食列表页

    # 反爬控制配置
    custom_settings = {
        "DOWNLOAD_DELAY": random.uniform(1, 3),  # 随机延迟1-3秒
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "RETRY_TIMES": 2,  # 失败重试2次
        "LOG_LEVEL": "WARNING",  # 简化日志输出
    }

    def parse(self, response):
        # 🔴 核心：检测验证码/封禁，立即停止爬虫
        if self._check_anti_crawl(response):
            self.logger.warning("⚠️ 检测到验证码/访问受限，立即停止爬虫！")
            return  # 直接终止，不继续解析/翻页

        # 🟢 解析餐厅列表数据
        restaurant_list = response.xpath('//div[contains(@class, "restaurant-item") or contains(@class, "poi-item")]')

        for item_node in restaurant_list:
            item = RestaurantItem()

            # 提取核心字段
            item["name"] = item_node.xpath('.//*[contains(@class, "name") or contains(@class, "title")]/text()').get(
                default="").strip()
            item["address"] = item_node.xpath('.//*[contains(@class, "address")]/text()').get(default="").strip()
            item["cuisine"] = item_node.xpath(
                './/*[contains(@class, "cate") or contains(@class, "category")]/text()').get(default="").strip()

            # 均价处理（去除¥/人均，转数字）
            price_text = item_node.xpath('.//*[contains(@class, "price")]/text()').get(default="0").strip()
            item["avg_price"] = int(''.join(filter(str.isdigit, price_text)) or 0)

            # 评分处理
            score_text = item_node.xpath('.//*[contains(@class, "score")]/text()').get(default="0").strip()
            item["score"] = float(score_text) if score_text.replace('.', '').isdigit() else 0.0

            # 区域提取（从地址中解析上海行政区）
            item["area"] = self._extract_area_from_address(item["address"])

            # 爬取时间
            item["crawl_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 跳过空数据
            if item["name"]:
                yield item

        # 🟡 翻页逻辑（如需关闭翻页，直接注释这段即可）
        next_page = response.xpath('//a[contains(@class, "next")]/@href').get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse
            )

    def _check_anti_crawl(self, response):
        """检测反爬的核心方法，满足任一条件即判定为被封/需要验证码"""
        # 1. 状态码检测（403/405/503为典型封禁状态）
        if response.status in [403, 405, 503]:
            return True
        # 2. 页面关键词检测（验证码/访问受限）
        anti_keywords = ["验证码", "验证中心", "访问受限", "封禁", "forbidden", "verify"]
        if any(keyword in response.text.lower() for keyword in anti_keywords):
            return True
        # 3. 页面长度异常（正常页面远大于1000字符）
        if len(response.text) < 1000:
            return True
        return False

    def _extract_area_from_address(self, address):
        """从地址中提取上海行政区（16区标准化）"""
        shanghai_districts = [
            "黄浦区", "徐汇区", "长宁区", "静安区", "普陀区", "虹口区", "杨浦区",
            "闵行区", "宝山区", "嘉定区", "浦东新区", "金山区", "松江区", "青浦区", "奉贤区", "崇明区"
        ]
        for district in shanghai_districts:
            if district in address:
                return district
        return ""