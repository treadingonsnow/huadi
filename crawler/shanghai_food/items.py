import scrapy

class RestaurantItem(scrapy.Item):
    name = scrapy.Field()
    address = scrapy.Field()
    cuisine = scrapy.Field()
    avg_price = scrapy.Field()
    rating = scrapy.Field()
    district = scrapy.Field()
    phone = scrapy.Field()  # 用于脱敏