import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from handlers.user_private import user_private_router
from handlers.admin_private import admin_router
from middlewares.db import DataBaseSession

load_dotenv()

from database.engine import create_db, session_maker


bot = Bot(
    token=os.getenv("TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
bot.my_admins_list = list(map(int, os.getenv('ADMIN_LS').split(',')))


dp = Dispatcher()


dp.include_router(user_private_router)
dp.include_router(admin_router)


async def on_startup():
    await create_db()

async def on_shutdown():
    print("бот лег")

async def main() -> None:
    """Фунция для запуска бота"""
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_poll=session_maker))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == '__main__':
    asyncio.run(main())
