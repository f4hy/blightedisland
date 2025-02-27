import hashlib
import fsspec
import streamlit as st
from typing import Literal
from pydantic import BaseModel, Field, ValidationError
from datetime import date
from players import Player, select_player
from spirits import Spirit
from adversary import Adversary

STORAGE_ROOT = "s3://blightedisland/recorded_games/"


class PlayerSpirit(BaseModel):
    player: Player
    spirit: Spirit


class Game(BaseModel, frozen=True):
    date_played: date = Field(default_factory=date.today)
    adversary: Adversary
    players_played: list[PlayerSpirit]
    won: bool | None
    desync: bool | None = None

    def show(self):
        st.write("WON!" if self.won else "Lost :(")
        st.table({"Adversary": self.adversary.model_dump()})
        st.table({p.player.name: p.spirit.model_dump() for p in self.players_played})


class GameFilters(BaseModel):
    min_players: int
    max_players: int
    player: Player | None


@st.cache_resource
def get_fs():
    return fsspec.filesystem("s3")


@st.cache_data(ttl=300)
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
    st.cache_data.clear()


def set_filters() -> GameFilters:
    player = None
    min_players = 0
    max_players = 100
    with st.expander("Set filters"):
        min_players = st.slider("min player count", 2, 4)
        max_players = st.slider("max player count", 2, 4, 4)

        player = select_player()
    return GameFilters(
        min_players=min_players,
        max_players=max_players,
        player=player,
    )


def filter_games(games: list[Game], filters: GameFilters):
    games = [g for g in games if len(g.players_played) >= (filters.min_players or 0)]
    games = [g for g in games if len(g.players_played) <= (filters.max_players or 100)]
    if filters.player:
        games = [
            g for g in games if filters.player in {p.player for p in g.players_played}
        ]

    return games
