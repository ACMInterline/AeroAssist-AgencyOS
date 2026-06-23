from dataclasses import dataclass
from html.parser import HTMLParser
from io import BytesIO
from typing import Any


@dataclass
class PdfRenderResult:
    ok: bool
    data: bytes | None = None
    engine_name: str = "reportlab"
    engine_version: str | None = None
    diagnostic: str | None = None


def pdf_capabilities() -> dict[str, Any]:
    try:
        import reportlab

        return {
            "available": True,
            "engine": "reportlab",
            "engine_version": getattr(reportlab, "Version", None),
            "diagnostic": "ReportLab simplified snapshot PDF renderer is available. Output is not pixel-perfect HTML rendering.",
        }
    except Exception as exc:
        return {
            "available": False,
            "engine": "reportlab",
            "engine_version": None,
            "diagnostic": f"ReportLab PDF renderer is unavailable: {exc}",
        }


class SnapshotHtmlParser(HTMLParser):
    BLOCK_TAGS = {"p", "div", "section", "article", "header", "footer", "tr", "li", "h1", "h2", "h3", "h4", "table"}
    SKIP_TAGS = {"script", "style", "iframe", "object", "embed", "img", "link", "meta"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in {"br", "td", "th"}:
            self.parts.append(" ")
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            clean = " ".join(data.split())
            if clean:
                self.parts.append(clean)

    def paragraphs(self) -> list[str]:
        text = "".join(self.parts)
        paragraphs = []
        for raw in text.splitlines():
            clean = " ".join(raw.split())
            if clean:
                paragraphs.append(clean)
        return paragraphs


def html_to_paragraphs(rendered_html: str) -> list[str]:
    parser = SnapshotHtmlParser()
    parser.feed(rendered_html or "")
    paragraphs = parser.paragraphs()
    return paragraphs or ["No printable content was available in this stored document snapshot."]


def render_pdf_from_html(rendered_html: str, title: str, agency_id: str, document_id: str) -> PdfRenderResult:
    caps = pdf_capabilities()
    if not caps["available"]:
        return PdfRenderResult(ok=False, engine_name="reportlab", diagnostic=caps["diagnostic"])

    try:
        import reportlab
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        from xml.sax.saxutils import escape
    except Exception as exc:
        return PdfRenderResult(ok=False, engine_name="reportlab", diagnostic=f"ReportLab PDF renderer is unavailable: {exc}")

    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=title,
            author="AeroAssist AgencyOS",
            subject="Agency-generated snapshot document",
        )
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        title_style.textColor = colors.HexColor("#0f172a")
        normal = styles["BodyText"]
        normal.fontName = "Helvetica"
        normal.fontSize = 9.5
        normal.leading = 13

        story = [
            Paragraph(escape(title or "Agency-generated snapshot document"), title_style),
            Spacer(1, 6),
            Paragraph("Agency-generated snapshot document. Simplified PDF export from stored rendered HTML.", styles["Italic"]),
            Paragraph(f"Agency: {escape(agency_id)}", styles["Italic"]),
            Paragraph(f"Rendered document: {escape(document_id)}", styles["Italic"]),
            Spacer(1, 10),
        ]
        for paragraph in html_to_paragraphs(rendered_html):
            story.append(Paragraph(escape(paragraph), normal))
            story.append(Spacer(1, 5))

        doc.build(story)
        data = buffer.getvalue()
        if not data.startswith(b"%PDF"):
            return PdfRenderResult(ok=False, engine_name="reportlab", engine_version=getattr(reportlab, "Version", None), diagnostic="ReportLab did not return valid PDF bytes.")
        return PdfRenderResult(ok=True, data=data, engine_name="reportlab", engine_version=getattr(reportlab, "Version", None), diagnostic="Generated simplified snapshot PDF with ReportLab.")
    except Exception as exc:
        return PdfRenderResult(ok=False, engine_name="reportlab", engine_version=getattr(reportlab, "Version", None), diagnostic=f"PDF rendering failed: {exc}")
