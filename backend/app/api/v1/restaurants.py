# 餐厅相关 API 路由
# 功能：
# - GET  /search          多维度搜索（关键词、区域、商圈、菜系、价格区间、评分、场景）
#                          支持分页、排序（距离/评分/价格/热度）
# - GET  /{restaurant_id} 餐厅详情（基础信息、评分、菜品、评论列表）
# - GET  /{restaurant_id}/reviews  餐厅评论列表（分页、排序、筛选）
# - POST /favorites        收藏/取消收藏餐厅（需登录）
# - GET  /favorites        获取用户收藏列表（需登录）
