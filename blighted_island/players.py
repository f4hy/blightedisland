"""
Module for managing player data in the Blighted Island application.
Handles player representation and selection in the UI.
"""

import streamlit as st
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class Player(BaseModel, frozen=True):
    """
    Represents a player in the game.
    
    Attributes:
        name: The player's name
    """
    name: str
    
    def __str__(self) -> str:
        """String representation of the player (their name)."""
        return self.name


# List of player names
PLAYER_NAMES: List[str] = sorted(
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

# Create player objects from names
PLAYERS: List[Player] = [Player(name=n) for n in PLAYER_NAMES]


def select_player(label: str = "Select Player", allow_none: bool = True) -> Optional[Player]:
    """
    Create a UI element for selecting a player.
    
    Args:
        label: The label for the selection element
        allow_none: Whether to include a 'None' option
        
    Returns:
        The selected player or None
    """
    options = PLAYERS.copy()
    
    if allow_none:
        selected_player = st.selectbox(
            label=label,
            options=options + [None],
            format_func=lambda x: x.name if x else "No filter",
            index=len(options)
        )
    else:
        selected_player = st.selectbox(
            label=label,
            options=options,
            format_func=lambda x: x.name
        )
        
    return selected_player


def add_player(name: str) -> Optional[Player]:
    """
    Add a new player to the system.
    
    Args:
        name: The name of the player to add
        
    Returns:
        The newly created Player object, or None if the name is invalid
    """
    # Validate the name
    if not name or name.strip() == "":
        return None
    
    # Check if player already exists
    if name in PLAYER_NAMES:
        return None
    
    # Create new player
    new_player = Player(name=name)
    
    # Add to lists (would be persisted in a real implementation)
    PLAYER_NAMES.append(name)
    PLAYERS.append(new_player)
    
    return new_player


def get_player_stats(games: List) -> Dict[str, Dict[str, int]]:
    """
    Calculate statistics for each player from game history.
    
    Args:
        games: List of played games
        
    Returns:
        Dict mapping player names to their statistics
    """
    stats = {}
    
    for game in games:
        for player_spirit in game.players_played:
            player_name = player_spirit.player.name
            
            if player_name not in stats:
                stats[player_name] = {"wins": 0, "losses": 0, "total": 0}
                
            stats[player_name]["total"] += 1
            
            if game.won is True:
                stats[player_name]["wins"] += 1
            elif game.won is False:
                stats[player_name]["losses"] += 1
                
    # Calculate win percentages
    for player in stats:
        total = stats[player]["total"]
        stats[player]["win_pct"] = round(stats[player]["wins"] / total * 100 if total > 0 else 0, 1)
                
    return stats
