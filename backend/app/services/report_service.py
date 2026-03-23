"""报告生成服务
使用 matplotlib 生成图表 + reportlab 组合成 PDF
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    HRFlowable, Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from sqlalchemy import text
from sqlalchemy.orm import Session

# 注册 reportlab 内置中文 CID 字体
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

# matplotlib 尝试使用中文字体
rcParams["font.sans-serif"] = [
    "WenQuanYi Micro Hei", "SimHei", "Microsoft YaHei", "Noto Sans CJK SC", "DejaVu Sans",
]
rcParams["axes.unicode_minus"] = False

BRAND_RED = colors.HexColor("#e63946")
BRAND_GOLD = colors.HexColor("#ffd700")


def _cn_style(name: str, **kwargs) -> ParagraphStyle:
    return ParagraphStyle(name, fontName="STSong-Light", **kwargs)


def _fig_to_image(fig: plt.Figure, width: float = 14 * cm) -> Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    img = Image(buf)
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = width
    img.drawHeight = width * ratio
    return img


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_analysis_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {}

        row = self.db.execute(
            text("""
                SELECT COUNT(*) AS total_count,
                       COALESCE(ROUND(AVG(NULLIF(rating_overall,0)),2),0) AS avg_rating,
                       COALESCE(ROUND(AVG(NULLIF(avg_price,0)),2),0) AS avg_price,
                       COUNT(DISTINCT district) AS district_count
                FROM restaurant_info
            """)
        ).mappings().one()
        data["overview"] = dict(row)

        rows = self.db.execute(
            text("""
                SELECT district AS name, COUNT(*) AS cnt
                FROM restaurant_info
                WHERE district IS NOT NULL AND district != ''
                GROUP BY district ORDER BY cnt DESC
            """)
        ).mappings().all()
        data["area"] = [dict(r) for r in rows]

        rows = self.db.execute(
            text("""
                SELECT cuisine_type AS name, COUNT(*) AS cnt
                FROM restaurant_info
                WHERE cuisine_type IS NOT NULL AND cuisine_type != ''
                GROUP BY cuisine_type ORDER BY cnt DESC LIMIT 12
            """)
        ).mappings().all()
        data["cuisine"] = [dict(r) for r in rows]

        data["price"] = []
        for label, lo, hi in [
            ("50元以下", 0, 50), ("51-100元", 50, 100),
            ("101-200元", 100, 200), ("200元以上", 200, None),
        ]:
            if hi is None:
                cnt = self.db.execute(
                    text("SELECT COUNT(*) FROM restaurant_info WHERE avg_price > :lo"),
                    {"lo": lo},
                ).scalar_one()
            else:
                cnt = self.db.execute(
                    text("SELECT COUNT(*) FROM restaurant_info WHERE avg_price > :lo AND avg_price <= :hi"),
                    {"lo": lo, "hi": hi},
                ).scalar_one()
            data["price"].append({"label": label, "count": int(cnt)})

        data["rating"] = []
        for label, lo, hi in [
            ("3.0分以下", 0, 3.0), ("3.0-3.9分", 3.0, 4.0),
            ("4.0-4.4分", 4.0, 4.5), ("4.5-5.0分", 4.5, 5.0),
        ]:
            cnt = self.db.execute(
                text("SELECT COUNT(*) FROM restaurant_info WHERE rating_overall >= :lo AND rating_overall < :hi"),
                {"lo": lo, "hi": hi},
            ).scalar_one()
            data["rating"].append({"range": label, "count": int(cnt)})

        rows = self.db.execute(
            text("""
                SELECT district AS name, ROUND(AVG(avg_price),1) AS avg_p
                FROM restaurant_info
                WHERE district IS NOT NULL AND avg_price > 0
                GROUP BY district ORDER BY avg_p DESC
            """)
        ).mappings().all()
        data["area_price"] = [dict(r) for r in rows]

        return data

    def _chart_area(self, area: list[dict]) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(10, 4))
        names = [d["name"] for d in area]
        counts = [d["cnt"] for d in area]
        bars = ax.bar(names, counts, color="#e63946", edgecolor="none")
        ax.set_title("各区餐厅数量分布", fontsize=13)
        ax.set_xlabel("行政区")
        ax.set_ylabel("餐厅数量（家）")
        plt.xticks(rotation=45, ha="right")
        for bar, v in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    str(v), ha="center", va="bottom", fontsize=8)
        fig.tight_layout()
        return fig

    def _chart_cuisine(self, cuisine: list[dict]) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(7, 6))
        labels = [d["name"] for d in cuisine]
        values = [d["cnt"] for d in cuisine]
        cmap = plt.get_cmap("tab20")
        ax.pie(values, labels=labels, autopct="%1.1f%%",
               colors=[cmap(i / len(labels)) for i in range(len(labels))],
               startangle=90, pctdistance=0.8)
        ax.set_title("菜系分布（Top 12）", fontsize=13)
        fig.tight_layout()
        return fig

    def _chart_price(self, price: list[dict]) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(7, 4))
        labels = [d["label"] for d in price]
        counts = [d["count"] for d in price]
        ax.bar(labels, counts, color="#ffd700", edgecolor="none")
        ax.set_title("人均消费区间分布", fontsize=13)
        ax.set_ylabel("餐厅数量（家）")
        fig.tight_layout()
        return fig

    def _chart_rating(self, rating: list[dict]) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(7, 4))
        labels = [d["range"] for d in rating]
        counts = [d["count"] for d in rating]
        ax.bar(labels, counts, color="#06d6a0", edgecolor="none")
        ax.set_title("评分分布", fontsize=13)
        ax.set_ylabel("餐厅数量（家）")
        fig.tight_layout()
        return fig

    def _chart_area_price(self, area_price: list[dict]) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(10, 5))
        names = [d["name"] for d in area_price]
        prices = [float(d["avg_p"]) for d in area_price]
        ax.barh(names[::-1], prices[::-1], color="#118ab2", edgecolor="none")
        ax.set_title("各区人均消费对比", fontsize=13)
        ax.set_xlabel("人均消费（元）")
        fig.tight_layout()
        return fig

    def generate_pdf(self) -> bytes:
        data = self._get_analysis_data()
        ov = data["overview"]

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm,
        )

        title_style = _cn_style("Title", fontSize=22, textColor=BRAND_RED,
                                alignment=TA_CENTER, spaceAfter=6)
        h1_style = _cn_style("H1", fontSize=14, textColor=BRAND_RED,
                              spaceBefore=14, spaceAfter=6, leading=20)
        h2_style = _cn_style("H2", fontSize=11, spaceBefore=8, spaceAfter=4)
        body_style = _cn_style("Body", fontSize=10, leading=18, spaceAfter=6)
        caption_style = _cn_style("Caption", fontSize=9, textColor=colors.HexColor("#555555"),
                                   alignment=TA_CENTER, spaceAfter=10)

        story: list = []

        # 封面
        story.append(Spacer(1, 3 * cm))
        story.append(Paragraph("上海美食大数据分析报告", title_style))
        story.append(Paragraph(
            "Shanghai Food Big Data Analysis Report",
            _cn_style("Sub", fontSize=13, textColor=BRAND_GOLD, alignment=TA_CENTER, spaceAfter=4)
        ))
        story.append(Spacer(1, 0.5 * cm))
        story.append(HRFlowable(width="100%", thickness=1, color=BRAND_RED))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}　　数据来源：美团",
            _cn_style("Meta", fontSize=10, textColor=colors.grey, alignment=TA_CENTER)
        ))
        story.append(PageBreak())

        # 一、数据概览
        story.append(Paragraph("一、数据概览", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 0.3 * cm))

        tbl_data = [
            ["指标", "数值"],
            ["餐厅总数", f"{int(ov['total_count']):,} 家"],
            ["平均评分", f"{ov['avg_rating']} 分"],
            ["人均消费", f"¥{ov['avg_price']}"],
            ["覆盖行政区", f"{ov['district_count']} 个"],
        ]
        tbl = Table(tbl_data, colWidths=[6 * cm, 8 * cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_RED),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(
            f"本平台共收录上海地区餐厅 {int(ov['total_count']):,} 家，"
            f"覆盖 {ov['district_count']} 个行政区，"
            f"整体平均评分 {ov['avg_rating']} 分，人均消费约 ¥{ov['avg_price']}。",
            body_style
        ))

        # 二、区域分布
        if data["area"]:
            story.append(Paragraph("二、上海各区餐厅分布", h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
            story.append(Spacer(1, 0.3 * cm))
            story.append(_fig_to_image(self._chart_area(data["area"])))
            story.append(Paragraph("图1　上海各区餐厅数量分布柱状图", caption_style))
            top3 = data["area"][:3]
            story.append(Paragraph(
                "餐厅数量最多的三个区依次为：" +
                "、".join(f"{d['name']}（{d['cnt']}家）" for d in top3) + "。"
                "浦东新区面积最大且商业发达，餐厅总量居首；"
                "黄浦、静安作为核心商务区，餐饮密度高。",
                body_style
            ))

        # 三、菜系分布
        if data["cuisine"]:
            story.append(Paragraph("三、菜系分布分析", h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
            story.append(Spacer(1, 0.3 * cm))
            story.append(_fig_to_image(self._chart_cuisine(data["cuisine"]), width=12 * cm))
            story.append(Paragraph("图2　菜系分布饼图（Top 12）", caption_style))
            top1 = data["cuisine"][0]
            story.append(Paragraph(
                f"上海餐饮菜系多元，其中 {top1['name']} 餐厅最多（{top1['cnt']} 家）。"
                "本帮菜、川菜、日料、火锅等传统热门菜系占主导地位。",
                body_style
            ))

        # 四、价格分布
        story.append(Paragraph("四、人均消费区间分布", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 0.3 * cm))
        if any(d["count"] > 0 for d in data["price"]):
            story.append(_fig_to_image(self._chart_price(data["price"])))
            story.append(Paragraph("图3　人均消费区间分布柱状图", caption_style))
        story.append(Paragraph(
            "上海餐厅人均消费主要集中在 50-200 元区间。"
            "中档餐厅数量最多，体现了消费者对性价比的关注。"
            "高端餐厅主要集中在黄浦、静安等核心商圈。",
            body_style
        ))

        # 五、评分分布
        story.append(Paragraph("五、餐厅评分分布", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 0.3 * cm))
        if any(d["count"] > 0 for d in data["rating"]):
            story.append(_fig_to_image(self._chart_rating(data["rating"])))
            story.append(Paragraph("图4　餐厅评分分布柱状图", caption_style))
        story.append(Paragraph(
            "上海餐厅整体评分较高，4.0 分以上占主体，"
            "说明上海餐饮市场服务和品质整体处于较高水平。",
            body_style
        ))

        # 六、区域均价
        if data["area_price"]:
            story.append(Paragraph("六、各区人均消费对比", h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
            story.append(Spacer(1, 0.3 * cm))
            story.append(_fig_to_image(self._chart_area_price(data["area_price"])))
            story.append(Paragraph("图5　各区人均消费横向对比图", caption_style))
            top1_p = data["area_price"][0]
            bot1_p = data["area_price"][-1]
            story.append(Paragraph(
                f"各区人均消费差异明显：{top1_p['name']} 最高（¥{top1_p['avg_p']}），"
                f"{bot1_p['name']} 最低（¥{bot1_p['avg_p']}）。"
                "核心商务区消费水平远高于郊区。",
                body_style
            ))

        # 结语
        story.append(Spacer(1, 1 * cm))
        story.append(HRFlowable(width="100%", thickness=1, color=BRAND_RED))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("结语", h2_style))
        story.append(Paragraph(
            "本报告基于平台采集的上海美食数据，从区域分布、菜系结构、消费水平、评分质量等维度进行分析，"
            "为消费者和餐饮从业者提供数据驱动的参考依据。",
            body_style
        ))

        doc.build(story)
        buf.seek(0)
        return buf.getvalue()
