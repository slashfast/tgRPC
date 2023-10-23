import asyncio
import secrets
from decimal import Decimal

from aiogram import Router, F
from aiogram.filters.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from common import rpc
from common.api import confirmed, fastest_fee
from common.envs import API
from handlers.core import db
from keyboards import auto


class InvalidSeparator(Exception):
    pass


class Auto(StatesGroup):
    addresses = State()
    amount_range = State()


router = Router()


async def auto_transferring(callback: CallbackQuery, addresses: list[str],
                            amount_range: list[Decimal, Decimal]) -> None:
    try:
        total = len(addresses)
        for count, address in enumerate(addresses.copy()):
            random_value = Decimal(secrets.SystemRandom().uniform(float(amount_range[0]), float(amount_range[1])))
            unsigned_tx = await rpc.pay_to(address, random_value, await fastest_fee())
            signed_tx = await rpc.sign_tx(unsigned_tx)
            tx_id = await rpc.broadcast(signed_tx)
            await callback.message.answer(
                text=f'Транзакция отправлена\n'
                     f'<b><a href="{API}/tx/{tx_id}">{tx_id}</a></b>'
                     f'\n{count + 1} из {total}',
                parse_mode='HTML'
            )
            await db.pop_address()
            db.save()
            tx_status = False
            while not tx_status:
                tx_status = await confirmed(tx_id)
                if tx_status:
                    break
                else:
                    await asyncio.sleep(60)

            await callback.message.answer(
                text=f'Транзакция подтверждена\n'
                     f'<b><a href="{API}/tx/{tx_id}">{tx_id}</a></b>\n{count + 1} из {total}',
                parse_mode='HTML'
            )

    except Exception as e:
        await callback.message.answer(repr(e) + f' {e.__traceback__.tb_lineno}')


async def menu_text():
    addresses = db.addresses
    if len(addresses) > 5:
        addresses = '\n'.join(addresses[:2]) + '\n...\n' + '\n'.join(addresses[-2:])
    else:
        addresses = '\n'.join(addresses) if addresses else 'не задан'
    amount_range = f'₿{db.range[0]} - ₿{db.range[1]}' if db.range else 'не задан'
    return f'📝 Список адресов ({len(db.addresses)}):\n{addresses}\n\n↔️ Диапазон:\n{amount_range}'


@router.message(F.text == 'Автоматические переводы')
async def menu(message: Message, state: FSMContext, callback: CallbackQuery | None = None) -> None:
    try:
        data = await state.get_data()

        if callback:
            await callback.answer()
            auto_transferring_menu_msg = await callback.message.edit_text(
                text=await menu_text(),
                reply_markup=await auto.menu() if not data.get('running') else None
            )
        else:
            auto_transferring_menu_msg = await message.answer(
                text=await menu_text(),
                reply_markup=await auto.menu() if not data.get('running') else None
            )

        if data.get('running'):
            for i in reversed(range(5)):
                await auto_transferring_menu_msg.edit_reply_markup(reply_markup=await auto.stop(i + 1))
                await asyncio.sleep(1)

            await auto_transferring_menu_msg.edit_reply_markup(reply_markup=None)
    except AttributeError as e:
        if callback:
            message = callback.message
        await message.answer(str(e))


@router.callback_query(F.data == 'start')
async def start(callback: CallbackQuery, state: FSMContext):
    try:
        if len(db.addresses) == 0:
            raise ValueError('Список адресов не задан!')
        if len(db.range) == 0:
            raise ValueError('Диапазон не задан!')

        await state.update_data(running=True)
        # await callback.message.answer()
        await callback.answer('✅ Рассылка запущена!')

        auto_transferring_task = asyncio.create_task(
            auto_transferring(callback, db.addresses, db.range),
            name='transferring_task'
        )

        await auto_transferring_task
        await state.update_data(running=False)
        await callback.message.answer('✅ Рассылка завершена!')
    except ValueError as e:
        await callback.answer(str(e))


@router.callback_query(F.data == 'stop')
async def stop(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    task, = [task for task in asyncio.all_tasks() if task.get_name() == 'transferring_task']
    task.cancel()
    await callback.message.answer('✅ Рассылка остановлена!')
    await callback.answer()


@router.callback_query(F.data == 'update_addresses')
async def addresses_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text='📝 Отправьте список адресов в чат',
        reply_markup=await auto.cancel())
    await state.update_data(callback_msg_id=callback.message)
    await state.set_state(Auto.addresses)


@router.message(Auto.addresses)
async def addresses_input(message: Message, state: FSMContext):
    callback_msg: Message = (await state.get_data()).get('callback_msg_id')
    db.addresses = list(message.text.split('\n'))
    db.save()
    await callback_msg.edit_reply_markup(reply_markup=None)
    await menu(message, state)
    await state.set_state(state=None)


@router.callback_query(F.data == 'update_amount_range')
async def amount_range_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text='↔️ Отправьте диапазон, разделенный пробелом',
        reply_markup=await auto.cancel())
    await state.update_data(callback_msg_id=callback.message)
    await state.set_state(Auto.amount_range)


@router.message(Auto.amount_range)
async def amount_range_input(message: Message, state: FSMContext):
    callback_msg: Message = (await state.get_data()).get('callback_msg_id')
    try:
        amount_range = message.text.split()
        if len(amount_range) < 2:
            raise InvalidSeparator
        db.range = amount_range
        db.save()
        await callback_msg.edit_reply_markup(reply_markup=None)
        await state.set_state(state=None)
        await menu(message, state)
    except InvalidSeparator:
        await message.answer(
            text='<b>Отправьте диапазон, разделенный пробелом!</b>',
            parse_mode='HTML'
        )


@router.callback_query(F.data == 'cancel')
async def cancel(callback: CallbackQuery, state: FSMContext):
    await state.set_state(state=None)
    await menu(callback.message, state, callback)


@router.callback_query(F.data == 'clear_addresses')
async def clear_addresses(callback: CallbackQuery, state: FSMContext):
    await db.clean_addresses()
    db.save()
    await menu(callback.message, state, callback)
