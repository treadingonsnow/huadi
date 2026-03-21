"""报告导出 API"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ...database import get_db
from ...response import error
from ...services.report_service import ReportService

router = APIRouter(prefix="/report", tags=["报告导出"])


@router.get("/generate")
def generate_report(db: Session = Depends(get_db)):
    """生成并下载 PDF 分析报告"""
    try:
        svc = ReportService(db)
        pdf_bytes = svc.generate_pdf()
    except Exception as exc:
        return error(message=f"报告生成失败：{exc}", code=500)

    from datetime import datetime
    filename = f"上海美食分析报告_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
