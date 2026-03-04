# 场景推荐算法
# 功能：
# - match_scene_tags()            根据用餐场景匹配餐厅标签
# - score_by_scene()              计算餐厅的场景匹配得分
# - get_scene_recommendations()   获取指定场景下的推荐餐厅列表
# 支持场景：约会、聚餐、商务、家庭、独自、团建、生日、下午茶
# 算法：基于标签匹配 + 评分加权排序
# 依赖：config/dictionaries/scene_dict.py（场景关键词字典）
