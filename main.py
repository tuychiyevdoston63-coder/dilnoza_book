import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config import settings
from database import init_db
from handlers import router

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Jadvallarni avtomatik yaratish
    await init_db()
    
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    
    dp.include_router(router)
    
    logging.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi!")
