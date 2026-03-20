# Scrapy Item 定义
# 功能：定义爬虫采集的数据结构
# 包含：
# - RestaurantItem     餐厅基础信息（名称、地址、电话、营业时间、人均消费、菜系、经纬度、商圈等）
# - ReviewItem         评论数据（评分、评论内容、评论时间、用户ID、点赞数）
# - DishItem           菜品数据（菜品名称、价格、月销量、分类）
# - NoteItem           探店笔记（标题、正文、点赞数、收藏数、标签）—— 小红书/抖音
# - GovDataItem        政府公开数据（食品经营许可证、抽检结果、行政处罚）


import scrapy

class RestaurantItem(scrapy.Item):
    name = scrapy.Field()
    address = scrapy.Field()
    cuisine = scrapy.Field()
    avg_price = scrapy.Field()
    rating = scrapy.Field()
    district = scrapy.Field()
    phone = scrapy.Field()  # 用于脱敏
