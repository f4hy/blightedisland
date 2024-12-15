from typing import Literal
from pydantic import BaseModel


class Player(BaseModel):
    name: str


PLAYER_NAMES: list[str] = sorted(
    [
        "Brendan",
        "Kyle",
        "Geoff",
        "Bill",
        "Colin",
    ]
)


PLAYERS: list[Player] = [Player(name=n) for n in PLAYER_NAMES]
