from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_auto(state) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if not state['auto_transferring']['running']:
        kb.button(text="▶️ Начать", callback_data='run_auto_transferring')
        kb.button(text="📝 Изменить список адресов", callback_data='update_addresses')
        kb.button(text="↔️ Изменить диапазон", callback_data='update_amount_range')
    kb.adjust(1)
    return kb.as_markup()
