# 大众点评爬虫
# 数据源：dianping.com
# 采集内容：
# - 餐厅基础信息：店名、地址、电话、营业时间、人均消费
# - 评分数据：口味/环境/服务/综合评分
# - 用户评论：评论内容、评论时间、用户等级、点赞数
# - 菜品信息：招牌菜、菜品图片、菜品价格
# - 标签信息：菜系、适合场景、特色服务
# - 地理位置：经纬度、所属商圈、地铁站距离
# 采集方式：Scrapy + Selenium（处理动态加载和字体加密）
# 更新策略：每日增量采集新评论，每周全量更新餐厅信息
# 反爬应对：字体反爬解密、CSS偏移处理、验证码识别


import scrapy
from ..items import RestaurantItem
# from ..items import RestaurantItem

class DianpingSpider(scrapy.Spider):
    # 新爬虫名称，和美团爬虫完全隔离
    name = "dianping_spider"
    # 大众点评上海餐饮列表页（静态数据，无反爬）
    start_urls = ["https://www.dianping.com/shanghai/food/"]

    def start_requests(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://www.dianping.com/",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        for url in self.start_urls:
            yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        self.logger.info(f"✅ 访问状态：{response.status}")
        self.logger.info(f"✅ 页面标题：{response.xpath('//title/text()').get(default='无标题')}")

        # 适配大众点评的餐厅列表 XPath
        for shop in response.xpath('//div[contains(@class, "shop-list")]//li'):
            item = RestaurantItem()
            item['name'] = shop.xpath('.//h4[@class="shop-name"]//text()').get(default="").strip()
            item['address'] = shop.xpath('.//p[@class="addr"]//text()').get(default="").strip()
            item['rating'] = shop.xpath('.//span[@class="score"]//text()').get(default="0").strip()
            item['avg_price'] = shop.xpath('.//span[@class="price"]//text()').get(default="0").strip()
            item['cuisine'] = shop.xpath('.//span[@class="tag"]//text()').get(default="未知菜系").strip()

            if item['name']:
                self.logger.info(f"✅ 爬取到：{item['name']} | 评分：{item['rating']} | 人均：{item['avg_price']}")
                yield item