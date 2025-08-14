# storybook_creator/pdf_assembler.py
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Image, PageBreak, Spacer, PageTemplate, Frame
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
        doc.pagesize[0] - inch * 0.5,
        0.5 * inch,
        f"Page {page_num}"
    )

def create_storybook_pdf(
    illustrated_scenes: list,
    output_path: str,
    font_name: str = "Helvetica",
    font_size: int = 14,
    story_title: str = "My Storybook",
    author: str = "Anonymous"
):
    """
    Assembles the text scenes and their corresponding images into a storybook PDF
    with improved layout and formatting.
    """
    logger.info(f"Assembling storybook PDF with {len(illustrated_scenes)} scenes.")
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=1 * inch,
        bottomMargin=0.75 * inch
    )
    story_flowables = []

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName=font_name,
        fontSize=font_size,
        leading=font_size * 1.5,
        spaceAfter=16
    )
    scene_title_style = ParagraphStyle(
        'SceneTitle',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=font_size + 4,
        textColor=colors.darkblue,
        spaceAfter=12
    )
    cover_title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Title'],
        fontName=font_name,
        fontSize=28,
        alignment=1,  # center
        textColor=colors.HexColor("#1f4e79"),
        spaceAfter=20
    )
    cover_author_style = ParagraphStyle(
        'CoverAuthor',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=16,
        alignment=1,  # center
        textColor=colors.grey
    )

    # Cover Page
    story_flowables.append(Spacer(1, 2 * inch))
    story_flowables.append(Paragraph(story_title, cover_title_style))
    story_flowables.append(Paragraph(f"by {author}", cover_author_style))
    story_flowables.append(PageBreak())

    # Scene pages
    for i, scene in enumerate(illustrated_scenes, start=1):
        scene_text = scene.get('text', '[No text for this scene]')
        scene_title = f"Scene {i}"
        story_flowables.append(Paragraph(scene_title, scene_title_style))
        story_flowables.append(Paragraph(scene_text, body_style))
        story_flowables.append(Spacer(1, 0.2 * inch))

        image_path = scene.get('image_path')
        if image_path and os.path.exists(image_path):
            try:
                logger.info(f"Adding image {image_path} for scene {i} to PDF.")
                img = Image(image_path, width=5.5 * inch, height=5.5 * inch, kind='proportional')
                img.hAlign = 'CENTER'
                story_flowables.append(img)
            except Exception as e:
                logger.warning(f"Could not add image from {image_path} for scene {i}. Error: {e}")
                story_flowables.append(Paragraph(f"[Image could not be loaded]", styles['Normal']))
        else:
            logger.warning(f"No image found for scene {i}. Adding placeholder text.")
            story_flowables.append(Paragraph(f"[Image missing]", styles['Normal']))

        story_flowables.append(PageBreak())

    try:
        logger.info(f"Building final PDF document at {output_path}.")
        doc.build(
            story_flowables,
            onFirstPage=_add_page_number,
            onLaterPages=_add_page_number
        )
        logger.info(f"Storybook PDF successfully created at {output_path}")
    except Exception as e:
        logger.critical(f"Error while building PDF: {e}", exc_info=True)
