import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.error import TelegramError
from telegram import Update
from config.settings import settings
from config.logging_config import get_logger
# Fixed import path
from bot_handlers.telegram_handlers import telegram_handlers

logger = get_logger('telegram_bot')

class TelegramBot:
    """Main Telegram Bot class"""
    
    def __init__(self):
        """Initialize Telegram Bot"""
        self.token = settings.TELEGRAM_TOKEN
        self.application = None
        self.is_running = False
        logger.info("TelegramBot initialized")
    
    def setup_handlers(self):
        """Setup all message handlers"""
        try:
            # Command handlers
            self.application.add_handler(
                CommandHandler("start", telegram_handlers.start_handler)
            )
            
            self.application.add_handler(
                CommandHandler("help", telegram_handlers.help_handler)
            )
            
            self.application.add_handler(
                CommandHandler("cleanup", telegram_handlers.cleanup_handler)
            )
            
            # Message handlers
            self.application.add_handler(
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    telegram_handlers.text_message_handler
                )
            )
            
            self.application.add_handler(
                MessageHandler(
                    filters.VOICE,
                    telegram_handlers.voice_message_handler
                )
            )
            
            self.application.add_handler(
                MessageHandler(
                    filters.AUDIO,
                    telegram_handlers.voice_message_handler
                )
            )
            
            self.application.add_handler(
                MessageHandler(
                    filters.PHOTO,
                    telegram_handlers.photo_message_handler
                )
            )
            
            self.application.add_handler(
                MessageHandler(
                    filters.Document.ALL,
                    telegram_handlers.document_message_handler
                )
            )
            
            # Unknown command handler - should be last
            self.application.add_handler(
                MessageHandler(
                    filters.COMMAND,
                    telegram_handlers.unknown_handler
                )
            )
            
            # Error handler
            self.application.add_error_handler(telegram_handlers.error_handler)
            
            logger.info("✅ All handlers setup successfully")
            
        except Exception as e:
            logger.error(f"Error setting up handlers: {str(e)}")
            raise e
    
    async def post_init(self, application):
        """Post initialization setup"""
        try:
            bot_info = await application.bot.get_me()
            logger.info(f"✅ Bot initialized: @{bot_info.username} ({bot_info.first_name})")
            
            # Set bot commands for better UX
            from telegram import BotCommand
            
            commands = [
                BotCommand("start", "Start the bot and get welcome message"),
                BotCommand("help", "Show help and available commands"),
                BotCommand("cleanup", "Clean up temporary files (admin only)")
            ]
            
            await application.bot.set_my_commands(commands)
            logger.info("✅ Bot commands set successfully")
            
        except Exception as e:
            logger.error(f"Error in post initialization: {str(e)}")
    
    async def post_shutdown(self, application):
        """Post shutdown cleanup"""
        try:
            logger.info("🛑 Bot shutting down...")
            
            # FIXED: Only clean up temporary files, preserve Google auth token
            from utils.file_handler import file_handler
            import os
            from config.settings import settings
            
            # Get the Google auth token file path
            token_file = os.path.join(settings.TEMP_DIR, 'token.pickle')
            
            # Perform selective cleanup - exclude Google auth token
            cleanup_result = file_handler.cleanup_old_files(
                max_age_hours=0,  # Clean all temp files
                exclude_files=[token_file, 'token.pickle']  # But exclude Google auth token
            )
            
            if cleanup_result["success"]:
                logger.info(f"✅ Cleanup on shutdown: {cleanup_result['deleted_count']} files deleted")
                logger.info("🔐 Google auth token preserved for next session")
            
        except Exception as e:
            logger.error(f"Error in post shutdown: {str(e)}")
    
    def create_application(self):
        """Create the Telegram application"""
        try:
            # Build application - remove timeout parameters that cause issues
            self.application = (
                ApplicationBuilder()
                .token(self.token)
                .post_init(self.post_init)
                .post_shutdown(self.post_shutdown)
                .concurrent_updates(True)  # Enable concurrent message processing
                .build()
            )
            
            # Setup handlers
            self.setup_handlers()
            
            logger.info("✅ Telegram application created successfully")
            return self.application
            
        except Exception as e:
            logger.error(f"Error creating Telegram application: {str(e)}")
            raise e
    
    async def start_polling(self):
        """Start bot polling"""
        try:
            if not self.application:
                self.create_application()
            
            logger.info("🚀 Starting Telegram bot polling...")
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            
            # Start polling with minimal parameters
            await self.application.updater.start_polling(
                poll_interval=1.0,
                bootstrap_retries=-1
            )
            
            self.is_running = True
            logger.info("✅ Telegram bot is running and listening for messages...")
            
            # Keep the bot running
            while self.is_running:
                await asyncio.sleep(1)
                
        except TelegramError as e:
            logger.error(f"Telegram API error: {str(e)}")
            self.is_running = False
            raise e
        except Exception as e:
            logger.error(f"Error starting bot: {str(e)}")
            self.is_running = False
            raise e
        finally:
            await self.stop()
    
    async def start_webhook(self, webhook_url: str, port: int = 8443):
        """Start bot with webhook (for production)"""
        try:
            if not self.application:
                self.create_application()
            
            logger.info(f"🚀 Starting Telegram bot webhook on {webhook_url}:{port}")
            
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_webhook(
                listen="0.0.0.0",
                port=port,
                url_path=self.token,
                webhook_url=f"{webhook_url}/{self.token}"
            )
            
            self.is_running = True
            logger.info("✅ Telegram bot webhook is running...")
            
            # Keep the bot running
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting webhook: {str(e)}")
            self.is_running = False
            raise e
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the bot"""
        try:
            if self.application and self.is_running:
                logger.info("🛑 Stopping Telegram bot...")
                
                self.is_running = False
                
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                
                logger.info("✅ Telegram bot stopped successfully")
                
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")
    
    async def send_message(self, chat_id: int, text: str, **kwargs):
        """Send a message to a specific chat"""
        try:
            if not self.application:
                logger.error("Bot not initialized")
                return False
            
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=text,
                **kwargs
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    async def send_audio(self, chat_id: int, audio_path: str, **kwargs):
        """Send an audio file to a specific chat"""
        try:
            if not self.application:
                logger.error("Bot not initialized")
                return False
            
            with open(audio_path, 'rb') as audio_file:
                await self.application.bot.send_audio(
                    chat_id=chat_id,
                    audio=audio_file,
                    **kwargs
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending audio: {str(e)}")
            return False
    
    async def send_photo(self, chat_id: int, photo_path: str, caption: str = None, **kwargs):
        """Send a photo to a specific chat"""
        try:
            if not self.application:
                logger.error("Bot not initialized")
                return False
            
            with open(photo_path, 'rb') as photo_file:
                await self.application.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                    caption=caption,
                    **kwargs
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending photo: {str(e)}")
            return False
    
    def get_bot_info(self):
        """Get information about the bot"""
        if self.application:
            return {
                "is_running": self.is_running,
                "token_preview": f"{self.token[:10]}..." if self.token else None
            }
        return {"is_running": False}

# Create global bot instance
telegram_bot = TelegramBot()

# Main function to run the bot
async def run_telegram_bot():
    """Run the Telegram bot"""
    try:
        logger.info("🤖 Initializing Telegram Bot...")
        
        # Validate token
        if not settings.TELEGRAM_TOKEN:
            logger.error("❌ TELEGRAM_TOKEN not found in environment variables")
            return
        
        logger.info(f"📱 Using Telegram token: {settings.TELEGRAM_TOKEN[:10]}...")
        
        # Start the bot
        await telegram_bot.start_polling()
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error running bot: {str(e)}")
        raise e

if __name__ == "__main__":
    # Run the bot if this file is executed directly
    asyncio.run(run_telegram_bot())