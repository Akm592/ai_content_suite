# backend/pdf_to_audiobook/tts_generator.py
import os
import io
import logging
import struct
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types

logger = logging.getLogger(__name__)

VOICE_PROFILE_MAP = {
    "AMERICAN_MALE": "Puck",
    "AMERICAN_FEMALE": "Kore",
    "BRITISH_MALE": "Algieba",
    "BRITISH_FEMALE": "Despina",
}

# --- Load API key & configure client ONCE ---
def configure_api():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.critical("GEMINI_API_KEY not found in .env file.")
        raise ValueError("GEMINI_API_KEY not found.")
    return genai.Client(api_key=api_key)

client = configure_api()  # singleton client

def parse_audio_mime_type(mime_type: str):
    """
    Parse values like: audio/L16; rate=24000
    """
    bits_per_sample = 16
    rate = 24000
    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate = int(param.split("=")[1])
            except ValueError:
                pass
        elif "audio/L" in param:
            try:
                bits_per_sample = int(param.split("L")[1])
            except ValueError:
                pass
    return {"bits_per_sample": bits_per_sample, "rate": rate}

def convert_to_wav(audio_data: bytes, mime_type: str):
    """
    Construct a WAV header around raw PCM audio and return full WAV bytes.
    """
    params = parse_audio_mime_type(mime_type)
    bits_per_sample = params["bits_per_sample"]
    sample_rate = params["rate"]
    num_channels = 1

    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", chunk_size, b"WAVE", b"fmt ", 16, 1,
        num_channels, sample_rate, byte_rate, block_align,
        bits_per_sample, b"data", data_size
    )
    return header + audio_data

def generate_audio_with_profile(text: str, profile_key: str):
    """Generates audio from text using the Gemini TTS API."""
    profile_key = profile_key.upper()
    if profile_key not in VOICE_PROFILE_MAP:
        raise ValueError(f"Invalid profile key: {profile_key}")

    voice_name = VOICE_PROFILE_MAP[profile_key]
    logger.info(f"Generating audio with voice '{voice_name}'.")

    try:
        audio_buffer = io.BytesIO()
        audio_mime_type = None

        model = "gemini-2.5-flash-preview-tts"
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=text)]
            )
        ]

        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            ),
        )

        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                not chunk.candidates or
                not chunk.candidates[0].content or
                not chunk.candidates[0].content.parts
            ):
                continue

            part = chunk.candidates[0].content.parts[0]
            if getattr(part, "inline_data", None) and part.inline_data.data:
                if not audio_mime_type:
                    audio_mime_type = part.inline_data.mime_type
                audio_buffer.write(part.inline_data.data)

        if audio_buffer.getbuffer().nbytes > 0 and audio_mime_type:
            return convert_to_wav(audio_buffer.getvalue(), audio_mime_type)
        else:
            logger.warning("No audio data received.")
            return None

    except Exception as e:
        logger.exception(f"Error generating audio: {e}")
        return None
