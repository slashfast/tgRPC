from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def menu() -> InlineKeyboardMarkup | None:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Начать", callback_data='start')],
            [InlineKeyboardButton(text="📝 Добавить адреса", callback_data='update_addresses')],
            [InlineKeyboardButton(text="🗑️ Удалить все адреса", callback_data='clear_addresses')],
            [InlineKeyboardButton(text="↔️ Изменить диапазон", callback_data='update_amount_range')],
        ],
    )


async def stop(seconds) -> InlineKeyboardMarkup | None:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f'⛔ Остановить ({seconds})', callback_data='stop_auto_transferring')]
        ],
    )


async def cancel() -> InlineKeyboardMarkup | None:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
        ],
    )
