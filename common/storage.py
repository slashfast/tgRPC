from decimal import Decimal

import simplejson as json


class Storage:
    def __init__(self, path: str, addresses: list[str] | None = None,
                 amount_range: list[Decimal, Decimal] | None = None):
        self.__path = path
        self.__addresses = addresses if addresses else []
        self.__range = amount_range if amount_range else []

    @property
    def addresses(self) -> list[str]:
        return self.__addresses

    @addresses.setter
    def addresses(self, addresses: list[str]):
        self.__addresses.extend(addresses)

    @property
    def range(self):
        return self.__range

    @range.setter
    def range(self, amount_range: list[float, float]):
        self.__range = list(map(Decimal, amount_range))

    @staticmethod
    def to_dict(addresses: list[str] | None = None, amount_range: list[Decimal, Decimal] | None = None):
        return {
            'addresses': [] if addresses is None else addresses,
            'range': amount_range if amount_range else []
        }

    async def clean_addresses(self):
        self.__addresses = []

    async def pop_address(self):
        self.__addresses.pop(0)

    def save(self):
        with open(self.__path, 'w') as file:
            json.dump(obj=self.to_dict(self.__addresses, self.__range), fp=file, indent=2)  # noqa
