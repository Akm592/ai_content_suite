# storybook_creator/narrative_processor.py
import os
import logging
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types
from spacy.lang.en import English

logger = logging.getLogger(__name__)

def configure_api():
    """Loads the API key from the .env file and creates a genai.Client."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.critical("GEMINI_API_KEY not found in .env file. Text generation will fail.")
        raise ValueError("GEMINI_API_KEY not found in .env file. Please set it.")
    return genai.Client(api_key=api_key)

# Create the API client once when the module loads
client = configure_api()

def segment_story_into_scenes(full_text: str, max_tokens: int = 250) -> list[str]:
    """
    Segments text into scenes of roughly max_tokens using spaCy sentencizer.
    """
    try:
        logger.info(f"Segmenting story into scenes with max_tokens={max_tokens}.")
        nlp = English()
        nlp.add_pipe("sentencizer")
        doc = nlp(full_text)

        def token_count(s: str) -> int:
            return len(s.split())

        scenes = []
        current = []
        current_tokens = 0

        for sent in doc.sents:
            s = sent.text.strip()
            if not s:
                continue
            t = token_count(s)
            if current and current_tokens + t > max_tokens:
                scenes.append(" ".join(current))
                current = [s]
                current_tokens = t
            else:
                current.append(s)
                current_tokens += t

        if current:
            scenes.append(" ".join(current))

        if not scenes:
            scenes = [p for p in full_text.split("\n") if p.strip()]

        logger.info(f"Story successfully segmented into {len(scenes)} scenes.")
        return scenes

    except Exception as e:
        logger.exception(f"Error during story segmentation: {e}")
        logger.warning("Falling back to a simpler split method (by newline).")
        return [para for para in full_text.split('\n') if para.strip()]

def generate_title_and_author(story_text: str) -> tuple[str, str]:
    """
    Generates a story title and a fictional author name using a Gemini LLM.
    """
    logger.info("Generating title and author for story.")
    prompt = (
        "Based on the following story text, suggest a concise and engaging title "
        "and a creative, fictional author name. "
        "Respond in the format: 'Title: [Your Title]\nAuthor: [Your Author Name]'.\n\n"
        "Story Text:\n"
        f"{story_text[:1000]}..." # Limit story text to avoid exceeding token limits
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-001", # Using a text-focused model
            contents=[prompt],
            generation_config=types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=100
            )
        )
        
        if not response or not response.candidates:
            raise ValueError("LLM response was empty or invalid.")

        generated_text = response.candidates[0].content.parts[0].text
        
        title = "Untitled Story"
        author = "Anonymous"

        lines = generated_text.strip().split('\n')
        for line in lines:
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
            elif line.startswith("Author:"):
                author = line.replace("Author:", "").strip()
        
        logger.info(f"Generated Title: '{title}', Author: '{author}'")
        return title, author

    except Exception as e:
        logger.exception(f"Error generating title and author with LLM: {e}")
        logger.warning("Falling back to default title and author.")
        return "Untitled Story", "Anonymous"

