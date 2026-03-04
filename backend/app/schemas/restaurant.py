# 餐厅相关 Pydantic Schema
# 功能：定义请求/响应数据校验模型
# 包含：
# - RestaurantSearchQuery   搜索请求参数（keyword, district, cuisine_type, price_min/max, rating_min, page, size, sort, order）
# - RestaurantListItem      搜索结果列表项（基础信息摘要）
# - RestaurantDetail        餐厅详情（完整信息 + 评分 + 菜品列表）
# - RestaurantListResponse  分页列表响应（total, page, size, items）
# - FavoriteRequest         收藏请求
