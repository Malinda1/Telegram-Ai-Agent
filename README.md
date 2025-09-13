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
3. Add to your `.env` file

#### Hugging Face API Token
1. Go to [Hugging Face](https://huggingface.co/)
2. Create account and go to Settings > Access Tokens
3. Create a new token with write permissions
4. Add to your `.env` file

#### Google Cloud Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Calendar API and Gmail API
4. Go to "Credentials" > "Create Credentials" > "OAuth 2.0 Client ID"
5. Configure consent screen
6. Download credentials and add client ID, secret, and project ID to `.env`

## 📱 Usage Examples

### Calendar Operations
```
User: "Create a meeting tomorrow at 9 AM with John"
Bot: "I'll create a meeting for tomorrow at 9:00 AM. Could you provide:
- Event title/description
- Duration (how long will it last?)
- John's email for invitation?"

User: "Show my events for today"
Bot: "Here are your events for today:
• Team Meeting - 09:00 AM
• Lunch with Sarah - 12:30 PM
• Project Review - 03:00 PM"
```

### Email Operations
```
User: "Send email to john@company.com about the quarterly review"
Bot: "I'll help you send an email to john@company.com about the quarterly review. 
Here's the professional email I've created:

Subject: Quarterly Review Discussion
[Email content...]

Should I send this email?"
```

### Image Generation
```
User: "Generate an image of a sunset over mountains"
Bot: "🎨 I've created an image based on: 'sunset over mountains'
Image saved and ready to send!"
[Image attached]
```

### Voice Messages
```
User: [Sends voice message: "Create an event for Friday at 2 PM"]
Bot: [Responds with both text and audio]
"I'll create an event for Friday at 2:00 PM. What should the event be called?"
```

## 🔧 API Endpoints

The FastAPI server provides RESTful endpoints:

### Message Processing
- `POST /message` - Process text message
- `POST /message/audio` - Process audio message

### Calendar
- `POST /calendar/create` - Create calendar event
- `GET /calendar/events` - Get calendar events

### Email
- `POST /email/send` - Send email
- `GET /email/list` - List emails

### Images
- `POST /image/generate` - Generate image
- `POST /image/edit` - Edit image

### Utilities
- `GET /health` - Health check
- `GET /stats` - System statistics
- `POST /cleanup` - Clean temporary files

## 🏃‍♂️ Running in Production

### Using Docker (Recommended)

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   CMD ["python", "main.py"]
   ```

2. **Build and run**
   ```bash
   docker build -t telegram-ai-agent .
   docker run -d --env-file .env -p 8000:8000 telegram-ai-agent
   ```

### Using Systemd Service

1. **Create service file**
   ```bash
   sudo nano /etc/systemd/system/telegram-ai-agent.service
   ```

2. **Add service configuration**
   ```ini
   [Unit]
   Description=Telegram AI Agent
   After=network.target
   
   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/path/to/telegram-ai-agent
   Environment=PATH=/path/to/venv/bin
   ExecStart=/path/to/venv/bin/python main.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable telegram-ai-agent
   sudo systemctl start telegram-ai-agent
   ```

## 📊 Monitoring & Logging

### Log Files
- `logs/telegram_agent.log` - Main application logs
- `logs/telegram_bot.log` - Telegram bot specific logs
- `logs/calendar_service.log` - Calendar operations
- `logs/email_service.log` - Email operations
- `logs/speech_service.log` - Speech processing
- `logs/image_service.log` - Image operations
- `logs/errors.log` - Error logs only

### Health Monitoring
```bash
# Check health via API
curl http://localhost:8000/health

# Check system stats
curl http://localhost:8000/stats

# View logs
tail -f logs/telegram_agent.log
```

## 🛡️ Security Considerations

### API Keys & Credentials
- Never commit API keys to version control
- Use environment variables for all sensitive data
- Rotate API keys regularly
- Use strong, unique passwords

### User Authentication
- Implement user verification for admin commands
- Add rate limiting for API endpoints
- Validate all user inputs
- Sanitize file uploads

### Network Security
- Use HTTPS in production
- Implement proper firewall rules
- Use VPN for sensitive deployments
- Monitor for unusual traffic patterns

## 🐛 Troubleshooting

### Common Issues

#### "TELEGRAM_TOKEN not found"
- Check your `.env` file exists and contains the token
- Ensure no spaces around the `=` sign
- Verify token is valid with [@BotFather](https://t.me/botfather)

#### "Authentication error" for Google services
- Verify Google Cloud project is set up correctly
- Check Calendar and Gmail APIs are enabled
- Ensure OAuth consent screen is configured
- Run the initial authentication flow

#### "Audio processing failed"
- Check audio file format is supported
- Verify file size is under 25MB
- Ensure Gemini API key is valid
- Check internet connection

#### "Image generation failed"  
- Verify Hugging Face API token is valid
- Check token has write permissions
- Ensure description doesn't contain inappropriate content
- Monitor API rate limits

### Debug Mode
```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
python main.py

# Check specific service logs
tail -f logs/telegram_bot.log
tail -f logs/errors.log
```

### Performance Issues
```bash
# Clean up temporary files
curl -X POST http://localhost:8000/cleanup

# Check system resources
curl http://localhost:8000/stats

# Monitor file system usage
du -sh temp/ logs/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Format code
black .
isort .

# Lint code
flake8 .
mypy .
```

## 📚 Documentation

### Code Structure
- **Core Module**: Main AI logic and service coordination
- **Services**: External API integrations (Google, Hugging Face, etc.)
- **Telegram**: Bot interface and message handling
- **Utils**: Helper functions and utilities
- **Config**: Configuration management and logging

### Key Classes
- `AIAgentBrain`: Main coordination logic
- `LLMHandler`: Gemini AI integration
- `CalendarService`: Google Calendar operations
- `EmailService`: Gmail operations
- `ImageGenerationService`: Image creation
- `ImageEditingService`: Image modification
- `TelegramBot`: Bot interface

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Google Gemini](https://gemini.google.com/) for AI capabilities
- [Hugging Face](https://huggingface.co/) for image generation models
- [python-telegram-bot](https://python-telegram-bot.org/) for Telegram integration
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

## 📞 Support

- Create an [issue](https://github.com/your-repo/issues) for bugs
- Join our [discussion](https://github.com/your-repo/discussions) for questions
- Check the [wiki](https://github.com/your-repo/wiki) for detailed guides

---

**Made with ❤️ by [Your Name]**

*This AI agent represents the future of conversational productivity tools, bringing together calendar management, email automation, and creative image generation in one intelligent assistant.*