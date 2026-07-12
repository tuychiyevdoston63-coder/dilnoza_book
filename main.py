import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from app.config import settings
from app.database import init_db
from app.handlers import router

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Ma'lumotlar bazasini initsializatsiya qilish (Jadvallarni yaratish)
    await init_db()
    
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    
    # Routerlarni ulash
    dp.include_router(router)
    
    logging.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi!")
