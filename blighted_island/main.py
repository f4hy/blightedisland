"""
Module for managing Spirit Island spirits.
Handles representation, selection, and randomization of spirits.
"""

import random
import time
from typing import Literal, List, Dict, Optional, Set, Tuple
from pydantic import BaseModel, Field
import streamlit as st
import urllib.parse

# Type definition for spirit complexity
Complexity = Literal["Very High", "High", "Moderate", "Low"]


class Spirit(BaseModel):
    """
    Represents a Spirit Island spirit with its properties.
    Includes name, complexity, and optional aspect.
    """

    name: str
    complexity: Complexity
    aspect: Optional[str] = None

    def __str__(self) -> str:
        """Format spirit as a string, including aspect if present."""
        if self.aspect:
            return f"{self.name} [{self.aspect}]"
        return f"{self.name}"

    @property
    def base_name(self) -> str:
        """Get the base name without aspect."""
        return self.name

    @property
    def display_name(self) -> str:
        """Get a fully formatted display name."""
        if self.aspect:
            return f"{self.name} • {self.aspect} Aspect"
        return self.name

    @property
    def complexity_level(self) -> int:
        """Convert complexity text to numeric value for sorting."""
        complexity_map = {"Low": 1, "Moderate": 2, "High": 3, "Very High": 4}
        return complexity_map.get(self.complexity, 0)


def spirit_image(spirit: Spirit) -> None:
    """
    Display an image of the spirit from the Spirit Island wiki.

    Args:
        spirit: The spirit to display an image for
    """
    try:
        root = "https://spiritislandwiki.com/images/c/c2/"
        name = spirit.name.replace(" ", "_")
        filename = urllib.parse.quote_plus(name) + ".png"
        path = f"{root}{filename}"

        st.write(f"**{spirit.display_name}**")
        st.image(path, caption=f"Complexity: {spirit.complexity}")
    except Exception as e:
        st.error(f"Could not load image for {spirit.name}: {e}")


# Complete list of spirits in Spirit Island (base game + expansions)
SPIRITS: List[Spirit] = sorted(
    [
        # Base Game Spirits
        Spirit(name="Lightning's Swift Strike", complexity="Low"),
        Spirit(name="Lightning's Swift Strike", complexity="Low", aspect="Pandemonium"),
        Spirit(name="Lightning's Swift Strike", complexity="Low", aspect="Wind"),
        Spirit(name="River Surges in Sunlight", complexity="Low"),
        Spirit(name="River Surges in Sunlight", complexity="Low", aspect="Sunshine"),
        Spirit(name="Shadows Flicker Like Flame", complexity="Low"),
        Spirit(name="Shadows Flicker Like Flame", complexity="Low", aspect="Madness"),
        Spirit(name="Shadows Flicker Like Flame", complexity="Low", aspect="Reach"),
        Spirit(name="Vital Strength of the Earth", complexity="Low"),
        Spirit(
            name="Vital Strength of the Earth", complexity="Low", aspect="Resilience"
        ),
        # Branch & Claw Expansion
        Spirit(name="A Spread of Rampant Green", complexity="Moderate"),
        Spirit(name="Thunderspeaker", complexity="Moderate"),
        Spirit(name="Bringer of Dreams and Nightmares", complexity="High"),
        Spirit(name="Ocean's Hungry Grasp", complexity="High"),
        # Promo Pack 1
        Spirit(name="Keeper of the Forbidden Wilds", complexity="Moderate"),
        Spirit(name="Sharp Fangs Behind the Leaves", complexity="Moderate"),
        # Promo Pack 2
        Spirit(name="Heart of the Wildfire", complexity="High"),
        Spirit(name="Serpent Slumbering Beneath the Island", complexity="High"),
        # Jagged Earth Expansion
        Spirit(name="Lure of the Deep Wilderness", complexity="Moderate"),
        Spirit(name="Many Minds Move as One", complexity="Moderate"),
        Spirit(name="Stone's Unyielding Defiance", complexity="Moderate"),
        Spirit(name="Volcano Looming High", complexity="Moderate"),
        Spirit(name="Vengeance as a Burning Plague", complexity="High"),
        Spirit(name="Fractured Days Split the Sky", complexity="Very High"),
        # Nature Incarnate Expansion
        Spirit(name="Devouring Teeth Lurk Underfoot", complexity="Low"),
        Spirit(name="Eyes Watch from the Trees", complexity="Low"),
        Spirit(name="Fathomless Mud of the Swamp", complexity="Low"),
        Spirit(name="Rising Heat of Stone and Sand", complexity="Low"),
        Spirit(name="Sun-Bright Whirlwind", complexity="Low"),
        Spirit(name="Shroud of Silent Mist", complexity="High"),
    ],
    key=str,
)


