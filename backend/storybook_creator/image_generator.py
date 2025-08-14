import os
import logging
import time
import io
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)

# ---------------- Constants ---------------- #
MODEL_NAME = "gemini-2.0-flash-preview-image-generation"
NO_TEXT_IN_IMAGE_INSTRUCTION = (
    "Do not include any text, letters, numbers, words, symbols, signs, or typographic marks anywhere in the image. "
    "No watermarks, captions, labels, speech bubbles, or logos."
)

# ---------------- API Client Setup ---------------- #
def configure_api():
    """Loads the API key from the .env file and creates a genai.Client."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.critical("GEMINI_API_KEY not found in .env file. Image generation will fail.")
        raise ValueError("GEMINI_API_KEY not found in .env file. Please set it.")
    return genai.Client(api_key=api_key)

# Create the API client once when the module loads
client = configure_api()

# ---------------- OCR Guardrail ---------------- #
def image_contains_text(image_bytes: bytes) -> bool:
    """Checks if an image contains any detectable text using OCR."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        text_found = pytesseract.image_to_string(img).strip()
        if text_found:
            logger.warning(f"OCR detected text in generated image: '{text_found[:50]}...'")
            return True
        return False
    except Exception as e:
        logger.exception(f"OCR check failed: {e}")
        return False  # Fail-safe: if OCR fails, treat as no text to avoid false positives

# ---------------- Prompt Generation ---------------- #
def generate_master_prompt(character_desc: str, style_desc: str) -> str:
    """
    Builds a robust, structured master prompt for text-to-image generation that:
    - Anchors character identity with stable, repeatable attributes
    - Specifies art/style, materials, lighting, color palette, and mood
    - Encourages composition discipline and scene coherence
    - Uses plain, explicit exclusions for text-free images (no 'don't/no' phrasing)
    - Is reusable across scenes to maintain visual consistency
    References for best practices: structured subject+style prompts and clarity on negative constraints[2][10][15][24].
    """
    # Rotating plain-language text prohibition variants improves adherence across attempts[10].
    text_prohibitions = [
        "Exclude all textual elements: letters, numbers, words, typographic symbols, captions, labels, logos, watermarks, and speech bubbles.",
        "Generate a purely visual image with zero text or typography: no letters, numerals, signs, captions, labels, logos, or watermarks.",
        "Omit all written content of any kind, including overlays, marks, labels, logos, captions, and watermarks."
    ]
    # Pick deterministically from variants to keep prompts stable across runs
    # (or randomize if preferred).
    text_block = text_prohibitions[0]

    # Optional: reusable “quality” and “consistency” anchors commonly cited in prompt design studies[2].
    consistency_anchor = (
        "Maintain identical facial features, hairstyle, clothing, body proportions, and unique identifiers "
        "(e.g., freckles, accessories) across all images for strict character consistency."
    )
    quality_anchor = (
        "High-quality, coherent composition with clean edges, balanced lighting, controlled noise, and accurate anatomy/perspective."
    )
    style_anchor = (
        "Adhere to the same palette, lighting style, brushwork/detail density, and overall mood to prevent style drift."
    )
    composition_anchor = (
        "Use clear subject framing, appropriate focal length, and depth cues; avoid clutter that competes with the main subject."
    )

    # Provide a template “shot scaffold” that scene prompts can fill consistently[2][10].
    shot_scaffold = (
        "If a scene specifies camera or framing, reflect it precisely (e.g., full-body, medium shot, close-up, profile, three-quarter view, "
        "over-the-shoulder), and keep the character’s identity unmistakable from any angle."
    )

    # Build the final master prompt with clear sections.
    prompt = (
        "MASTER IMAGE CREATION GUIDELINES\n\n"
        "Character Identity:\n"
        f"- {character_desc}\n"
        f"- {consistency_anchor}\n\n"
        "Artistic Style and Aesthetic:\n"
        f"- {style_desc}\n"
        f"- {style_anchor}\n"
        f"- {quality_anchor}\n\n"
        "Composition and Framing:\n"
        f"- {composition_anchor}\n"
        f"- {shot_scaffold}\n\n"
        "Color, Lighting, and Materials:\n"
        "- Keep the same color palette across scenes; ensure lighting feels consistent with the chosen style and mood.\n"
        "- Maintain material fidelity (fabric, metal, skin, hair) with realistic or intentionally stylized rendering, matching the declared style.\n\n"
        "Scene Coherence:\n"
        "- Environments, props, and wardrobe must complement the style and not alter the character’s identity or core attire unless the scene explicitly requires it.\n"
        "- Preserve continuity of defining accessories and proportions across different poses and angles.\n\n"
        "Negative Constraints (Text-Free Image):\n"
        f"- {text_block}\n\n"
        "Story and Continuity:\n"
        "- Maintain a cohesive, consistent visual narrative across all generated scenes without stylistic drift.\n"
    )
    return prompt

# ---------------- Image Generation ---------------- #
def generate_consistent_image(master_prompt: str, scene_prompt: str, output_path: str, retries: int = 3) -> bool:
    """
    Generates an image using Google GenAI with retries and OCR-based text guardrail.
    """
    full_prompt = (
        f"{master_prompt}\n"
        f"Scene Description: {scene_prompt}\n"
        f"{NO_TEXT_IN_IMAGE_INSTRUCTION}\n"
    )

    for attempt in range(retries):
        try:
            logger.info(f"Generating image (attempt {attempt+1}) with prompt: {full_prompt[:160]}...")
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"]
                ),
            )

            image_bytes = None
            if response and response.candidates:
                for part in response.candidates[0].content.parts:
                    if getattr(part, "inline_data", None) and part.inline_data.data:
                        image_bytes = part.inline_data.data
                        break

            if not image_bytes:
                logger.warning("No image data returned by API.")
                time.sleep(1.5 * (attempt + 1))
                continue

            # OCR Guardrail: reject if text is found
            if image_contains_text(image_bytes):
                logger.warning("Generated image contains text. Retrying...")
                time.sleep(1.5 * (attempt + 1))
                continue

            with open(output_path, "wb") as f:
                f.write(image_bytes)
            logger.info(f"Image successfully generated and saved to {output_path}")
            return True

        except Exception as e:
            logger.exception(f"Error calling Image Generation API (attempt {attempt+1}): {e}")
            time.sleep(1.5 * (attempt + 1))

    logger.error("Image generation failed after all retries.")
    return False
