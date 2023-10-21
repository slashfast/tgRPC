from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from keyboards.start import get_start

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        text=f"Здравствуйте, {hbold(message.from_user.full_name)}!\nИспользуйте клавиатуру для навигации.",
        reply_markup=get_start()
    )
