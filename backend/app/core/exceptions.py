# 全局异常处理
# 功能：
# - 定义业务异常类：NotFoundException, UnauthorizedException, ForbiddenException, ValidationException
# - 注册 FastAPI 异常处理器，统一返回格式：{"code": xxx, "message": "...", "data": null}
# - 捕获未处理异常，记录日志并返回500
