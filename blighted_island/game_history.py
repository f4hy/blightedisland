"""
Module for tracking and managing Spirit Island game history.
Handles game record storage, retrieval, filtering, and display.
"""

import hashlib
import fsspec
import streamlit as st
import logging
import traceback
import json
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, ValidationError
from datetime import date, datetime
from config import STORAGE_ROOT, CACHE_TTL

# Import required project modules - handled in a way to avoid circular imports
from players import Player, select_player
from spirits import Spirit
from adversary import Adversary

# Set up logging
logger = logging.getLogger(__name__)


class PlayerSpirit(BaseModel):
    """Records which player played which spirit in a game."""

    player: Player
    spirit: Spirit


class Game(BaseModel, frozen=True):
    """
    Represents a complete Spirit Island game record.
    Contains all information about a single play session.
    """

    date_played: date = Field(default_factory=date.today)
    adversary: Adversary
    players_played: List[PlayerSpirit]
    won: Optional[bool]
    desync: Optional[bool] = None
    notes: Optional[str] = None

    def show(self) -> None:
        """Display the game details in the Streamlit UI."""
        st.write(
            "WON! 🎉" if self.won else "Lost 😢" if self.won is False else "Desync ⚠️"
        )

        # Show date and adversary info
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Date:** {self.date_played}")
            st.write(
                f"**Adversary:** {self.adversary.display_name} (Level {self.adversary.level})"
            )

        # Show player and spirit info in a clean table format
        st.write("### Players and Spirits")
        player_data = {
            f"Player {i + 1}": p.player.name for i, p in enumerate(self.players_played)
        }
        spirit_data = {
            f"Spirit {i + 1}": str(p.spirit) for i, p in enumerate(self.players_played)
        }

        st.table([player_data, spirit_data])

        # Show notes if available
        if self.notes:
            st.write("### Notes")
            st.write(self.notes)


class GameFilters(BaseModel):
    """Filters that can be applied to game history."""

    min_players: int
    max_players: int
    player: Optional[Player] = None
    adversary: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None

    def filter_games(self, games: List[Game]) -> List[Game]:
        """Apply all filters to a list of games."""
        filtered = [g for g in games if len(g.players_played) >= self.min_players]
        filtered = [g for g in filtered if len(g.players_played) <= self.max_players]

        if self.player:
            filtered = [
                g
                for g in filtered
                if self.player in {p.player for p in g.players_played}
            ]

        if self.adversary:
            filtered = [g for g in filtered if g.adversary.name == self.adversary]

        if self.date_from:
            filtered = [g for g in filtered if g.date_played >= self.date_from]

        if self.date_to:
            filtered = [g for g in filtered if g.date_played <= self.date_to]

        return filtered


@st.cache_resource
def get_fs():
    """Get a filesystem object for accessing storage."""
    try:
        return fsspec.filesystem("s3")
    except Exception as e:
        logger.error(f"Error creating filesystem: {e}")
        st.error(f"Unable to connect to storage: {e}")
        return None


@st.cache_data(ttl=CACHE_TTL)
def list_games() -> List[Game]:
    """
    Load all saved games from storage.

    Returns:
        List[Game]: List of all saved games, sorted by date
    """
    fs = get_fs()
    if not fs:
        return []

    try:
        saved_files = fs.ls(STORAGE_ROOT)
    except FileNotFoundError:
        # No games recorded yet, return empty list
        return []
    except Exception as e:
        logger.error(f"Error listing games: {e}")
        st.error(f"Unable to list games: {e}")
        return []

    games: List[Game] = []

    try:
        jsons = fs.cat(saved_files)
    except Exception as e:
        logger.error(f"Error reading game files: {e}")
        st.error(f"Unable to read game files: {e}")
        return []

    for path, j in jsons.items():
        try:
            game = Game.model_validate_json(j)
            games.append(game)
        except ValidationError as e:
            logger.warning(f"Unable to parse {path}: {e}")
            st.warning(f"Unable to parse {path}")
        except Exception as e:
            logger.error(f"Error parsing {path}: {e}")

    return sorted(games, key=lambda x: x.date_played, reverse=True)


def record_game(game: Game) -> bool:
    """
    Save a game record to storage.

    Args:
        game: The game to save

    Returns:
        bool: True if successfully saved, False otherwise
    """
    fs = get_fs()
    if not fs:
        st.error("Unable to connect to storage")
        return False

    try:
        game_json = game.model_dump_json()
        hashstr = hashlib.sha256(game_json.encode()).hexdigest()
        filepath = f"{STORAGE_ROOT}{hashstr}.json"

        fs.write_text(filepath, game_json)
        st.cache_data.clear()
        return True

    except Exception as e:
        logger.error(f"Error saving game: {e}")
        st.error(f"Unable to save game: {e}")
        traceback.print_exc()
        return False


def export_games(games: List[Game], filename: str = None) -> str:
    """
    Export games to a JSON file for backup or sharing.

    Args:
        games: List of games to export
        filename: Optional custom filename

    Returns:
        str: JSON string of exported games
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"spirit_island_games_{timestamp}.json"

    games_json = json.dumps([g.model_dump() for g in games], default=str, indent=2)

    return games_json


def import_games(games_json: str) -> Tuple[int, int]:
    """
    Import games from a JSON file.

    Args:
        games_json: JSON string containing game data

    Returns:
        Tuple[int, int]: (number of games imported, number of games failed)
    """
    try:
        games_data = json.loads(games_json)
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON format: {e}")
        return 0, 0

    imported = 0
    failed = 0

    for game_data in games_data:
        try:
            game = Game.model_validate(game_data)
            if record_game(game):
                imported += 1
            else:
                failed += 1
        except ValidationError as e:
            logger.error(f"Validation error importing game: {e}")
            failed += 1
        except Exception as e:
            logger.error(f"Error importing game: {e}")
            failed += 1

    return imported, failed


def set_filters() -> GameFilters:
    """
    Create a UI for setting game filters.

    Returns:
        GameFilters: The filters set by the user
    """
    player = None
    min_players = 0
    max_players = 100
    date_from = None
    date_to = None
    adversary = None

    with st.expander("Set filters"):
        col1, col2 = st.columns(2)

        with col1:
            min_players = st.slider("Min player count", 1, 6, 2)
            max_players = st.slider("Max player count", min_players, 6, 4)

        with col2:
            date_from = st.date_input("From date", value=None)
            date_to = st.date_input("To date", value=None)

        # Player filter
        player = select_player()

        # Adversary filter
        from adversary import ADVERSARY_NAMES

        adversary = st.selectbox(
            "Filter by adversary", options=["All"] + ADVERSARY_NAMES, index=0
        )
        if adversary == "All":
            adversary = None

    return GameFilters(
        min_players=min_players,
        max_players=max_players,
        player=player,
        adversary=adversary,
        date_from=date_from,
        date_to=date_to,
    )


def filter_games(games: List[Game], filters: GameFilters) -> List[Game]:
    """
    Apply filters to a list of games.

    Args:
        games: List of games to filter
        filters: Filters to apply

    Returns:
        List[Game]: The filtered list of games
    """
    return filters.filter_games(games)
