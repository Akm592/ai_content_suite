# pdf_to_audiobook/pdf_parser.py

import pymupdf4llm
import re
import logging
from .token_counter import count_tokens_streaming, count_tokens, DEFAULT_MODEL

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
    Cleans extracted text to make it suitable for Text-to-Speech conversion and general LLM processing.
    This removes formatting and artifacts that would sound unnatural if read aloud or confuse an LLM.
    
    Args:
        text: The raw text string extracted from the PDF.

    Returns:
        A cleaned string ready for the TTS engine and LLM.
    """
    # 1. Remove Markdown headers (e.g., #, ##, ###)
    text = re.sub(r'#+\s', '', text)
    
    # 2. Remove Markdown-style links but keep the link text
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    
    # 3. Remove Markdown formatting for bold/italic (*, **, _, __, `)
    text = re.sub(r'(\*\*|\*|_|__|`)', '', text)
    
    # 4. More robust hyphenation handling:
    #    a. Remove hyphens at the end of lines, followed by a newline and a lowercase letter (common for hyphenated words)
    text = re.sub(r'(-\s*\n\s*)([a-z])', r'\2', text)
    #    b. Remove hyphens at the end of lines, followed by a newline (general case)
    text = re.sub(r'-\s*\n', '', text)

    # 5. Replace all newline characters with a space to ensure smooth sentence flow
    #    This is a crucial step for story continuity.
    text = text.replace('\n', ' ')

    # 6. Remove common PDF artifacts like page numbers (case-insensitive)
    text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\b', '', text) # Remove isolated numbers (potential page numbers)
    
    # 7. Remove any URLs
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)

    # 8. Normalize spacing around punctuation (e.g., "word ." -> "word.")
    text = re.sub(r'\s*([.,!?;:])\s*', r'\1 ', text)

    # 9. Remove lines that are mostly numbers or symbols (e.g., table of contents artifacts)
    #    This is a more aggressive filter for non-narrative content.
    #    First, split the text into potential "lines" or "sentences" based on common delimiters.
    #    Then, filter out lines that are primarily non-alphanumeric or very short and empty of letters.
    temp_lines = re.split(r'\s*[.!?]\s*', text) # Split by sentence-ending punctuation
    cleaned_temp_lines = []
    for line in temp_lines:
        line = line.strip()
        if not line:
            continue
        
        alpha_chars = sum(c.isalpha() for c in line)
        total_chars = len(line.replace(' ', '')) # Count non-space characters
        
        # Heuristic: If a line has less than 50% alphabetic characters (excluding spaces)
        # OR is very short (e.g., < 10 chars) and has no alphabetic characters,
        # it's likely an.artifact.
        if total_chars > 0 and (alpha_chars / total_chars < 0.5 or (total_chars < 10 and alpha_chars == 0)):
            logger.debug(f"Skipping potential artifact line: {line[:50]}...")
            continue
        cleaned_temp_lines.append(line)
    text = '. '.join(cleaned_temp_lines) + ('.' if cleaned_temp_lines and not text.endswith('.') else '') # Rejoin, add period if needed

    # 10. Collapse multiple whitespace characters into a single space
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def extract_text_and_count(pdf_path: str, sanitize: bool = True, model: str = None, streaming: bool = True) -> tuple:
    """
    Extract text and count tokens for the text that will be sent to the model.

    Returns:
        (text, token_count)
    """
    text = extract_text_advanced(pdf_path)
    if text is None:
        text = ""
    if sanitize:
        text = sanitize_text_for_tts(text)

    model = model or DEFAULT_MODEL
    if streaming:
        tokens = count_tokens_streaming(text, model=model)
    else:
        tokens = count_tokens(text, model=model)
    return text, tokens