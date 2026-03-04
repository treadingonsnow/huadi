# 区域分析模块
# 功能：
# - calc_district_density()       各行政区餐厅密度分析（餐厅数量/面积）
# - calc_business_area_density()  各商圈餐厅数量分布统计
# - calc_area_cuisine_dist()      不同区域的菜系偏好分布（区域×菜系 交叉统计）
# - calc_area_price_level()       各区域人均消费水平分布
# - generate_heatmap_data()       生成热力图数据（经纬度 + 权重值，供前端ECharts渲染）
# - calc_subway_restaurant_dist() 地铁沿线餐厅分布分析
# 数据来源：restaurant_info 表
# 输出格式：适配前端 ECharts 的 JSON 数据结构
