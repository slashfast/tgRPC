from aiogram import Router, F
from aiogram.filters.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from common import rpc
from common.api import fastest_fee
from common.envs import API
from handlers.core import command_start
from keyboards.common import start
from keyboards.manual import cancel, confirm


class Transfer(StatesGroup):
    address = State()
    amount = State()
    confirmation = State()


router = Router()


@router.message(F.text == 'Перевести')
async def transfer_handler(message: Message, state: FSMContext) -> None:
    await message.answer(
        text=f'Введите адрес',
        reply_markup=await cancel()
    )
    await state.set_state(Transfer.address)


@router.message(Transfer.address)
async def address_input_handler(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await cancel_handler(message, state)
    else:
        await state.update_data(address=message.text)
        await message.answer(f'Введите сумму')
        await state.set_state(Transfer.amount)


@router.message(Transfer.amount)
async def amount_input_handler(message: Message, state: FSMContext):
    if message.text == 'Отмена':
        await cancel_handler(message, state)
    else:
        await state.update_data(amount=message.text)
        data = await state.get_data()
        try:
            fee = await fastest_fee()
            unsigned_tx = await rpc.pay_to(data['address'], data['amount'], fee)
            await state.update_data(unsigned_transaction=unsigned_tx)
            await message.answer(
                f'Отправить ₿<b>{data["amount"]}</b> на адрес <b>{data["address"]}</b>?',
                reply_markup=await confirm(),
                parse_mode="HTML"
            )
            await state.set_state(Transfer.confirmation)
        except Exception as e:
            await state.set_state(state=None)
            await message.answer(text=str(e), reply_markup=await start(), parse_mode=None)


@router.message(Transfer.confirmation)
async def amount_input_handler(message: Message, state: FSMContext):
    if message.text == 'Да ✅':
        await state.update_data(confirmation=message.text)
        state_data = await state.get_data()
        try:
            signed_tx = await rpc.sign_tx(state_data['unsigned_transaction'])
            tx_id = await rpc.broadcast(signed_tx)
            await message.answer(
                f'Транзакция отправлена\n<b><a href="{API}/tx/{tx_id}">{tx_id}</a></b>',
                parse_mode='HTML', reply_markup=await start())
        except Exception as e:
            await message.answer(str(e), reply_markup=await start())

        await state.set_state(state=None)
    else:
        await cancel_handler(message, state)


async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(state=None)
    await command_start(message)
