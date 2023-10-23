from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def confirm() -> ReplyKeyboardMarkup | None:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Нет ❌')],
            [KeyboardButton(text='Да ✅')]
        ],
        resize_keyboard=True
    )


async def cancel() -> ReplyKeyboardMarkup | None:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )
