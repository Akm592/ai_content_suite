# backend/main.py

# --- Core Python Libraries ---
import os
import tempfile
import shutil
import logging
import uuid
import json

# --- Pydantic for Request Bodies ---
from pydantic import BaseModel

# --- FastAPI Imports ---
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# --- Your Custom Logic Modules ---
from redis_client import get_redis_client
from pdf_to_audiobook.pdf_parser import extract_text_and_count, sanitize_text_for_tts
from pdf_to_audiobook.tts_generator import generate_audio_with_profile
from pdf_to_audiobook.audio_converter import convert_wav_bytes_to_mp3
from storybook_creator.narrative_processor import segment_story_into_scenes, generate_title_and_author, client as gemini_client
from pdf_to_audiobook.token_counter import count_tokens_streaming as local_count_tokens
from storybook_creator.image_generator import generate_master_prompt, generate_consistent_image
from storybook_creator.pdf_assembler import create_storybook_pdf

# --- Constants ---
MAX_TOKENS_FOR_PROCESSING = 10000 # Maximum tokens allowed for LLM/TTS processing
MAX_PDF_TOKENS = 3000 # Maximum tokens allowed for PDF input before warning

# --- Logging & App Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Content Transformation Suite API")
redis_client = get_redis_client()

# --- CORS Middleware ---
origins = ["http://localhost:3000", os.getenv("FRONTEND_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Session Management & Cleanup ---
SESSION_EXPIRATION_SECONDS = 7200  # 2 hours

def cleanup_directory(session_id: str, directory: str):
    """Removes a session's temporary directory and its key from Redis."""
    try:
        shutil.rmtree(directory, ignore_errors=True)
        redis_client.delete(f"session:{session_id}")
        logger.info(f"Successfully cleaned up session {session_id} and directory: {directory}")
    except Exception as e:
        logger.error(f"Error during cleanup of session {session_id} in directory {directory}: {e}")

def get_session_dir(session_id: str) -> str:
    """Helper function to get a session's directory from Redis, raising an error if not found."""
    session_key = f"session:{session_id}"
    session_dir = redis_client.get(session_key)
    if not session_dir:
        raise HTTPException(status_code=404, detail="Session not found or has expired.")
    return session_dir

def _check_and_truncate_text(text: str, max_tokens: int = MAX_TOKENS_FOR_PROCESSING) -> str:
    """
    Checks the token count of the given text and truncates it if it exceeds max_tokens.
    Logs a warning if truncation occurs.
    """
    try:
        # Use the local token counter
        token_count = local_count_tokens(text, model="gpt-4o")
        
        if token_count > max_tokens:
            logger.warning(f"Input text exceeds token limit ({token_count} > {max_tokens}). Truncating text.")
            # A simple truncation strategy: keep roughly max_tokens worth of characters.
            # This is a rough estimate, as character-to-token ratio varies.
            # For more precision, one would need a proper tokenizer, but this is a guardrail.
            # Assuming ~4 chars per token for English.
            truncated_text = text[:max_tokens * 4] 
            # Ensure truncation doesn't cut in the middle of a word or sentence awkwardly
            # Find the last space before the truncation point
            last_space_index = truncated_text.rfind(' ')
            if last_space_index != -1:
                truncated_text = truncated_text[:last_space_index]
            
            return truncated_text + "..." # Add ellipsis to indicate truncation
        return text
    except Exception as e:
        logger.error(f"Error counting or truncating tokens: {e}. Returning original text.")
        return text # Fallback to original text if token counting fails

# --- Root Endpoint ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Content Suite Backend!"}

# --- PDF to Audiobook Service ---
@app.post("/audiobook/convert")
async def convert_pdf_to_audiobook(background_tasks: BackgroundTasks, voice: str = Form(...), pdf_file: UploadFile = File(...)):
    temp_dir = tempfile.mkdtemp()
    background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)
    
    logger.info(f"Received request to convert PDF '{pdf_file.filename}' to audiobook with voice '{voice}'.")
    temp_pdf_path = os.path.join(temp_dir, pdf_file.filename)
    try:
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)
        raw_text, _ = extract_text_and_count(temp_pdf_path, sanitize=False, streaming=True)
        if not raw_text: raise HTTPException(status_code=400, detail="Failed to extract any text from the PDF.")
        clean_text = sanitize_text_for_tts(raw_text)
        
        # Apply token limit guardrail
        processed_text = _check_and_truncate_text(clean_text)

        wav_audio_data = generate_audio_with_profile(processed_text, voice)
        if not wav_audio_data: raise HTTPException(status_code=500, detail="AI model failed to generate audio.")
        output_mp3_path = os.path.join(temp_dir, "output.mp3")
        if not convert_wav_bytes_to_mp3(wav_audio_data, output_mp3_path):
            raise HTTPException(status_code=500, detail="Error converting audio file.")
        return FileResponse(path=output_mp3_path, media_type="audio/mpeg", filename="audiobook.mp3")
    except Exception as e:
        logger.exception(f"An unexpected error occurred during audiobook conversion: {e}")
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# AI STORYBOOK CREATOR SERVICE
# ==============================================================================

