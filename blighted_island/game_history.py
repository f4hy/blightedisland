import hashlib
import fsspec
import streamlit as st
from typing import Literal
from pydantic import BaseModel, Field, ValidationError
from datetime import date
from players import Player
from spirits import Spirit
from adversary import Adversary

STORAGE_ROOT = "s3://blightedisland/recorded_games/"


class PlayerSpirit(BaseModel):
    player: Player
    spirit: Spirit


class Game(BaseModel):
    date_played: date = Field(default_factory=date.today)
    adversary: Adversary
    players_played: list[PlayerSpirit]
    won: bool

    def show(self):
        st.write("WON!" if self.won else "Lost :(")
        st.table({"Adversary": self.adversary.model_dump()})
        st.table({p.player.name: p.spirit.model_dump() for p in self.players_played})


@st.cache_resource
def get_fs():
    return fsspec.filesystem("s3")


def list_games() -> list[Game]:
    fs = get_fs()
    try:
        saved_files = fs.ls(STORAGE_ROOT)
    except FileNotFoundError:
        return []
    games: Game = []
    jsons = fs.cat(saved_files)
    for path, j in jsons.items():
        try:
            game = Game.model_validate_json(j)
        except ValidationError:
            st.warning(f"Unable to parse {path}")
        games.append(game)
    return sorted(games, key=lambda x: x.date_played)


def record_game(game: Game):
    fs = get_fs()
    game_json = game.model_dump_json()
    hashstr = hashlib.sha256(game_json.encode()).hexdigest()
    filepath = f"{STORAGE_ROOT}{hashstr}.json"
    fs.write_text(filepath, game_json)
