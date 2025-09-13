import asyncio
import uvicorn
from concurrent.futures import ThreadPoolExecutor
import signal
import sys
import time

from config.settings import settings
from config.logging_config import get_logger
from telegram.bot import run_telegram_bot
from routes.router import app

logger = get_logger('main')

class AIAgentServer:
    """Main server class that runs both FastAPI and Telegram bot"""
    
    def __init__(self):
        """Initialize the AI Agent Server"""
        self.telegram_task = None
        self.fastapi_task = None
        self.running = False
        logger.info("AIAgentServer initialized")
    
    async def start_fastapi_server(self):
        """Start FastAPI server"""
        try:
            logger.info(f"🚀 Starting FastAPI server on {settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}")
            
            config = uvicorn.Config(
                app,
                host=settings.FASTAPI_HOST,
                port=settings.FASTAPI_PORT,
                log_level="info",
                reload=False,
                access_log=True
            )
            
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            logger.error(f"❌ Error starting FastAPI server: {str(e)}")
            raise e
    
    async def start_telegram_bot(self):
        """Start Telegram bot"""
        try:
            logger.info("🤖 Starting Telegram bot...")
            await run_telegram_bot()
            
        except Exception as e:
            logger.error(f"❌ Error starting Telegram bot: {str(e)}")
            raise e
    
    async def start_services(self):
        """Start all services concurrently"""
        try:
            logger.info("🚀 Starting AI Agent services...")
            self.running = True
            
            # Create tasks for both services
            self.telegram_task = asyncio.create_task(
                self.start_telegram_bot(),
                name="telegram_bot"
            )
            
            self.fastapi_task = asyncio.create_task(
                self.start_fastapi_server(),
                name="fastapi_server"
            )
            
            # Wait for both tasks to complete
            await asyncio.gather(
                self.telegram_task,
                self.fastapi_task,
                return_exceptions=True
            )
            
        except Exception as e:
            logger.error(f"❌ Error running services: {str(e)}")
            await self.stop_services()
            raise e
    
    async def stop_services(self):
        """Stop all services"""
        try:
            logger.info("🛑 Stopping AI Agent services...")
            self.running = False
            
            # Cancel tasks if they're running
            if self.telegram_task and not self.telegram_task.done():
                self.telegram_task.cancel()
                try:
                    await self.telegram_task
                except asyncio.CancelledError:
                    logger.info("✅ Telegram bot task cancelled")
            
            if self.fastapi_task and not self.fastapi_task.done():
                self.fastapi_task.cancel()
                try:
                    await self.fastapi_task
                except asyncio.CancelledError:
                    logger.info("✅ FastAPI server task cancelled")
            
            # Perform cleanup
            await self.cleanup()
            
            logger.info("✅ All services stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping services: {str(e)}")
    
    async def cleanup(self):
        """Perform cleanup operations"""
        try:
            logger.info("🧹 Performing cleanup...")
            
            # Clean up temporary files
            from utils.file_handler import file_handler
            cleanup_result = file_handler.cleanup_old_files(max_age_hours=0)
            
            if cleanup_result["success"]:
                logger.info(f"✅ Cleanup complete: {cleanup_result['deleted_count']} files deleted")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}")
            asyncio.create_task(self.stop_services())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

def validate_environment():
    """Validate environment variables and configuration"""
    try:
        logger.info("🔍 Validating environment configuration...")
        
        # Validate settings
        settings.validate_settings()
        
        # Check if required directories exist
        settings.create_directories()
        
        logger.info("✅ Environment validation complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ Environment validation failed: {str(e)}")
        return False

def display_startup_info():
    """Display startup information"""
    logger.info("=" * 80)
    logger.info("🤖 TELEGRAM AI AGENT SERVER")
    logger.info("=" * 80)
    logger.info(f"📱 Telegram Bot: {'✅ Configured' if settings.TELEGRAM_TOKEN else '❌ Missing Token'}")
    logger.info(f"🧠 Gemini AI: {'✅ Configured' if settings.GEMINI_API_KEY else '❌ Missing API Key'}")
    logger.info(f"🖼️  Image Generation: {'✅ Configured' if settings.HUGGINGFACEHUB_API_TOKEN else '❌ Missing Token'}")
    logger.info(f"📧 Google Services: {'✅ Configured' if settings.GOOGLE_CLIENT_ID else '❌ Missing Credentials'}")
    logger.info(f"🌐 FastAPI Server: {settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}")
    logger.info(f"📁 Temp Directory: {settings.TEMP_DIR}")
    logger.info(f"📋 Logs Directory: {settings.LOGS_DIR}")
    logger.info("=" * 80)
    logger.info("🚀 Starting services...")
    logger.info("=" * 80)

async def run_server():
    """Main function to run the server"""
    try:
        # Display startup information
        display_startup_info()
        
        # Validate environment
        if not validate_environment():
            logger.error("❌ Environment validation failed. Exiting.")
            return False
        
        # Create and start server
        server = AIAgentServer()
        server.setup_signal_handlers()
        
        # Start all services
        await server.start_services()
        
        return True
        
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
        return True
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        return False

def main():
    """Main entry point"""
    try:
        # Set up event loop policy for Windows
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Run the server
        success = asyncio.run(run_server())
        
        if success:
            logger.info("👋 Server shutdown complete")
            sys.exit(0)
        else:
            logger.error("❌ Server failed to start")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {str(e)}")
        sys.exit(1)

# Alternative functions for running services individually
async def run_telegram_only():
    """Run only the Telegram bot"""
    try:
        logger.info("🤖 Starting Telegram bot only...")
        
        if not validate_environment():
            return False
        
        await run_telegram_bot()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error running Telegram bot: {str(e)}")
        return False

async def run_fastapi_only():
    """Run only the FastAPI server"""
    try:
        logger.info("🌐 Starting FastAPI server only...")
        
        if not validate_environment():
            return False
        
        server = AIAgentServer()
        await server.start_fastapi_server()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error running FastAPI server: {str(e)}")
        return False

def run_development_server():
    """Run server in development mode with auto-reload"""
    try:
        logger.info("🔧 Starting development server...")
        
        # Run FastAPI with auto-reload
        uvicorn.run(
            "routes.router:app",
            host=settings.FASTAPI_HOST,
            port=settings.FASTAPI_PORT,
            reload=True,
            log_level="debug"
        )
        
    except Exception as e:
        logger.error(f"❌ Error running development server: {str(e)}")

if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "telegram":
            # Run only Telegram bot
            asyncio.run(run_telegram_only())
        elif command == "fastapi":
            # Run only FastAPI server
            asyncio.run(run_fastapi_only())
        elif command == "dev":
            # Run development server
            run_development_server()
        elif command == "help":
            print("""
Telegram AI Agent Server

Usage:
    python main.py           - Run both Telegram bot and FastAPI server
    python main.py telegram  - Run only Telegram bot
    python main.py fastapi   - Run only FastAPI server
    python main.py dev       - Run FastAPI in development mode (auto-reload)
    python main.py help      - Show this help message

Environment Variables Required:
    TELEGRAM_TOKEN              - Telegram bot token
    GEMINI_API_KEY             - Google Gemini API key
    HUGGINGFACEHUB_API_TOKEN   - Hugging Face API token
    GOOGLE_CLIENT_ID           - Google OAuth client ID
    GOOGLE_CLIENT_SECRET       - Google OAuth client secret
    GOOGLE_PROJECT_ID          - Google Cloud project ID
            """)
        else:
            print(f"Unknown command: {command}")
            print("Use 'python main.py help' for available commands")
    else:
        # Run full server (default)
        main()