class StorybookStyle(BaseModel):
    font_name: str
    font_size: int

class SceneUpdate(BaseModel):
    text: str

class StoryDetailsUpdate(BaseModel):
    title: str
    author: str

# --- Flow 1: Direct, Stateless Generation ---
@app.post("/storybook/create-and-finalize")
async def create_and_finalize_storybook(
    background_tasks: BackgroundTasks,
    story_text: str = Form(None),
    pdf_file: UploadFile = File(None),
    character_desc: str = Form(...),
    style_desc: str = Form(...)
):
    logger.info("Request received for direct-to-PDF storybook generation.")
    temp_dir = tempfile.mkdtemp()
    background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)

    extracted_story_text = None
    if pdf_file:
        temp_pdf_path = os.path.join(temp_dir, pdf_file.filename)
        try:
            with open(temp_pdf_path, "wb") as buffer:
                shutil.copyfileobj(pdf_file.file, buffer)
            raw_text, pdf_token_count = extract_text_and_count(temp_pdf_path, sanitize=True, model="gpt-4o", streaming=True)
            if not raw_text:
                raise HTTPException(status_code=400, detail="Failed to extract any text from the PDF.")
            
            # Apply PDF-specific token guardrail
            if pdf_token_count > MAX_PDF_TOKENS:
                raise HTTPException(
                    status_code=400,
                    detail=f"PDF content ({pdf_token_count} tokens) exceeds the limit of {MAX_PDF_TOKENS} tokens. "
                           "Please use a smaller PDF or provide text directly."
                )
            
            extracted_story_text = raw_text # Use raw_text after token check
        except Exception as e:
            logger.exception(f"Error processing uploaded PDF: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")
    
    final_story_text = extracted_story_text if extracted_story_text else story_text

    if not final_story_text:
        raise HTTPException(status_code=400, detail="Either 'story_text' or 'pdf_file' must be provided.")

    # Apply general token limit guardrail (truncation)
    processed_story_text = _check_and_truncate_text(final_story_text)

    try:
        story_title, author = generate_title_and_author(processed_story_text)
        master_prompt = generate_master_prompt(character_desc, style_desc)
        scenes = segment_story_into_scenes(processed_story_text)
        if not scenes: raise HTTPException(status_code=400, detail="Could not segment the story text.")
        illustrated_scenes = []
        for i, scene_text in enumerate(scenes):
            image_path = os.path.join(temp_dir, f"scene_{i+1}.png")
            success = generate_consistent_image(master_prompt, scene_text, image_path)
            illustrated_scenes.append({"text": scene_text, "image_path": image_path if success else None})
        output_pdf_path = os.path.join(temp_dir, "storybook.pdf")
        create_storybook_pdf(illustrated_scenes, output_pdf_path, story_title=story_title, author=author)
        return FileResponse(path=output_pdf_path, media_type="application/pdf", filename="ai_storybook.pdf")
    except Exception as e:
        logger.exception(f"An error occurred during direct-to-PDF storybook creation: {e}")
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

# --- Flow 2: Interactive Session Endpoints ---

