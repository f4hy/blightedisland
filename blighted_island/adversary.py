"""
Module for managing Spirit Island adversaries.
Handles representation, selection, and randomization of adversaries.
"""

from collections import Counter
import random
import streamlit as st
from typing import Literal, List, Optional, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from game_history import Game


class Adversary(BaseModel, frozen=True):
    """Represents a Spirit Island adversary with name and difficulty level."""

    name: str
    level: int

    def __str__(self) -> str:
        """Format adversary as a string: [level]Name."""
        # Display only the first word of the adversary name without hyphens
        return f"[{self.level}]{self.name.replace('-', ' ').split(' ')[0]}"

    @property
    def display_name(self) -> str:
        """Return a formatted name for display purposes."""
        return self.name.replace("-", " ")


# List of official adversaries in Spirit Island
ADVERSARY_NAMES: List[str] = sorted(
    [
        "Brandenburg-Prussia",
        "England",
        "Sweden",
        "France (Plantation Colony)",
        "Habsburg Monarchy (Livestock Colony)",
        "Russia",
        # "Habsburg Mining Expedition",  # Commented out for now
    ]
)


def enter_adversary() -> Optional[Adversary]:
    """
    Streamlit UI component for selecting an adversary and its level.

    Returns:
        Optional[Adversary]: The selected adversary or None if not selected
    """
    st.write()
    name = st.selectbox("Select Adversary", ADVERSARY_NAMES, index=None)

    if name:
        level = st.slider("Select level", 1, 6, 3)
        return Adversary(name=name, level=level)

    return None


def random_adversary(level: int) -> Adversary:
    """
    Generate a random adversary at the specified level.

    Args:
        level: The difficulty level of the adversary

    Returns:
        Adversary: A randomly selected adversary at the specified level
    """
    adv_name = random.choice(ADVERSARY_NAMES)
    return Adversary(name=adv_name, level=level)


def weighted_random_adversary(level: int, games: List["Game"]) -> Adversary:
    """
    Get an adversary with weighted randomization based on play history.
    Adversaries played less often have higher probability of being selected.

    Args:
        level: The difficulty level of the adversary
        games: List of previously played games to base weighting on

    Returns:
        Adversary: A randomly selected adversary with weighting applied
    """
    # Extract adversaries at the specified level from game history
    adversary_at_level = [g.adversary.name for g in games if g.adversary.level == level]

    # If no data available, return a completely random adversary
    if not adversary_at_level:
        return random_adversary(level)

    # Count occurrences of each adversary at the specified level
    counter = Counter(adversary_at_level)

    # Get the most common adversary and its count
    if counter:
        max_adversary, max_count = counter.most_common(1)[0]
    else:
        # Default values if counter is empty
        max_adversary, max_count = ADVERSARY_NAMES[0], 1

    # Calculate weights: less frequently played adversaries get higher weight
    weights = [(max_count / counter.get(a, 1) - 1) for a in ADVERSARY_NAMES]

    # Handle negative or zero weights (shouldn't happen but just in case)
    weights = [max(w, 0.1) for w in weights]

    # Select adversary using weighted random choice
    adv_name = random.choices(ADVERSARY_NAMES, weights=weights)[0]

    return Adversary(name=adv_name, level=level)


def get_adversary_stats(games: List["Game"]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate statistics for each adversary from game history.

    Args:
        games: List of played games

    Returns:
        Dict mapping adversary names to their statistics
    """
    stats: Dict[str, Dict[str, Any]] = {}

    for game in games:
        adv_key = f"{game.adversary.name} (Lvl {game.adversary.level})"

        if adv_key not in stats:
            stats[adv_key] = {"wins": 0, "losses": 0, "total": 0}

        stats[adv_key]["total"] += 1

        if game.won is True:
            stats[adv_key]["wins"] += 1
        elif game.won is False:
            stats[adv_key]["losses"] += 1

    # Calculate win percentages
    for adv in stats:
        total = stats[adv]["total"]
        stats[adv]["win_pct"] = round(
            stats[adv]["wins"] / total * 100 if total > 0 else 0, 1
        )

    return stats