def get_unique_spirit_names() -> Set[str]:
    """
    Get a set of unique spirit base names (without aspects).

    Returns:
        Set[str]: Set of unique spirit names
    """
    return {s.name for s in SPIRITS}


def get_spirits_by_complexity(complexity: Optional[Complexity] = None) -> List[Spirit]:
    """
    Filter spirits by complexity level.

    Args:
        complexity: The complexity level to filter by, or None for all

    Returns:
        List[Spirit]: Filtered list of spirits
    """
    if complexity is None:
        return SPIRITS

    return [s for s in SPIRITS if s.complexity == complexity]


def random_spirit(complexity: Optional[Complexity] = None) -> Spirit:
    """
    Get a random spirit, optionally filtered by complexity.
    Doesn't count aspects as separate spirits for randomization.

    Args:
        complexity: Optional complexity filter

    Returns:
        Spirit: A randomly selected spirit
    """
    filtered_spirits = get_spirits_by_complexity(complexity)

    # Get unique spirit names from the filtered list
    spirit_names = {s.name for s in filtered_spirits}

    with st.spinner("Selecting a random spirit..."):
        time.sleep(0.8)  # Brief delay for UX

    selected_name = random.choice(list(spirit_names))

    # Get all variants (base + aspects) of the selected spirit
    aspects = [s for s in filtered_spirits if selected_name == s.name]

    # Return a random variant
    return random.choice(aspects)


def group_spirits_by_complexity() -> Dict[Complexity, List[Spirit]]:
    """
    Group spirits by their complexity levels.

    Returns:
        Dict[Complexity, List[Spirit]]: Dictionary mapping complexity to spirits
    """
    result: Dict[Complexity, List[Spirit]] = {
        "Low": [],
        "Moderate": [],
        "High": [],
        "Very High": [],
    }

    for spirit in SPIRITS:
        result[spirit.complexity].append(spirit)

    return result


def get_spirit_stats(games: List) -> Dict[str, Dict[str, int]]:
    """
    Calculate statistics for each spirit from game history.

    Args:
        games: List of played games

    Returns:
        Dict mapping spirit names to their statistics
    """
    stats: Dict[str, Dict[str, int]] = {}

    for game in games:
        for player_spirit in game.players_played:
            spirit_str = str(player_spirit.spirit)

            if spirit_str not in stats:
                stats[spirit_str] = {"wins": 0, "losses": 0, "total": 0}

            stats[spirit_str]["total"] += 1

            if game.won is True:
                stats[spirit_str]["wins"] += 1
            elif game.won is False:
                stats[spirit_str]["losses"] += 1

    # Calculate win percentages
    for spirit in stats:
        total = stats[spirit]["total"]
        stats[spirit]["win_pct"] = round(
            stats[spirit]["wins"] / total * 100 if total > 0 else 0, 1
        )

    return stats


def select_spirit(
    key: str = "select_spirit", default_index: Optional[int] = None
) -> Optional[Spirit]:
    """
    Create a Streamlit UI for selecting a spirit.

    Args:
        key: Unique key for the Streamlit component
        default_index: Optional default selection index

    Returns:
        Optional[Spirit]: The selected spirit or None
    """
    # Group spirits by complexity
    grouped = group_spirits_by_complexity()

    # Create a list of options with headers
    options = []
    display_names = []

    for complexity in ["Low", "Moderate", "High", "Very High"]:
        if grouped[complexity]:
            # Add a non-selectable header
            options.append(None)
            display_names.append(f"--- {complexity} Complexity ---")

            # Add spirits for this complexity
            for spirit in grouped[complexity]:
                options.append(spirit)
                display_names.append(str(spirit))

    # Create the selectbox with grouped options
    selected_index = st.selectbox(
        "Select Spirit",
        options=range(len(options)),
        format_func=lambda i: display_names[i],
        key=key,
        index=default_index,
    )

    # Return the selected spirit if a valid selection was made
    if selected_index is not None and options[selected_index] is not None:
        return options[selected_index]

    return None