@app.post("/storybook/session/start")
async def start_storybook_session(
    story_text: str = Form(None),
    pdf_file: UploadFile = File(None),
    character_desc: str = Form(...),
    style_desc: str = Form(...)
):
    session_id = str(uuid.uuid4())
    temp_dir = tempfile.mkdtemp(prefix=f"storybook_{session_id}_")
    redis_client.set(f"session:{session_id}", temp_dir, ex=SESSION_EXPIRATION_SECONDS)
    logger.info(f"Starting new storybook session: {session_id} in {temp_dir}")

    extracted_story_text = None
    if pdf_file:
        temp_pdf_path = os.path.join(temp_dir, pdf_file.filename)
        try:
            with open(temp_pdf_path, "wb") as buffer:
                shutil.copyfileobj(pdf_file.file, buffer)
            raw_text, pdf_token_count = extract_text_and_count(temp_pdf_path, sanitize=True, model="gpt-4o", streaming=True)
            if not raw_text:
                raise HTTPException(status_code=400, detail="Failed to extract any text from the PDF.")
            
            # Apply PDF-specific token guardrail
            if pdf_token_count > MAX_PDF_TOKENS:
                raise HTTPException(
                    status_code=400,
                    detail=f"PDF content ({pdf_token_count} tokens) exceeds the limit of {MAX_PDF_TOKENS} tokens. "
                           "Please use a smaller PDF or provide text directly."
                )
            
            extracted_story_text = raw_text # Use raw_text after token check
        except Exception as e:
            logger.exception(f"Error processing uploaded PDF: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")
    
    final_story_text = extracted_story_text if extracted_story_text else story_text

    if not final_story_text:
        raise HTTPException(status_code=400, detail="Either 'story_text' or 'pdf_file' must be provided.")

    # Apply general token limit guardrail (truncation)
    processed_story_text = _check_and_truncate_text(final_story_text)

    story_title, author = generate_title_and_author(processed_story_text)
    master_prompt = generate_master_prompt(character_desc, style_desc)
    scenes = segment_story_into_scenes(processed_story_text)
    base_url = f"/storybook/session/{session_id}/image/"
    illustrated_scenes = []
    for i, scene_text in enumerate(scenes):
        image_name = f"scene_{i+1}.png"
        image_path = os.path.join(temp_dir, image_name)
        success = generate_consistent_image(master_prompt, scene_text, image_path)
        illustrated_scenes.append({"text": scene_text, "image_url": f"{base_url}{image_name}" if success else None})
    session_data = {"session_id": session_id, "master_prompt": master_prompt, "styles": {"font_name": "Helvetica", "font_size": 14}, "scenes": illustrated_scenes, "title": story_title, "author": author}
    with open(os.path.join(temp_dir, "session_data.json"), "w") as f:
        json.dump(session_data, f, indent=4)
    return session_data

@app.get("/storybook/session/{session_id}/state")
def get_session_state(session_id: str):
    session_dir = get_session_dir(session_id)
    session_data_path = os.path.join(session_dir, "session_data.json")
    if not os.path.exists(session_data_path):
        raise HTTPException(status_code=404, detail="Session data file not found.")
    with open(session_data_path, "r") as f:
        return json.load(f)

@app.get("/storybook/session/{session_id}/image/{image_name}")
async def get_session_image(session_id: str, image_name: str):
    session_dir = get_session_dir(session_id)
    image_path = os.path.join(session_dir, image_name)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found in session")
    return FileResponse(image_path)

@app.put("/storybook/session/{session_id}/scene/{scene_index}")
async def update_scene_text(session_id: str, scene_index: int, update_data: SceneUpdate):
    session_dir = get_session_dir(session_id)
    session_data_path = os.path.join(session_dir, "session_data.json")
    with open(session_data_path, "r") as f:
        session_data = json.load(f)
    if not 0 <= scene_index < len(session_data["scenes"]):
        raise HTTPException(status_code=400, detail="Scene index out of bounds.")
    session_data["scenes"][scene_index]["text"] = update_data.text
    with open(session_data_path, "w") as f:
        json.dump(session_data, f, indent=4)
    return {"message": "Scene updated successfully"}

