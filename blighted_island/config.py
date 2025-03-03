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
