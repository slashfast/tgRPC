import logging
from decimal import Decimal

import simplejson as json
from simplejson.errors import JSONDecodeError

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from common.envs import TOKEN, USER_ID, DATA_PATH
from common.storage import Storage
from keyboards.common import start

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.basicConfig(level=logging.DEBUG, handlers=[handler])

try:
    with open(DATA_PATH, 'r') as file:
        file = json.load(file, parse_float=Decimal)
        db = Storage(DATA_PATH, file['addresses'], file['range'])
except (FileNotFoundError, JSONDecodeError) as e:
    with open(DATA_PATH, 'w') as file:
        json.dump(obj=Storage.to_dict(), fp=file, indent=2)
        db = Storage(DATA_PATH)


# except JSONDecodeError as e:
#     logging.info(f'{repr(e)} in {DATA_PATH}')


@dp.message(F.from_user.id != USER_ID)
async def whitelist(_):
    pass


@dp.message(CommandStart())
async def command_start(message: Message) -> None:
    await message.answer(
        text=f'Здравствуйте, <b>{message.from_user.full_name}</b>!'
             f'\nИспользуйте клавиатуру для навигации',
        reply_markup=await start()
    )
