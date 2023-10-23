import simplejson as json
from aiohttp import ClientSession

from common.envs import API


async def fastest_fee() -> float:
    async with ClientSession() as session:
        async with session.get(f'{API}/api/v1/fees/recommended') as fees:
            return json.loads(await fees.text())['fastestFee']


async def confirmed(tx_id) -> bool:
    async with ClientSession() as session:
        async with session.get(f'{API}/api/tx/{tx_id}/status') as tx_info:
            return json.loads(await tx_info.text())['confirmed']
