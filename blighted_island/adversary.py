from collections import Counter
import random
import streamlit as st
from typing import Literal
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game_history import Game


class Adversary(BaseModel, frozen=True):
    name: str
    level: int

    def __str__(self):
        return f"[{self.level}]{self.name.replace('-', ' ').split(' ')[0]}"


ADVERSARY_NAMES: list[str] = sorted(
    [
        "Brandenburg-Prussia",
        "England",
        "Sweden",
        "France (Plantation Colony)",
        "Habsburg Monarchy (Livestock Colony)",
        "Russia",
        # "Habsburg Mining Expedition",
    ]
)


def enter_adversary() -> Adversary:
    st.write()
    name = st.selectbox("Select Adversary", ADVERSARY_NAMES, index=None)
    if name:
        level = st.slider("select level", 1, 6, 3)
        return Adversary(name=name, level=level)


def random_adversary(level: int) -> Adversary:
    """Get a random adverary at a level."""

    adv_name = random.choice(ADVERSARY_NAMES)
    return Adversary(name=adv_name, level=level)


def weighted_random_adversary(level: int, games: list["Game"]) -> Adversary:
    """Get an adversary decreasing probability based on games."""

    adversary_at_level = [g.adversary.name for g in games if g.adversary.level == level]

    counter = Counter(adversary_at_level)
    max_adversary, max_count = counter.most_common(1)[0]
    weights = [(max_count / counter.get(a, 1) - 1) for a in ADVERSARY_NAMES]
    adv_name = random.choices(ADVERSARY_NAMES, weights=weights)
    return Adversary(name=adv_name[0], level=level)
