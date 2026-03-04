# 菜品信息 ORM 模型
# 对应数据表：dish_info
# 字段：
# - dish_id         VARCHAR(50) PK  菜品唯一标识
# - restaurant_id   VARCHAR(50) FK  关联餐厅ID
# - dish_name       VARCHAR(200)    菜品名称
# - dish_price      DECIMAL(10,2)   菜品价格（元）
# - monthly_sales   INT             近30天销量
# - dish_category   VARCHAR(50)     菜品分类（热菜/凉菜/主食/饮品等）
# - mention_count   INT             评论中被提及次数
# - image_url       VARCHAR(500)    菜品图片URL
# - create_time     DATETIME        创建时间
# - update_time     DATETIME        更新时间
