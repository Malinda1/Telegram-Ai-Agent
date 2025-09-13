import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # Telegram Configuration
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    
    # Gemini API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Hugging Face Configuration
    HUGGINGFACEHUB_API_TOKEN: str = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
    
    # Google Cloud Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_PROJECT_ID: str = os.getenv("GOOGLE_PROJECT_ID", "")
    
    # FastAPI Configuration
    FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
    
    # File Paths
    TEMP_DIR: str = os.getenv("TEMP_DIR", "./temp")
    LOGS_DIR: str = os.getenv("LOGS_DIR", "./logs")
    CREDENTIALS_FILE: str = os.getenv("CREDENTIALS_FILE", "./credentials.json")
    
    # Audio Settings
    AUDIO_SAMPLE_RATE: int = int(os.getenv("AUDIO_SAMPLE_RATE", "24000"))
    AUDIO_CHANNELS: int = int(os.getenv("AUDIO_CHANNELS", "1"))
    AUDIO_SAMPLE_WIDTH: int = int(os.getenv("AUDIO_SAMPLE_WIDTH", "2"))
    
    # TTS Voice Configuration
    TTS_VOICE_NAME: str = os.getenv("TTS_VOICE_NAME", "Kore")
    
    # Model Names
    GEMINI_STT_MODEL: str = "gemini-2.5-pro"
    GEMINI_TTS_MODEL: str = "gemini-2.5-flash-preview-tts"
    GEMINI_LLM_MODEL: str = "gemini-2.5-flash"
    IMAGE_GENERATION_MODEL: str = "Qwen/Qwen-Image"
    IMAGE_EDIT_MODEL: str = "Qwen/Qwen-Image-Edit"
    
    # Google Scopes
    GOOGLE_SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    @classmethod
    def validate_settings(cls) -> bool:
        """Validate that all required settings are present"""
        required_settings = [
            cls.TELEGRAM_TOKEN,
            cls.GEMINI_API_KEY,
            cls.HUGGINGFACEHUB_API_TOKEN,
            cls.GOOGLE_CLIENT_ID,
            cls.GOOGLE_CLIENT_SECRET,
            cls.GOOGLE_PROJECT_ID
        ]
        
        missing_settings = []
        for i, setting in enumerate(required_settings):
            if not setting:
                setting_names = [
                    "TELEGRAM_TOKEN",
                    "GEMINI_API_KEY", 
                    "HUGGINGFACEHUB_API_TOKEN",
                    "GOOGLE_CLIENT_ID",
                    "GOOGLE_CLIENT_SECRET",
                    "GOOGLE_PROJECT_ID"
                ]
                missing_settings.append(setting_names[i])
        
        if missing_settings:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_settings)}")
        
        return True
    
    @classmethod
    def create_directories(cls) -> None:
        """Create necessary directories if they don't exist"""
        directories = [cls.TEMP_DIR, cls.LOGS_DIR]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

# Create settings instance
settings = Settings()

# Validate settings on import
try:
    settings.validate_settings()
    settings.create_directories()
    print("✅ Configuration loaded successfully")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    exit(1)