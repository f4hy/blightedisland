"""Configuration settings for the Blighted Island application."""

import os
from typing import Dict, Any

# Storage configuration
STORAGE_ROOT = os.environ.get(
    "BLIGHTED_ISLAND_STORAGE", "s3://blightedisland/recorded_games/"
)

# Application settings
APP_TITLE = "Blighted Island"
APP_SUBTITLE = "Stats for Spirit Island"

# Default values
DEFAULT_ADVERSARY_LEVEL = 3
DEFAULT_MIN_PLAYERS = 2
DEFAULT_MAX_PLAYERS = 4

# Cache settings
CACHE_TTL = 300  # seconds

# UI settings
CHART_COLORS = ["#FF0000", "#0000FF"]
CHART_HEIGHT = 400

# Game settings
DESYNC_LABEL = "desync"
WIN_LABEL = "won"
LOSS_LABEL = "lost"
RESULT_OPTIONS = [WIN_LABEL, LOSS_LABEL, DESYNC_LABEL]


# Adversary level configuration
ADVERSARY_MIN_LEVEL = 0  # Minimum adversary level
ADVERSARY_MAX_LEVEL = 6  # Maximum adversary level
ADVERSARY_DEFAULT_LEVEL = 3  # Default level for new games

# Adversary level descriptions (optional)
ADVERSARY_LEVEL_DESCRIPTIONS = {
    0: "Base Game (No Adversary)",
    1: "Very Easy",
    2: "Easy",
    3: "Moderate",
    4: "Challenging",
    5: "Hard",
    6: "Very Hard",
}


# This can be used in the UI to show level difficulty with the number
def get_adversary_level_display(level):
    """Get a formatted display string for an adversary level."""
    if level in ADVERSARY_LEVEL_DESCRIPTIONS:
        return f"Level {level} - {ADVERSARY_LEVEL_DESCRIPTIONS[level]}"
    return f"Level {level}"
