"""数据导入 API"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from ...database import get_db
from ...response import success, error
from ...services.import_service import ImportService

router = APIRouter(prefix="/import", tags=["数据导入"])


@router.post("/upload")
async def upload_and_import(
    file: UploadFile = File(..., description="CSV / JSON / Excel 文件"),
    destination: str = Form("mysql", description="目标存储：mysql / hdfs / hive"),
    task_name: str = Form("", description="任务名称（为空时自动生成）"),
    hdfs_host: str = Form("", description="HDFS 主机（destination=hdfs/hive 时必填）"),
    hdfs_port: int = Form(9870, description="HDFS WebHDFS 端口"),
    hdfs_path: str = Form("/user/hadoop/restaurant", description="HDFS 目标目录"),
    hdfs_user: str = Form("hadoop", description="HDFS 用户名"),
    hive_host: str = Form("localhost", description="HiveServer2 主机"),
    hive_port: int = Form(10000, description="HiveServer2 端口"),
    hive_db: str = Form("default", description="Hive 数据库"),
    hive_table: str = Form("restaurant_info", description="Hive 表名"),
    db: Session = Depends(get_db),
):
    """上传文件并导入到指定存储目标"""
    if not task_name:
        from datetime import datetime
        task_name = f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    allowed_types = {"text/csv", "application/json",
                     "application/vnd.ms-excel",
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    filename = file.filename or "upload.csv"

    file_bytes = await file.read()
    svc = ImportService(db)

    try:
        if destination == "mysql":
            result = svc.import_to_mysql(file_bytes, filename, task_name)
        elif destination == "hdfs":
            if not hdfs_host:
                return error(message="destination=hdfs 时必须填写 hdfs_host", code=400)
            result = svc.import_to_hdfs(
                file_bytes, filename, task_name,
                hdfs_host, hdfs_port, hdfs_path, hdfs_user,
            )
        elif destination == "hive":
            if not hdfs_host:
                return error(message="destination=hive 时必须填写 hdfs_host", code=400)
            result = svc.import_to_hive(
                file_bytes, filename, task_name,
                hdfs_host, hdfs_port, hdfs_path, hdfs_user,
                hive_host, hive_port, hive_db, hive_table,
            )
        else:
            return error(message=f"不支持的目标存储：{destination}，可选 mysql/hdfs/hive", code=400)
    except ValueError as exc:
        return error(message=str(exc), code=422)
    except Exception as exc:
        return error(message=f"导入失败：{exc}", code=500)

    return success(data={**result, "task_name": task_name})
