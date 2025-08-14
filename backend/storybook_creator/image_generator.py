# storybook_creator/image_generator.py
import os
import logging
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types

logger = logging.getLogger(__name__)

def configure_api():
    """Loads the API key from the .env file and creates a genai.Client."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.critical("GOOGLE_API_KEY not found in .env file. Image generation will fail.")
        raise ValueError("GOOGLE_API_KEY not found in .env file. Please set it.")
    return genai.Client(api_key=api_key)

# Create the API client once when the module loads
client = configure_api()

def generate_master_prompt(character_desc: str, style_desc: str) -> str:
    """
    Expands simple user descriptions into a detailed master prompt.
    Ensures character and style consistency across all images.
    """
    logger.info(f"Generating master prompt with character '{character_desc}' and style '{style_desc}'.")
    return (
        "Master Instructions: Create all images with the following consistent style and character. "
        f"Character Details: A character based on the description '{character_desc}'. "
        "Maintain the character's facial features, clothing, and hair style identically in every image. "
        f"Artistic Style: A consistent style of '{style_desc}'. "
        "The color palette, line work, and overall mood must be the same across all images. "
        "Do not include any text, letters, or numbers in the generated images. "
        "This is a storybook, so ensure the style is cohesive from one image to the next."
    )

def generate_consistent_image(master_prompt: str, scene_prompt: str, output_path: str) -> bool:
    """
    Generates an image using Google GenAI.
    Uses image generation according to current Gemini/Imagen API.
    """
    full_prompt = f"{master_prompt}\n\nCurrent Scene: {scene_prompt}"

    try:
        # Prefer current Gemini image generation entrypoint; see docs for models/config[24][21]
        logger.info(f"Generating image with prompt: {full_prompt[:160]}...")
        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            ),
        )

        # Extract first image from response
        image_bytes = None
        if response and response.candidates:
            for part in response.candidates[0].content.parts:
                if getattr(part, "inline_data", None) and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    break

        if not image_bytes:
            logger.warning("Image generation returned no image data.")
            return False

        with open(output_path, "wb") as f:
            f.write(image_bytes)
        logger.info(f"Image successfully generated and saved to {output_path}")
        return True

    except Exception as e:
        logger.exception(f"Error calling Image Generation API: {e}")
        return False
