from dataclasses import dataclass
from typing import NamedTuple


@dataclass(frozen=True)
class Offer:
    variant: str
    price: int


class ShopResult(NamedTuple):
    prices: dict[str, int]
    error: str | None
