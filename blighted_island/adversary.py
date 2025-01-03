import streamlit as st
from typing import Literal
from pydantic import BaseModel, Field


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
