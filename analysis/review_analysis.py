# 口碑分析模块
# 功能：
# - calc_rating_distribution()    评分区间分布统计
# - analyze_review_sentiment()    批量评论情感分析（调用 nlp/sentiment.py）
# - extract_hot_dishes()          热门菜品挖掘（调用 nlp/dish_mining.py）
# - analyze_service_quality()     服务质量分析（提取服务相关评论，分析情感倾向）
# - extract_review_keywords()     评论关键词提取（调用 nlp/keyword_extract.py）
# - generate_wordcloud_data()     生成词云数据（关键词 + 频率，供前端渲染）
# 数据来源：restaurant_review 表
# 依赖：pandas, analysis/nlp 子模块
