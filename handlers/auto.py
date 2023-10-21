import asyncio
import json
import secrets

import aiogram.types
from aiogram import Router, F
import aiohttp
from aiogram.types import Message, CallbackQuery
from keyboards.auto import get_auto
from aiogram.filters.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from handlers.manual import call, WALLET_PASSWORD, ElectrumRPCError


class InvalidSeparator(Exception):
    pass


class Auto(StatesGroup):
    addresses_list = State()
    amount_range = State()
    auto_transferring = State()
    current_tx_state = State()


router = Router()
config_path = './config.toml'


async def auto_transferring(callback: CallbackQuery, addresses: list[str],
                            amount_range: list) -> None:
    async with aiohttp.ClientSession() as session:
        for count, address in enumerate(addresses):
            async with session.get('https://mempool.space/api/v1/fees/recommended') as fees:
                fee = json.loads(await fees.text())['fastestFee']
            random_value = secrets.SystemRandom().uniform(amount_range[0], amount_range[1])
            try:
                unsigned_tx = await call(
                    method='payto',
                    params={
                        'destination': address,
                        'amount': random_value,
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
                tx_id = await call(
                    method='broadcast',
                    params={
                        'tx': signed_tx
                    }
                )
                await callback.message.answer(
                    text=f'Транзакция отправлена\n'
                         f'<b><a href="https://mempool.space/tx/{tx_id}">{tx_id}</a></b>'
                         f'\n{count + 1} из {len(addresses)}',
                    parse_mode='HTML'
                )
            except ElectrumRPCError as e:
                await callback.message.answer(str(e))
            tx_status = False
            while not tx_status:
                async with session.get(
                        f'https://mempool.space/api/tx/{tx_id}/status') as tx_info:
                    tx_status = json.loads(await tx_info.text())['confirmed']
                    if tx_status:
                        break
                await asyncio.sleep(60)
            await callback.message.answer(
                text=f'Транзакция подтверждена\n'
                     f'<b><a href="https://mempool.space/tx/{tx_id}">{tx_id}</a></b>\n{count + 1} из {len(addresses)}',
                parse_mode='HTML'
            )


@router.message(F.text == "Автоматические переводы")
async def auto_main_handler(message: Message, state: FSMContext) -> None:
    # Проверка диалога
    if 'auto_transferring' not in await state.get_data():
        await state.set_state(Auto.auto_transferring)
        await state.update_data(auto_transferring={'running': False})
        await state.set_state(state=None)

    user_state = await state.get_data()
    addresses_list = user_state['addresses_list'] if 'addresses_list' in user_state else 'не задан'
    amount_range = user_state['amount_range'] if 'amount_range' in user_state else 'не задан'

    auto_transferring_menu_msg = await message.answer(
        text=f'📝 Список кошельков:\n{addresses_list}\n\n'
             f'↔️ Диапазон:\n{amount_range}',
        reply_markup=get_auto(state=user_state)
    )

    if user_state['auto_transferring']['running']:
        for i in reversed(range(5)):
            await auto_transferring_menu_msg.edit_reply_markup(reply_markup=aiogram.types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        aiogram.types.InlineKeyboardButton(
                            text=f'⛔ Остановить ({i + 1})',
                            callback_data='stop_auto_transferring'
                        )
                    ]
                ]
            ))
            await asyncio.sleep(1)

        await auto_transferring_menu_msg.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data == "run_auto_transferring")
async def start_auto(callback: CallbackQuery, state: FSMContext):
    user_state = await state.get_data()

    if 'addresses_list' in user_state:
        if 'amount_range' in user_state:
            await state.set_state(Auto.auto_transferring)
            auto_transferring_task = asyncio.create_task(
                auto_transferring(
                    callback,
                    user_state['addresses_list'].split('\n'),
                    [float(e) for e in user_state['amount_range'].split()]
                ),
                name='auto_transferring_task'
            )

            await state.update_data(auto_transferring={'running': True})
            await callback.message.answer('✅ Рассылка запущена!')
            await callback.answer()
            await auto_transferring_task
            await state.update_data(auto_transferring={'running': False})
            await callback.message.answer('✅ Рассылка завершена!')
        else:
            await callback.answer('Диапазон не задан!')
    else:
        await callback.answer('Список адресов не задан!')


@router.callback_query(F.data == "stop_auto_transferring")
async def start_auto(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Auto.auto_transferring)
    await state.update_data(auto_transferring={'running': False})
    task, = [task for task in asyncio.all_tasks() if task.get_name() == 'auto_transferring_task']
    task.cancel()
    await callback.message.answer('✅ Рассылка остановлена!')
    await callback.answer()


@router.callback_query(F.data == "update_addresses")
async def update_addresses_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text='📝 Отправьте список адресов в чат',
        reply_markup=aiogram.types.InlineKeyboardMarkup(
            inline_keyboard=[
                [aiogram.types.InlineKeyboardButton(text="< Назад", callback_data="back")]
            ]
        ))
    await state.set_state(Auto.addresses_list)


@router.message(Auto.addresses_list)
async def update_addresses_list_state(message: Message, state: FSMContext):
    if message.text:
        await state.update_data(addresses_list=message.text)
        await auto_main_handler(message, state)
        await state.set_state(state=None)


@router.callback_query(F.data == "back")
async def back(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(state=None)
    await callback.answer()
    await auto_main_handler(callback.message, state)


@router.callback_query(F.data == "update_amount_range")
async def update_amount_range_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text='↔️ Отправьте диапазон, разделенный пробелом',
        reply_markup=aiogram.types.InlineKeyboardMarkup(
            inline_keyboard=[
                [aiogram.types.InlineKeyboardButton(text="< Назад", callback_data="back")]
            ]
        ))
    await state.set_state(Auto.amount_range)
    await callback.answer()


@router.message(Auto.amount_range)
async def update_amount_range_state(message: Message, state: FSMContext):
    if message.text:
        try:
            if len(message.text.split()) < 2:
                raise InvalidSeparator
            await state.update_data(amount_range=message.text)
            await auto_main_handler(message, state)
            await state.set_state(state=None)
        except InvalidSeparator:
            await message.answer('Введите диапазон, разделенный пробелом!')
