# 协同过滤推荐算法
# 功能：
# - build_user_item_matrix()      构建用户-餐厅评分矩阵
# - calc_user_similarity()        计算用户相似度（余弦相似度）
# - predict_rating()              预测用户对未评分餐厅的评分
# - get_recommendations()         获取Top N推荐餐厅列表
# 算法：基于用户的协同过滤（User-based CF）
# 依赖：numpy, scikit-learn (cosine_similarity)
