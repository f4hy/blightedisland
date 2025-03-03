import streamlit as st
from typing import Literal
from pydantic import BaseModel


class Player(BaseModel, frozen=True):
    name: str


PLAYER_NAMES: list[str] = sorted(
    [
        "Brendan",
        "Kyle",
        "Geoff",
        "Bill",
        "Colin",
        "Nathan",
        "Linda",
        "Manu",
        "Stephan",
    ]
)


PLAYERS: list[Player] = [Player(name=n) for n in PLAYER_NAMES]


def select_player() -> Player | None:
    selected_player = st.segmented_control(
        label="Filter to games for just player",
        options=PLAYERS + [None],
        format_func=lambda x: x.name if x else "No filter",
        default=None,
    )
    return selected_player
