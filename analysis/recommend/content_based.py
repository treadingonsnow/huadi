# 基于内容的推荐算法
# 功能：
# - build_feature_vector()        构建餐厅特征向量（菜系、价格区间、评分、区域、标签）
# - calc_restaurant_similarity()  计算餐厅间相似度（余弦相似度）
# - get_similar_restaurants()     获取与目标餐厅最相似的Top N餐厅
# 算法：基于内容的推荐（Content-based Filtering）
# 特征：菜系类型(one-hot) + 价格等级 + 综合评分 + 区域(one-hot) + 场景标签
# 依赖：numpy, scikit-learn
