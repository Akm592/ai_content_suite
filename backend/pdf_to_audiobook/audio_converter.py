# pdf_to_audiobook/audio_converter.py
from pydub import AudioSegment
import io
import logging

logger = logging.getLogger(__name__)

def convert_wav_bytes_to_mp3(wav_bytes: bytes, output_path: str) -> bool:
    """
    Converts a WAV byte stream to an MP3 file using pydub.
    """
    try:
        logger.info(f"Converting {len(wav_bytes)} bytes of WAV data to MP3.")
        audio_segment = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
        logger.info(f"Exporting MP3 to {output_path} with bitrate 192k.")
        audio_segment.export(output_path, format="mp3", bitrate="192k")
        logger.info(f"Successfully converted audio and saved to {output_path}")
        return True
    except Exception as e:
        logger.exception(f"Error converting audio to MP3: {e}")
        logger.critical("Please ensure that FFmpeg is installed and accessible in your system's PATH.")
        return False
