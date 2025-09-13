import base64
import os
from typing import Optional
from google import genai
from google.genai import types
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger('speech_service')

class SpeechToTextService:
    """Service for converting speech to text using Gemini STT"""
    
    def __init__(self):
        """Initialize the speech-to-text service"""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_STT_MODEL
        logger.info("SpeechToTextService initialized")
    
    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribes an audio file using the Gemini 2.5 Pro model.
        
        Args:
            audio_file_path (str): The path to the audio file to transcribe.
            
        Returns:
            Optional[str]: The transcribed text or None if failed
        """
        try:
            logger.info(f"Starting transcription for file: {audio_file_path}")
            
            # Check if the audio file exists
            if not os.path.exists(audio_file_path):
                logger.error(f"Audio file '{audio_file_path}' does not exist")
                return None
            
            # Read the audio file in binary mode and encode it in base64
            with open(audio_file_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
                audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            
            logger.info(f"Audio file size: {len(audio_bytes)} bytes")
            
            # Determine MIME type based on file extension
            file_extension = os.path.splitext(audio_file_path)[1].lower()
            mime_type_map = {
                '.wav': 'audio/wav',
                '.mp3': 'audio/mpeg',
                '.m4a': 'audio/mp4',
                '.ogg': 'audio/ogg',
                '.flac': 'audio/flac'
            }
            
            mime_type = mime_type_map.get(file_extension, 'audio/wav')
            logger.info(f"Using MIME type: {mime_type}")
            
            # Define the content parts for the multimodal input
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text="Please provide a detailed transcription of the following audio. "
                                 "Do not include any extra commentary, just the transcription."
                        ),
                        types.Part(
                            inline_data=types.Blob(
                                mime_type=mime_type,
                                data=audio_base64
                            )
                        ),
                    ],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=-1,
                ),
            )
            
            # Get transcription from Gemini
            logger.info("Sending audio to Gemini API for transcription...")
            
            transcription_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text:
                    transcription_text += chunk.text
            
            if transcription_text.strip():
                logger.info(f"Transcription successful: {transcription_text[:100]}...")
                return transcription_text.strip()
            else:
                logger.warning("Empty transcription received")
                return None
                
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            return None
    
    def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        return ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
    
    def validate_audio_file(self, file_path: str) -> bool:
        """
        Validate if the audio file is supported and accessible
        
        Args:
            file_path (str): Path to the audio file
            
        Returns:
            bool: True if file is valid, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                return False
            
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension not in self.get_supported_formats():
                logger.error(f"Unsupported file format: {file_extension}")
                return False
            
            file_size = os.path.getsize(file_path)
            max_size = 25 * 1024 * 1024  # 25MB limit for Gemini API
            if file_size > max_size:
                logger.error(f"File too large: {file_size} bytes (max: {max_size})")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating audio file: {str(e)}")
            return False

# Create global instance
stt_service = SpeechToTextService()