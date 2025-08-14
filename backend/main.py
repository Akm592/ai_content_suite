# backend/main.py

# --- Core Python Libraries ---
import os
import tempfile
import shutil
import logging

# --- FastAPI Imports ---
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# --- Your Custom Logic Modules ---
from pdf_to_audiobook.pdf_parser import extract_text_advanced, sanitize_text_for_tts
from pdf_to_audiobook.tts_generator import generate_audio_with_profile
from pdf_to_audiobook.audio_converter import convert_wav_bytes_to_mp3

from storybook_creator.narrative_processor import segment_story_into_scenes
from storybook_creator.image_generator import generate_master_prompt, generate_consistent_image
from storybook_creator.pdf_assembler import create_storybook_pdf

# --- Logging & App ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Content Transformation Suite API")

# --- CORS ---
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Root ---
@app.get("/")
def read_root():
    logger.info("Root endpoint accessed. API is running.")
    return {"message": "Welcome to the AI Content Suite Backend!"}

# --- Cleanup Helper ---
def cleanup_directory(directory: str):
    """Remove a directory and its contents."""
    try:
        shutil.rmtree(directory, ignore_errors=True)
        logger.info(f"Successfully cleaned up temporary directory: {directory}")
    except Exception as e:
        logger.error(f"Error during cleanup of directory {directory}: {e}")

# --- PDF to Audiobook ---
@app.post("/audiobook/convert")
async def convert_pdf_to_audiobook(
    background_tasks: BackgroundTasks,
    voice: str = Form(...),
    pdf_file: UploadFile = File(...)
):
    temp_dir = tempfile.mkdtemp()
    background_tasks.add_task(cleanup_directory, temp_dir)

    logger.info(f"Received request to convert PDF '{pdf_file.filename}' to audiobook with voice '{voice}'.")
    logger.info(f"Temporary directory created at '{temp_dir}'. It will be cleaned up after the request.")

    temp_pdf_path = os.path.join(temp_dir, pdf_file.filename)

    try:
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)
        logger.info(f"PDF file saved temporarily to '{temp_pdf_path}'.")

        logger.info("Step 1: Extracting text...")
        raw_text = extract_text_advanced(temp_pdf_path)
        if not raw_text:
            raise HTTPException(status_code=400, detail="Failed to extract any text from the PDF.")

        logger.info("Step 2: Sanitizing text...")
        clean_text = sanitize_text_for_tts(raw_text)

        logger.info(f"Step 3: Generating audio with voice '{voice}'...")
        wav_audio_data = generate_audio_with_profile(clean_text, voice)
        if not wav_audio_data:
            raise HTTPException(status_code=500, detail="AI model failed to generate audio.")

        logger.info("Step 4: Converting to MP3...")
        output_mp3_path = os.path.join(temp_dir, "output.mp3")
        conversion_success = convert_wav_bytes_to_mp3(wav_audio_data, output_mp3_path)
        if not conversion_success:
            raise HTTPException(status_code=500, detail="Error converting audio file. Check server logs.")

        logger.info(f"Successfully created audiobook. Sending file: {output_mp3_path}")
        return FileResponse(
            path=output_mp3_path,
            media_type="audio/mpeg",
            filename="audiobook.mp3",
        )

    except Exception as e:
        logger.exception(f"An unexpected error occurred during audiobook conversion: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# --- Storybook Creation ---
@app.post("/storybook/create")
async def create_ai_storybook(
    background_tasks: BackgroundTasks,
    story_text: str = Form(...),
    character_desc: str = Form(...),
    style_desc: str = Form(...),
):
    logger.info("Received request to create a new AI storybook.")
    temp_dir = tempfile.mkdtemp()
    background_tasks.add_task(cleanup_directory, temp_dir)

    try:
        logger.info("Step 1: Generating master prompt...")
        master_prompt = generate_master_prompt(character_desc, style_desc)

        logger.info("Step 2: Segmenting story into scenes...")
        scenes = segment_story_into_scenes(story_text)
        if not scenes:
            raise HTTPException(status_code=400, detail="Could not segment the story text.")

        logger.info(f"Step 3: Generating {len(scenes)} images...")
        illustrated_scenes = []
        for i, scene_text in enumerate(scenes):
            image_path = os.path.join(temp_dir, f"scene_{i+1}.png")
            logger.info(f"Generating image for scene {i+1}...")
            success = generate_consistent_image(master_prompt, scene_text, image_path)
            illustrated_scenes.append({
                "text": scene_text,
                "image_path": image_path if success else None
            })

        logger.info("Step 4: Assembling final PDF...")
        output_pdf_path = os.path.join(temp_dir, "storybook.pdf")
        create_storybook_pdf(illustrated_scenes, output_pdf_path)

        logger.info(f"Successfully created storybook. Sending file: {output_pdf_path}")
        return FileResponse(
            path=output_pdf_path,
            media_type="application/pdf",
            filename="ai_storybook.pdf",
        )

    except Exception as e:
        logger.exception(f"An error occurred during storybook creation: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")
