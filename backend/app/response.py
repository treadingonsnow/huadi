# 统一响应格式
# 功能：
# - 所有接口统一返回格式：{"code": xxx, "message": "xxx", "data": ...}
# - 成功响应：success()
# - 错误响应：error()

from fastapi.responses import JSONResponse
from typing import Any, Optional


def success(data: Any = None, message: str = "success", code: int = 200) -> dict:
    """
    统一成功响应

    参数:
        data: 返回数据
        message: 成功消息
        code: 状态码

    返回:
        {"code": 200, "message": "success", "data": ...}
    """
    return {
        "code": code,
        "message": message,
        "data": data
    }


def error(message: str = "error", code: int = 400, data: Any = None) -> JSONResponse:
    """
    统一错误响应

    参数:
        message: 错误消息
        code: 状态码
        data: 返回数据（通常为 None）

    返回:
        JSONResponse({"code": 400, "message": "error", "data": None})
    """
    return JSONResponse(
        status_code=code,
        content={
            "code": code,
            "message": message,
            "data": data
        }
    )
