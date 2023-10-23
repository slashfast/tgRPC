import asyncio

from aiogram.types import BotCommand

from handlers import auto, manual
from handlers.core import dp, bot


async def main():
    dp.include_routers(auto.router, manual.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота")
    ])

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
