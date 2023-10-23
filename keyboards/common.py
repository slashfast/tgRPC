from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def start():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Автоматические переводы')],
            [KeyboardButton(text='Перевести')]
        ],
        resize_keyboard=True
    )
