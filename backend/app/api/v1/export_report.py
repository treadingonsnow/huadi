"""报告导出 API"""
from __future__ import annotations

from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ...database import get_db
from ...response import error
from ...services.report_service import ReportService

router = APIRouter(prefix="/report", tags=["报告导出"])


@router.get("/generate")
def generate_report(db: Session = Depends(get_db)):
    """生成并下载 PDF 分析报告（matplotlib 图表 + reportlab 排版）"""
    try:
        svc = ReportService(db)
        pdf_bytes = svc.generate_pdf()
    except Exception as exc:
        return error(message=f"报告生成失败：{exc}", code=500)

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    cn_name = f"上海美食分析报告_{ts}.pdf"
    # RFC 5987 编码，兼容所有现代浏览器
    encoded_name = quote(cn_name, safe="")
    disposition = (
        f'attachment; filename="report_{ts}.pdf"; '
        f"filename*=UTF-8''{encoded_name}"
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": disposition},
    )

