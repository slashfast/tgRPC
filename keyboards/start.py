from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

buttons = {
    'auto': 'Автоматические переводы',
    'manual': 'Перевести'
}


def get_start() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=buttons.get('auto'))
    kb.button(text=buttons.get('manual'))
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)
