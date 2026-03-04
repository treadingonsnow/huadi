# 热门菜品挖掘模块
# 功能：
# - extract_dishes_from_review()  从单条评论中提取菜品名称（基于菜品词典匹配 + jieba分词）
# - batch_extract_dishes()        批量提取菜品
# - rank_hot_dishes()             热门菜品排行（按提及频率排序）
# - get_dish_sentiment()          菜品级情感分析（提取包含菜品名的句子，分析情感）
# 依赖：jieba, config/dictionaries/cuisine_dict.py（热门菜品词典）