@app.post("/storybook/session/{session_id}/scene/{scene_index}/regenerate")
async def regenerate_scene_image(session_id: str, scene_index: int):
    session_dir = get_session_dir(session_id)
    session_data_path = os.path.join(session_dir, "session_data.json")
    with open(session_data_path, "r") as f:
        session_data = json.load(f)
    if not 0 <= scene_index < len(session_data["scenes"]):
        raise HTTPException(status_code=400, detail="Scene index out of bounds.")
    scene = session_data["scenes"][scene_index]
    image_name = f"scene_{scene_index + 1}.png"
    image_path = os.path.join(session_dir, image_name)
    if not generate_consistent_image(session_data["master_prompt"], scene["text"], image_path):
        raise HTTPException(status_code=500, detail="Failed to regenerate image.")
    new_image_url = f"/storybook/session/{session_id}/image/{image_name}"
    session_data["scenes"][scene_index]["image_url"] = new_image_url
    with open(session_data_path, "w") as f:
        json.dump(session_data, f, indent=4)
    return {"message": "Image regenerated successfully", "new_image_url": new_image_url}

@app.put("/storybook/session/{session_id}/styles")
async def update_styles(session_id: str, styles: StorybookStyle):
    session_dir = get_session_dir(session_id)
    session_data_path = os.path.join(session_dir, "session_data.json")
    with open(session_data_path, "r") as f:
        session_data = json.load(f)
    session_data["styles"] = styles.dict()
    with open(session_data_path, "w") as f:
        json.dump(session_data, f, indent=4)
    return {"message": "Styles updated successfully"}

@app.put("/storybook/session/{session_id}/details")
async def update_storybook_details(session_id: str, update_data: StoryDetailsUpdate):
    session_dir = get_session_dir(session_id)
    session_data_path = os.path.join(session_dir, "session_data.json")
    with open(session_data_path, "r") as f:
        session_data = json.load(f)
    session_data["title"] = update_data.title
    session_data["author"] = update_data.author
    with open(session_data_path, "w") as f:
        json.dump(session_data, f, indent=4)
    return {"message": "Story details updated successfully"}

@app.get("/storybook/session/{session_id}/preview")
async def preview_storybook(session_id: str):
    """Generates a PDF for previewing (inline) and does NOT clean up the session."""
    session_dir = get_session_dir(session_id)
    session_data_path = os.path.join(session_dir, "session_data.json")
    with open(session_data_path, "r") as f:
        session_data = json.load(f)
    for scene in session_data["scenes"]:
        if scene.get("image_url"):
            scene["image_path"] = os.path.join(session_dir, os.path.basename(scene["image_url"]))
    output_pdf_path = os.path.join(session_dir, "preview_storybook.pdf")
    create_storybook_pdf(
        session_data["scenes"],
        output_pdf_path,
        font_name=session_data["styles"]["font_name"],
        font_size=session_data["styles"]["font_size"],
        story_title=session_data.get("title", "My Storybook"),
        author=session_data.get("author", "Anonymous")
    )
    logger.info(f"Generated PREVIEW PDF for session {session_id}.")
    return FileResponse(path=output_pdf_path, media_type="application/pdf", headers={"Content-Disposition": "inline"})

@app.get("/storybook/session/{session_id}/download")
async def download_final_pdf(session_id: str, background_tasks: BackgroundTasks):
    """Generates the final PDF, serves it for download, and triggers session cleanup."""
    session_dir = get_session_dir(session_id)
    session_data_path = os.path.join(session_dir, "session_data.json")
    with open(session_data_path, "r") as f:
        session_data = json.load(f)
    for scene in session_data["scenes"]:
        if scene.get("image_url"):
            scene["image_path"] = os.path.join(session_dir, os.path.basename(scene["image_url"]))
    output_pdf_path = os.path.join(session_dir, "final_storybook.pdf")
    create_storybook_pdf(
        session_data["scenes"],
        output_pdf_path,
        font_name=session_data["styles"]["font_name"],
        font_size=session_data["styles"]["font_size"],
        story_title=session_data.get("title", "My Storybook"),
        author=session_data.get("author", "Anonymous")
    )
    
    # Schedule the session directory and Redis key to be deleted AFTER the response is sent.
    background_tasks.add_task(cleanup_directory, session_id, session_dir)
    
    logger.info(f"Serving FINAL PDF for session {session_id} and scheduling cleanup.")
    return FileResponse(path=output_pdf_path, media_type="application/pdf", filename="ai_storybook.pdf")