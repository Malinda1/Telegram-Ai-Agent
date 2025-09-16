# /Users/pasindumalinda/Personal_AI_Agent/telegram-ai-agent/test.py

import asyncio
from bot_handlers.bot import run_telegram_bot
from config.logging_config import get_logger

logger = get_logger("test_bot")

async def test_bot():
    try:
        logger.info("Starting test for Telegram bot...")
        # Run bot
        await run_telegram_bot()
    except Exception as e:
        logger.error(f"Error during bot test: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_bot())
