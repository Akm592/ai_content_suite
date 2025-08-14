from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Image, PageBreak, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors
import os
import logging

logger = logging.getLogger(__name__)

def _add_page_number(canvas: Canvas, doc):
    page_num = canvas.getPageNumber()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(
        doc.pagesize[0] - inch * 0.4,
        0.4 * inch,
        f"{page_num}"
    )

def create_storybook_pdf(
    illustrated_scenes: list,
    output_path: str,
    font_name: str = "Helvetica",
    font_size: int = 16,
    story_title: str = "My Storybook",
    author: str = "Anonymous"
):
    """
    Creates a picture book style PDF:
    - Cover page
    - Each scene: left page with text, right page with large image
    - Minimal margins for more immersive visuals
    """
    logger.info(f"Assembling storybook PDF with {len(illustrated_scenes)} scenes.")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.5 * inch
    )
    story_flowables = []

    styles = getSampleStyleSheet()

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName=font_name,
        fontSize=font_size,
        leading=font_size * 1.4,
        spaceAfter=14
    )
    scene_title_style = ParagraphStyle(
        'SceneTitle',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=font_size + 4,
        textColor=colors.darkblue,
        spaceAfter=10
    )
    cover_title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Title'],
        fontName=font_name,
        fontSize=32,
        alignment=1,  # center
        textColor=colors.HexColor("#1f4e79"),
        spaceAfter=20
    )
    cover_author_style = ParagraphStyle(
        'CoverAuthor',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=18,
        alignment=1,  # center
        textColor=colors.grey
    )

    # --- Cover Page ---
    story_flowables.append(Spacer(1, 3 * inch))
    story_flowables.append(Paragraph(story_title, cover_title_style))
    story_flowables.append(Paragraph(f"by {author}", cover_author_style))
    story_flowables.append(PageBreak())

    # --- Scene Pages ---
    for i, scene in enumerate(illustrated_scenes, start=1):
        scene_text = scene.get('text', '[No text for this scene]')
        image_path = scene.get('image_path')

        # Text page (left)
        story_flowables.append(Paragraph(f"Scene {i}", scene_title_style))
        story_flowables.append(Paragraph(scene_text, body_style))
        story_flowables.append(PageBreak())

        # Image page (right)
        if image_path and os.path.exists(image_path):
            try:
                logger.info(f"Adding image {image_path} for scene {i}.")
                img = Image(image_path, width=7.5 * inch, height=9.5 * inch, kind='proportional')
                img.hAlign = 'CENTER'
                story_flowables.append(img)
            except Exception as e:
                logger.warning(f"Could not add image from {image_path}: {e}")
                story_flowables.append(Paragraph("[Image could not be loaded]", styles['Normal']))
        else:
            logger.warning(f"No image found for scene {i}")
            story_flowables.append(Paragraph("[Image missing]", styles['Normal']))

        story_flowables.append(PageBreak())

    try:
        doc.build(
            story_flowables,
            onFirstPage=_add_page_number,
            onLaterPages=_add_page_number
        )
        logger.info(f"Storybook PDF created at {output_path}")
    except Exception as e:
        logger.critical(f"Error while building PDF: {e}", exc_info=True)
