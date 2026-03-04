# 价格分析模块
# 功能：
# - calc_price_distribution()     价格区间分布统计（经济型/中档/中高档/高档）
# - calc_cuisine_price_compare()  不同菜系平均消费水平对比
# - calc_price_trend()            餐饮价格时间变化趋势（按月/季度聚合）
# - calc_cost_performance_rank()  性价比排行（性价比指数 = (评分/5) / (人均/100)）
# - detect_price_anomaly()        价格异常检测（识别价格异常偏高/偏低的餐厅）
# 数据来源：restaurant_info 表、restaurant_review 表
# 依赖：pandas, numpy
