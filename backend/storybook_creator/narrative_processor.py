# storybook_creator/narrative_processor.py
from spacy.lang.en import English
import logging

logger = logging.getLogger(__name__)

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
