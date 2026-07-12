import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from aiohttp import web

from config import settings
from handlers import router
from database import init_db

# Render taqdim etadigan PORT-ni aniqlaymiz (agar bo'lmasa, 8080)
PORT = int(os.environ.get("PORT", 8080))

# Cron-job yoki Render tekshiruvi uchun juda qisqa javob qaytaruvchi funksiya
async def handle_cron_check(request):
    # 'Output too large' xatosini oldini olish uchun shunchaki qisqa 'OK' qaytaramiz
    return web.Response(text="OK", content_type="text/plain")

async def main():
    # 1. Loggingni sozlash (Bot xatolarini logda ko'rish uchun)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    
    # 2. Ma'lumotlar bazasini ishga tushirish (Jadvallarni yaratish)
    await init_db()
    
    # 3. Bot va Dispatcher-ni sozlash
    # 3. Bot va Dispatcher-ni sozlash (Tokenni xavfsiz aniqlash)
    token = getattr(settings, 'bot_token', None) or getattr(settings, 'BOT_TOKEN', None) or os.environ.get("BOT_TOKEN")
    
    if not token:
        raise ValueError("❌ XATOLIK: Bot token topilmadi! config.py yoki Render Environment Variables-ni tekshiring.")
        
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    
    # 4. Kichik va soxta Web Serverni yaratish (Render va Cron-job uchun)
    app = web.Application()
    app.router.add_get('/', handle_cron_check)  # Asosiy sahifaga kirganda faqat 'OK' chiqadi
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    
    # Veb-serverni orqa fonda asinxron ishga tushiramiz
    asyncio.create_task(site.start())
    logging.info(f"======= WEB SERVER STARTED ON PORT {PORT} FOR CRON/RENDER =======")
    
    # 5. Botni Polling (tinimsiz tekshirish) rejimida yurgizamiz
    try:
        # Eski kelib qolgan xabarlarga javob bermasligi uchun webhooklarni o'chiramiz
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
