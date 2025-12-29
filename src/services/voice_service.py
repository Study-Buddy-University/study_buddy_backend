import io
import tempfile
from pathlib import Path
from typing import BinaryIO

from faster_whisper import WhisperModel

from src.config import settings
from src.core.exceptions import FileProcessingError


class VoiceService:
    def __init__(self):
        self.model = None
        self.model_name = settings.WHISPER_MODEL
        self.device = settings.WHISPER_DEVICE

    def _load_model(self):
        if self.model is None:
            try:
                self.model = WhisperModel(self.model_name, device=self.device, compute_type="int8")
            except Exception as e:
                raise FileProcessingError(f"Failed to load Whisper model: {str(e)}")

    async def transcribe_audio(self, audio_file: BinaryIO, language: str = None) -> str:
        self._load_model()
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                audio_content = audio_file.read()
                temp_file.write(audio_content)
                temp_path = temp_file.name
            
            try:
                segments, info = self.model.transcribe(
                    temp_path,
                    language=language,
                )
                
                text = " ".join([segment.text for segment in segments])
                return text.strip()
            finally:
                Path(temp_path).unlink(missing_ok=True)
                
        except Exception as e:
            raise FileProcessingError(f"Failed to transcribe audio: {str(e)}")

    async def text_to_speech(self, text: str) -> bytes:
        raise NotImplementedError("TTS feature not implemented - pyttsx3 removed for Python 3.13 compatibility")
