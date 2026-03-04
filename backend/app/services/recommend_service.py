# 智能推荐业务服务
# 功能：
# - get_personalized_recommendations()  个性化推荐（调用协同过滤算法，基于用户行为数据）
# - get_similar_restaurants()           相似餐厅推荐（调用内容相似度算法）
# - get_scene_recommendations()         场景推荐（根据场景标签匹配餐厅）
# - get_hot_restaurants()               热门推荐（综合热度得分排序）
# 注意：推荐结果使用 Redis 缓存，个性化推荐需要用户登录
