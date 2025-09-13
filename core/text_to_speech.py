import requests
import wave
import base64
import json
import os
import uuid
from typing import Optional
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger('speech_service')

class TextToSpeechService:
    """Service for converting text to speech using Gemini TTS"""
    
    def __init__(self):
        """Initialize the text-to-speech service"""
        self.api_key = settings.GEMINI_API_KEY
        self.voice_name = settings.TTS_VOICE_NAME
        self.model = settings.GEMINI_TTS_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        logger.info("TextToSpeechService initialized")
    
    def _save_wav(self, file_path: str, audio_data: bytes) -> bool:
        """
        Saves raw PCM audio data to a WAV file.
        
        Args:
            file_path (str): Path where to save the WAV file
            audio_data (bytes): Raw audio data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(settings.AUDIO_CHANNELS)  # Mono
                wf.setsampwidth(settings.AUDIO_SAMPLE_WIDTH)  # 16-bit
                wf.setframerate(settings.AUDIO_SAMPLE_RATE)  # Sample rate
                wf.writeframes(audio_data)
            
            logger.info(f"Audio saved successfully to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving WAV file: {str(e)}")
            return False
    
    async def generate_speech(
        self, 
        text: str, 
        output_file: Optional[str] = None,
        voice_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Generates speech from text and saves it as a WAV file.
        
        Args:
            text (str): Text to convert to speech
            output_file (Optional[str]): Output file path (auto-generated if None)
            voice_name (Optional[str]): Voice name to use (default from config)
            
        Returns:
            Optional[str]: Path to the generated audio file or None if failed
        """
        try:
            logger.info(f"Generating speech for text: {text[:100]}...")
            
            # Use provided voice or default
            voice = voice_name or self.voice_name
            
            # Generate output filename if not provided
            if not output_file:
                unique_id = str(uuid.uuid4())[:8]
                output_file = os.path.join(settings.TEMP_DIR, f"tts_output_{unique_id}.wav")
            
            # Prepare API request
            url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "contents": [{"parts": [{"text": text}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": voice
                            }
                        }
                    }
                }
            }
            
            logger.info("Sending request to Gemini TTS API...")
            
            # Make API request
            response = requests.post(
                url, 
                headers=headers, 
                data=json.dumps(payload),
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"TTS API error: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            
            # Extract audio data
            if 'candidates' not in result or not result['candidates']:
                logger.error("No audio data in API response")
                return None
            
            candidate = result['candidates'][0]
            if 'content' not in candidate or 'parts' not in candidate['content']:
                logger.error("Invalid response structure from TTS API")
                return None
            
            parts = candidate['content']['parts']
            audio_part = None
            
            for part in parts:
                if 'inlineData' in part:
                    audio_part = part
                    break
            
            if not audio_part:
                logger.error("No audio data found in response")
                return None
            
            # Decode base64 audio data
            base64_audio_data = audio_part['inlineData']['data']
            audio_bytes = base64.b64decode(base64_audio_data)
            
            # Save audio file
            if self._save_wav(output_file, audio_bytes):
                logger.info(f"TTS generation successful: {output_file}")
                return output_file
            else:
                return None
                
        except requests.exceptions.Timeout:
            logger.error("TTS API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS API request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error during TTS generation: {str(e)}")
            return None
    
    def get_available_voices(self) -> list:
        """Get list of available voice names"""
        # Common Gemini TTS voices
        return [
            "Kore",
            "Charon", 
            "Aoede",
            "Fenrir"
        ]
    
    def validate_text_length(self, text: str) -> bool:
        """
        Validate if text length is within acceptable limits
        
        Args:
            text (str): Text to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        max_length = 5000  # Reasonable limit for TTS
        if len(text) > max_length:
            logger.warning(f"Text too long for TTS: {len(text)} characters (max: {max_length})")
            return False
        
        if not text.strip():
            logger.warning("Empty text provided for TTS")
            return False
        
        return True
    
    async def generate_speech_for_response(self, text: str) -> Optional[str]:
        """
        Convenience method to generate speech for agent responses
        
        Args:
            text (str): Response text to convert to speech
            
        Returns:
            Optional[str]: Path to generated audio file
        """
        if not self.validate_text_length(text):
            return None
        
        # Clean text for better TTS output
        cleaned_text = text.replace("*", "").replace("#", "").strip()
        
        return await self.generate_speech(cleaned_text)

# Create global instance
tts_service = TextToSpeechService()