# 餐厅信息 ORM 模型
# 对应数据表：restaurant_info
# 字段：
# - restaurant_id   VARCHAR(50) PK  餐厅唯一标识
# - restaurant_name VARCHAR(200)    餐厅名称
# - address         VARCHAR(500)    餐厅地址
# - phone           VARCHAR(20)     联系电话（已脱敏）
# - business_hours  VARCHAR(100)    营业时间
# - avg_price       DECIMAL(10,2)   人均消费（元）
# - cuisine_type    VARCHAR(50)     菜系类型
# - district        VARCHAR(50)     所属行政区
# - business_area   VARCHAR(100)    所属商圈
# - latitude        DECIMAL(10,6)   纬度
# - longitude       DECIMAL(10,6)   经度
# - subway_distance INT             地铁距离（米）
# - data_source     VARCHAR(50)     数据来源
# - crawl_time      DATETIME        采集时间
# - create_time     DATETIME        创建时间
# - update_time     DATETIME        更新时间
# 索引：district, business_area, cuisine_type, (latitude, longitude)
