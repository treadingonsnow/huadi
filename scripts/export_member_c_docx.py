from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


SOURCE_MD = Path("docs/成员C-测试用例及运行结果.md")
TARGET_DOCX = Path("docs/成员C-测试用例及运行结果.docx")


def p(text: str, bold: bool = False, size: int | None = None) -> str:
    content = escape(text)
    run_prop = ""
    if bold or size:
        props = []
        if bold:
            props.append("<w:b/>")
        if size:
            props.append(f'<w:sz w:val="{size}"/>')
            props.append(f'<w:szCs w:val="{size}"/>')
        run_prop = f"<w:rPr>{''.join(props)}</w:rPr>"
    if not text:
        return "<w:p/>"
    return f"<w:p><w:r>{run_prop}<w:t xml:space=\"preserve\">{content}</w:t></w:r></w:p>"


def table(rows: list[list[str]]) -> str:
    tbl_rows = []
    for row in rows:
        cells = []
        for cell in row:
            text = escape(cell.strip())
            cells.append(
                "<w:tc>"
                "<w:tcPr><w:tcW w:w=\"2400\" w:type=\"dxa\"/></w:tcPr>"
                f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"
                "</w:tc>"
            )
        tbl_rows.append(f"<w:tr>{''.join(cells)}</w:tr>")
    return (
        "<w:tbl>"
        "<w:tblPr>"
        "<w:tblW w:w=\"0\" w:type=\"auto\"/>"
        "<w:tblBorders>"
        "<w:top w:val=\"single\" w:sz=\"8\" w:space=\"0\" w:color=\"auto\"/>"
        "<w:left w:val=\"single\" w:sz=\"8\" w:space=\"0\" w:color=\"auto\"/>"
        "<w:bottom w:val=\"single\" w:sz=\"8\" w:space=\"0\" w:color=\"auto\"/>"
        "<w:right w:val=\"single\" w:sz=\"8\" w:space=\"0\" w:color=\"auto\"/>"
        "<w:insideH w:val=\"single\" w:sz=\"8\" w:space=\"0\" w:color=\"auto\"/>"
        "<w:insideV w:val=\"single\" w:sz=\"8\" w:space=\"0\" w:color=\"auto\"/>"
        "</w:tblBorders>"
        "</w:tblPr>"
        "<w:tblGrid>"
        "<w:gridCol w:w=\"1800\"/><w:gridCol w:w=\"4200\"/><w:gridCol w:w=\"1800\"/><w:gridCol w:w=\"4200\"/>"
        "</w:tblGrid>"
        f"{''.join(tbl_rows)}"
        "</w:tbl>"
    )


def parse_markdown(md_text: str) -> list[str]:
    blocks: list[str] = []
    lines = md_text.splitlines()
    i = 0
    in_code = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            i += 1
            continue
        if in_code:
            blocks.append(p(line))
            i += 1
            continue
        if stripped.startswith("### "):
            blocks.append(p(stripped[4:], bold=True, size=24))
            i += 1
            continue
        if stripped.startswith("## "):
            blocks.append(p(stripped[3:], bold=True, size=28))
            i += 1
            continue
        if stripped.startswith("# "):
            blocks.append(p(stripped[2:], bold=True, size=32))
            i += 1
            continue
        if stripped.startswith("- "):
            blocks.append(p(f"• {stripped[2:]}"))
            i += 1
            continue
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows: list[list[str]] = []
            for idx, table_line in enumerate(table_lines):
                parts = [part.strip() for part in table_line.split("|")[1:-1]]
                if idx == 1 and all(set(part) <= {"-"} for part in parts):
                    continue
                rows.append(parts)
            if rows:
                blocks.append(table(rows))
            continue
        if not stripped:
            blocks.append("<w:p/>")
            i += 1
            continue
        blocks.append(p(line))
        i += 1
    return blocks


def build_document_xml(body_blocks: list[str]) -> str:
    body = "".join(body_blocks)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document xmlns:wpc=\"http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas\" "
        "xmlns:mc=\"http://schemas.openxmlformats.org/markup-compatibility/2006\" "
        "xmlns:o=\"urn:schemas-microsoft-com:office:office\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" "
        "xmlns:m=\"http://schemas.openxmlformats.org/officeDocument/2006/math\" "
        "xmlns:v=\"urn:schemas-microsoft-com:vml\" "
        "xmlns:wp14=\"http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing\" "
        "xmlns:wp=\"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing\" "
        "xmlns:w10=\"urn:schemas-microsoft-com:office:word\" "
        "xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\" "
        "xmlns:w14=\"http://schemas.microsoft.com/office/word/2010/wordml\" "
        "xmlns:w15=\"http://schemas.microsoft.com/office/word/2012/wordml\" "
        "xmlns:w16cex=\"http://schemas.microsoft.com/office/word/2018/wordml/cex\" "
        "xmlns:w16cid=\"http://schemas.microsoft.com/office/word/2016/wordml/cid\" "
        "xmlns:w16=\"http://schemas.microsoft.com/office/word/2018/wordml\" "
        "xmlns:w16du=\"http://schemas.microsoft.com/office/word/2023/wordml/word16du\" "
        "xmlns:w16sdtdh=\"http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash\" "
        "xmlns:w16sdtfl=\"http://schemas.microsoft.com/office/word/2024/wordml/sdtformatlock\" "
        "xmlns:w16se=\"http://schemas.microsoft.com/office/word/2015/wordml/symex\" "
        "xmlns:wpg=\"http://schemas.microsoft.com/office/word/2010/wordprocessingGroup\" "
        "xmlns:wpi=\"http://schemas.microsoft.com/office/word/2010/wordprocessingInk\" "
        "xmlns:wne=\"http://schemas.microsoft.com/office/word/2006/wordml\" "
        "xmlns:wps=\"http://schemas.microsoft.com/office/word/2010/wordprocessingShape\" mc:Ignorable=\"w14 w15 w16se w16cid w16 w16cex w16sdtdh w16sdtfl w16du wp14\">"
        "<w:body>"
        f"{body}"
        "<w:sectPr>"
        "<w:pgSz w:w=\"11906\" w:h=\"16838\"/>"
        "<w:pgMar w:top=\"1440\" w:right=\"1440\" w:bottom=\"1440\" w:left=\"1440\" w:header=\"708\" w:footer=\"708\" w:gutter=\"0\"/>"
        "<w:cols w:space=\"708\"/>"
        "<w:docGrid w:linePitch=\"360\"/>"
        "</w:sectPr>"
        "</w:body>"
        "</w:document>"
    )


def write_docx(document_xml: str, target: Path) -> None:
    content_types = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
        "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
        "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
        "<Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>"
        "</Types>"
    )
    rels = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/>"
        "</Relationships>"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document_xml)


def main() -> None:
    markdown = SOURCE_MD.read_text(encoding="utf-8")
    blocks = parse_markdown(markdown)
    document_xml = build_document_xml(blocks)
    write_docx(document_xml, TARGET_DOCX)
    print(TARGET_DOCX.as_posix())


if __name__ == "__main__":
    main()
