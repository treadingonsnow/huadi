# 竞品分析模块
# 功能：
# - find_competitors()            识别竞品餐厅（同商圈 + 同菜系 + 相近价格区间）
# - compare_restaurants()         多维度对比（价格、评分、销量、评论数）
# - analyze_strengths_weaknesses() 优劣势分析（口味/环境/服务各维度评分对比）
# - calc_market_share()           市场份额分析（品牌/连锁店在区域内的占比）
# - generate_swot()               生成SWOT分析（基于评分、评论情感、价格、位置等综合判断）
# - analyze_competition_landscape() 区域竞争格局分析
# 数据来源：restaurant_info, restaurant_review, dish_info
# 依赖：pandas, numpy, analysis/nlp
