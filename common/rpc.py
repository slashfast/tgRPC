import time
from decimal import Decimal

import simplejson as json
from aiohttp import ClientSession

from common.envs import RPC_URL, WALLET_PASSWORD


class ElectrumRPCError(Exception):
    pass


async def call(method, params):
    payload = {
        'jsonrpc': '2.0',
        'id': f'{method}_{int(time.time())}',
        'method': method,
        'params': params
    }

    async with ClientSession() as session:
        async with session.post(RPC_URL, data=json.dumps(payload)) as response:
            response = json.loads(await response.text())

        if 'error' in response:
            raise ElectrumRPCError(f'ElectrumRPCError: {str(response["error"]["message"])}')

        return response['result']


async def pay_to(address: str, amount: Decimal, fee: float):
    return await call(
        method='payto',
        params={
            'destination': address,
            'amount': amount,
            'password': WALLET_PASSWORD,
            'feerate': fee,
        })


async def sign_tx(unsigned_tx: str):
    return await call(
        method='signtransaction',
        params={
            'tx': unsigned_tx,
            'password': WALLET_PASSWORD
        }
    )


async def broadcast(signed_tx: str):
    return await call(
        method='broadcast',
        params={
            'tx': signed_tx
        }
    )
