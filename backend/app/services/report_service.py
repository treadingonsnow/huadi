# 报告生成业务服务
# 功能：
# - create_market_report_task()      创建市场分析报告任务（写入任务表，提交Celery异步任务）
# - create_competitor_report_task()  创建竞品分析报告任务
# - generate_market_report()         Celery异步任务：聚合多源数据 → 执行分析 → 生成图表 → 输出PDF/Word
# - generate_competitor_report()     Celery异步任务：识别竞品 → 对比分析 → SWOT → 输出PDF/Word
# - get_task_status()                查询任务状态和进度
# - get_report_download_url()       获取报告下载链接
# 依赖：reportlab/python-docx 生成PDF/Word，matplotlib 生成图表
