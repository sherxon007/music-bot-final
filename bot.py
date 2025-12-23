"""Main bot entry point."""
import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Config
from db import init_db
from handlers import get_routers
from utils import logger


async def main():
    """Initialize and start the bot."""
    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")
    
    # Create bot instance
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Create dispatcher
    dp = Dispatcher()
    
    # Register all routers
    for router in get_routers():
        dp.include_router(router)
    
    logger.info("Bot started successfully!")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Set default commands
        from aiogram.types import BotCommand
        await bot.set_my_commands([
            BotCommand(command="start", description="Botni ishga tushirish"),
            BotCommand(command="search", description="Musiqa qidirish"),
            BotCommand(command="shazam", description="Musiqani aniqlash"),
            BotCommand(command="help", description="Yordam"),
        ])

        # Start polling
        from keep_alive import start_web_server
        
        # Start polling and web server (needed for Render)
        await asyncio.gather(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
            start_web_server()
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
