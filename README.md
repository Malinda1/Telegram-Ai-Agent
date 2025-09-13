# Telegram AI Agent

A powerful AI-powered Telegram bot that integrates with Google Calendar, Gmail, and provides image generation/editing capabilities. The bot can process both text and voice messages and provides audio responses.

## 🌟 Features

### 📅 Calendar Management
- Create, update, and delete calendar events
- View upcoming events
- Send meeting reminders via email
- Natural language date/time parsing

### 📧 Email Operations  
- Send professional emails
- Read and organize inbox
- Create draft emails
- Automated meeting reminders

### 🎨 Image Generation & Editing
- Generate images from text descriptions
- Edit existing images with text instructions
- Multiple artistic styles
- High-quality output

### 🎤 Voice & Audio Support
- Process voice messages (Speech-to-Text)
- Generate audio responses (Text-to-Speech)
- Multiple audio format support
- Real-time processing

### 🤖 AI Brain
- Powered by Google Gemini 2.5 Flash
- Intent recognition and context understanding
- Multi-step operation support
- Conversational interface

## 🏗️ Architecture

```
telegram-ai-agent/
├── config/                   # Configuration and logging
├── core/                     # Core AI functionality
├── services/                 # External service integrations
├── telegram/                 # Telegram bot handlers
├── auth/                     # Authentication services
├── utils/                    # Utility functions
├── routes/                   # FastAPI routes
├── temp/                     # Temporary files
└── logs/                     # Application logs
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Cloud Project with Calendar & Gmail APIs enabled
- Telegram Bot Token
- Gemini API Key
- Hugging Face API Token

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd telegram-ai-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and credentials
   ```

4. **Configure Google OAuth**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Calendar API and Gmail API
   - Create OAuth 2.0 credentials
   - Add credentials to `.env` file

5. **Run the application**
   ```bash
   # Run both Telegram bot and FastAPI server
   python main.py
   
   # Or run individually:
   python main.py telegram    # Telegram bot only
   python main.py fastapi     # FastAPI server only
   python main.py dev         # Development mode with auto-reload
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Telegram Configuration
TELEGRAM_TOKEN=your_telegram_bot_token

# Gemini AI Configuration  
GEMINI_API_KEY=your_gemini_api_key

# Hugging Face Configuration
HUGGINGFACEHUB_API_TOKEN=your_hf_token

# Google Cloud Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_PROJECT_ID=your_google_project_id

# Server Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# File Paths
TEMP_DIR=./temp
LOGS_DIR=./logs

# Audio Settings
AUDIO_SAMPLE_RATE=24000
AUDIO_CHANNELS=1
AUDIO_SAMPLE_WIDTH=2

# TTS Configuration
TTS_VOICE_NAME=Kore
```

### Getting API Keys

#### Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Get your bot token

#### Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create an API key
3. Ad