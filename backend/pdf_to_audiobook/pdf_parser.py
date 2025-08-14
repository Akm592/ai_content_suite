# pdf_to_audiobook/pdf_parser.py

import pymupdf4llm
import re
import logging

logger = logging.getLogger(__name__)

def extract_text_advanced(pdf_path: str) -> str:
    """
    Extracts text from a PDF using pymupdf4llm to handle complex multi-column layouts.
    This is the most reliable method for preserving reading order from complex documents.
    
    Args:
        pdf_path: The file path to the PDF document.

    Returns:
        A string containing the document's content in Markdown format.
    """
    try:
        # pymupdf4llm.to_markdown() is a powerful function that intelligently
        # processes the PDF layout to produce a clean, linear output.
        logger.info(f"Extracting text from {pdf_path} using pymupdf4llm.")
        md_text = pymupdf4llm.to_markdown(pdf_path)
        return md_text
    except Exception as e:
        logger.exception(f"Error processing PDF {pdf_path} with pymupdf4llm: {e}")
        return ""

def sanitize_text_for_tts(text: str) -> str:
    """
    Cleans extracted text to make it suitable for Text-to-Speech conversion.
    This removes formatting and artifacts that would sound unnatural if read aloud.
    
    Args:
        text: The raw text string extracted from the PDF.

    Returns:
        A cleaned string ready for the TTS engine.
    """
    # Remove Markdown headers (e.g., #, ##, ###)
    text = re.sub(r'#+\s', '', text)
    
    # Remove Markdown-style links but keep the link text
    text = re.sub(r'\[(.*?)\]\(.*\)', r'\1', text)
    
    # Remove Markdown formatting for bold/italic (*, **, _, __, `)
    text = re.sub(r'(\*\*|\*|__|`)', '', text)
    
    # Re-join words that were hyphenated across line breaks
    text = re.sub(r'-\n', '', text)

    # Replace newline characters with a space to ensure smooth sentence flow
    text = text.replace('\n', ' ')

    # Remove common PDF artifacts like page numbers (case-insensitive)
    text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
    
    # Remove any URLs
    text = re.sub(r'http\S+', '', text)

    # Collapse multiple whitespace characters into a single space
    text = re.sub(r'\s+', ' ', text).strip()

    return text
