import os
import re
import html
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as PlatypusImage,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.pdfgen import canvas
from story_generator import Storybook

class StorybookCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self.pages)
        for page_data in self.pages:
            self.__dict__.update(page_data)
            self.draw_page_decorations(total_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        if self._pageNumber == 1:
            self.saveState()
            self.setStrokeColor(colors.HexColor("#4A7C59"))
            self.setLineWidth(3)
            self.rect(20, 20, 792 - 40, 612 - 40, stroke=1, fill=0)
            self.setStrokeColor(colors.HexColor("#D8E2DC"))
            self.setLineWidth(1)
            self.rect(26, 26, 792 - 52, 612 - 52, stroke=1, fill=0)
            self.restoreState()
            return

        self.saveState()
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(1)
        self.line(36, 42, 792 - 36, 42)
        
        self.setFont("Helvetica-Bold", 9)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawString(36, 26, "MagicTale AI — Children's Storybook Creator")
        
        page_str = f"Page {self._pageNumber - 1} of {total_pages - 1}"
        self.drawRightString(792 - 36, 26, page_str)
        self.restoreState()

def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name)
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    return cleaned[:50] or "magictale_storybook"

def generate_pdf(
    storybook: Storybook,
    image_paths: List[str],
    output_directory: str
) -> str:
    os.makedirs(output_directory, exist_ok=True)
    file_base = sanitize_filename(storybook.title)
    pdf_filename = f"{file_base}.pdf"
    pdf_path = os.path.join(output_directory, pdf_filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    cover_title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=30,
        leading=36,
        textColor=colors.HexColor("#1A365D"),
        alignment=1,
        spaceAfter=12
    )

    cover_sub_style = ParagraphStyle(
        "CoverSub",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=15,
        leading=20,
        textColor=colors.HexColor("#4A5568"),
        alignment=1,
        spaceAfter=16
    )

    cover_meta_style = ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#718096"),
        alignment=1
    )

    stage_style = ParagraphStyle(
        "PageStage",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#2B6CB0"),
        spaceAfter=6,
        textTransform="uppercase"
    )

    page_title_style = ParagraphStyle(
        "PageTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=14
    )

    story_text_style = ParagraphStyle(
        "StoryText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=13.5,
        leading=22,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=14
    )

    char_badge_style = ParagraphStyle(
        "CharBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#718096")
    )

    elements = []

    elements.append(Spacer(1, 30))
    elements.append(Paragraph(html.escape(storybook.title), cover_title_style))
    elements.append(Paragraph(f"A Whimsical Tale of {html.escape(storybook.theme)}", cover_sub_style))
    elements.append(Spacer(1, 10))

    if image_paths and os.path.exists(image_paths[0]):
        cover_img = PlatypusImage(image_paths[0], width=280, height=280)
        img_table = Table([[cover_img]], colWidths=[720], hAlign="CENTER")
        img_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
        ]))
        elements.append(img_table)
    else:
        elements.append(Spacer(1, 260))

    elements.append(Spacer(1, 24))
    meta_text = (
        f"<b>Main Character:</b> {html.escape(storybook.character.name)} &bull; "
        f"<b>Target Age:</b> {html.escape(storybook.target_age)} &bull; "
        f"<b>Mode:</b> {html.escape(storybook.mode_label)}"
    )
    elements.append(Paragraph(meta_text, cover_meta_style))
    elements.append(PageBreak())

    for idx, page in enumerate(storybook.pages):
        img_flowable = None
        current_img_path = image_paths[idx] if idx < len(image_paths) else None

        if current_img_path and os.path.exists(current_img_path):
            img_flowable = PlatypusImage(current_img_path, width=350, height=350)
        else:
            placeholder_text = Paragraph(
                f"<para align=center><br/><br/><br/><br/><b>[ Illustration for Page {page.page_number} ]</b><br/>{html.escape(page.scene_description)}</para>",
                story_text_style
            )
            img_flowable = placeholder_text

        text_cell_contents = [
            Spacer(1, 10),
            Paragraph(f"STAGE: {html.escape(page.stage)}", stage_style),
            Paragraph(html.escape(page.title), page_title_style),
            Spacer(1, 10),
            Paragraph(html.escape(page.text), story_text_style),
            Spacer(1, 16),
            Paragraph(f"<b>Key Scene:</b> <i>{html.escape(page.scene_description[:160])}...</i>", char_badge_style)
        ]

        spread_table = Table(
            [[img_flowable, text_cell_contents]],
            colWidths=[360, 360],
            hAlign="CENTER"
        )
        spread_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 15),
            ("LEFTPADDING", (1, 0), (1, 0), 15),
            ("RIGHTPADDING", (1, 0), (1, 0), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))

        elements.append(spread_table)
        if idx < len(storybook.pages) - 1:
            elements.append(PageBreak())

    doc.build(elements, canvasmaker=StorybookCanvas)
    return pdf_path
