# 报告生成 API 路由
# 功能：
# - POST /market          提交市场分析报告生成任务（指定区域、菜系、价格区间、时间范围）
#                          返回任务ID，后台异步生成（Celery任务）
# - POST /competitor       提交竞品分析报告生成任务（指定目标餐厅ID）
# - GET  /tasks            查询报告生成任务列表及状态
# - GET  /tasks/{task_id}  查询单个任务状态
# - GET  /download/{task_id}  下载已生成的报告（PDF/Word格式）
