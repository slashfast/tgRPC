import json
import logging
import os
import time

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import aiohttp
from dotenv import load_dotenv
from handlers.start import command_start_handler

load_dotenv()

RPC_ENDPOINT = os.getenv('RPC_ENDPOINT')
RPC_PORT = os.getenv('RPC_PORT')
RPC_USER = os.getenv('RPC_USER')
RPC_PASSWORD = os.getenv('RPC_PASSWORD')
WALLET_PASSWORD = os.getenv('WALLET_PASSWORD')
RPC_URL = f'http://{RPC_USER}:{RPC_PASSWORD}@{RPC_ENDPOINT}:{RPC_PORT}/'


class ElectrumRPCError(Exception):
    pass


class Transfer(StatesGroup):
    address = State()
    amount = State()
    confirmation = State()


router = Router()


async def call(method, params):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    payload = {
        'jsonrpc': '2.0',
        'id': f'{method}_{int(time.time())}',
        'method': method,
        'params': params
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(RPC_URL, data=json.dumps(payload)) as response:
                response = json.loads(await response.text())
        except aiohttp.ClientConnectorError as e:
            print('Connection Error', str(e))

    if 'error' in response and response['error'] is not None:
        raise ElectrumRPCError(str(response['error']['message']))

    if "result" not in response:
        raise ElectrumRPCError('Missing result in the response')

    return response['result']


@router.message(F.text == 'Перевести')
async def transfer_handler(message: Message, state: FSMContext) -> None:
    await message.answer(
        text=f'Введите адрес',
        reply_markup=ReplyKeyboardMarkup(
            resize_keyboard=True,
            keyboard=[
                [KeyboardButton(text='Отмена')]
            ],
        ),
    )
    await state.set_state(Transfer.address)


@router.message(Transfer.address)
async def address_input_handler(message: Message, state: FSMContext):
    if message.text != 'Отмена':
        await state.update_data(address=message.text)
        await message.answer(f'Введите сумму')
        await state.set_state(Transfer.amount)
    else:
        await cancel_handler(message, state)


@router.message(Transfer.amount)
async def amount_input_handler(message: Message, state: FSMContext):
    match message.text:
        case 'Отмена':
            await cancel_handler(message, state)
        case _:
            await state.update_data(amount=message.text)
            async with aiohttp.ClientSession() as session:
                state_data = await state.get_data()
                async with session.get('https://mempool.space/api/v1/fees/recommended') as fees:
                    fee = json.loads(await fees.text())['economyFee']
            try:
                unsigned_tx = await call(
                    method='payto',
                    params={
                        'destination': state_data['address'],
                        'amount': state_data['amount'],
                        'password': WALLET_PASSWORD,
                        'feerate': fee,
                    })
                signed_tx = await call(
                    method='signtransaction',
                    params={
                        'tx': unsigned_tx,
                        'password': WALLET_PASSWORD
                    }
                )
                await state.set_state(state=None)
                await state.update_data(signed_transaction=signed_tx)
                await message.answer(
                    f'Отправить ₿<b>{state_data["amount"]}</b> на адрес <b>{state_data["address"]}</b>?',
                    reply_markup=ReplyKeyboardMarkup(
                        resize_keyboard=True,
                        keyboard=[
                            [KeyboardButton(text='Нет ❌')],
                            [KeyboardButton(text='Да ✅')]
                        ]
                    ),
                    parse_mode="HTML"
                )
                await state.set_state(Transfer.confirmation)
            except ElectrumRPCError as e:
                await message.answer(str(e))


@router.message(Transfer.confirmation)
async def amount_input_handler(message: Message, state: FSMContext):
    match message.text:
        case 'Нет ❌':
            await cancel_handler(message, state)
        case 'Да ✅':
            await state.update_data(confirmation=message.text)
            state_data = await state.get_data()
            try:
                tx_id = await call(
                    method='broadcast',
                    params={
                        'tx': state_data['signed_transaction']
                    }
                )
                await message.answer(
                    f'Транзакция отправлена\n<b><a href="https://mempool.space/tx/{tx_id}">{tx_id}</a></b>',
                    parse_mode='HTML')
            except ElectrumRPCError as e:
                await message.answer(str(e), reply_markup=ReplyKeyboardRemove())

            await cancel_handler(message, state)


async def cancel_handler(message: Message, state: FSMContext) -> None:
    if await state.get_state() is not None:
        await state.set_state(state=None)
        await command_start_handler(message)
