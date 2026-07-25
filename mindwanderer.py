"""
Client for mindwanderer.net's "Spirit Island Digital" personal statistics export.

The official Spirit Island Digital app (Handelabra) auto-uploads every completed
game to a per-device UID on mindwanderer.net. That data can be pulled back down
as JSON, which is what this module does - no manual export/upload required.

Endpoint discovered by inspecting https://mindwanderer.net/si/player/?uid=<uid>:
    https://mindwanderer.net/si/player/json.cgi?uid=<uid>

A bad/missing uid returns an HTML error page (406 or 404) instead of JSON, so
callers should expect MindWandererError rather than a JSON parse error.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, ConfigDict, ValidationError

logger = logging.getLogger(__name__)

BASE_URL = "https://mindwanderer.net/si/player/json.cgi"
UID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


class MindWandererError(Exception):
    """Raised when the mindwanderer.net export can't be fetched or parsed."""


class GameRecord(BaseModel):
    """
    One completed game as recorded by the Spirit Island Digital app.

    Field names mirror the source JSON exactly (camelCase) rather than being
    translated to blightedisland's own domain models - that mapping is a
    separate concern for whenever this gets wired into the Streamlit app.
    Unknown fields are kept rather than rejected, since this is an undocumented
    third-party endpoint that could add fields at any time.
    """

    model_config = ConfigDict(extra="allow")

    createdAt: datetime
    spirits: List[str]
    aspects: Dict[str, str] = {}
    adversary: Optional[str] = None
    adversaryLevel: int
    supportingAdversary: Optional[str] = None
    supportingAdversaryLevel: Optional[int] = None
    scenario: Optional[str] = None
    difficulty: int
    waveNumber: int
    boards: List[str]
    layoutId: str
    blightCard: Optional[str] = None
    blightRemaining: int
    blightOnIsland: int
    dahanOnIsland: int
    powerCardsInDiscard: List[str] = []
    powerCardsOwned: Dict[str, List[str]] = {}
    endingResult: str
    terrorLevel: int
    turn: int
    score: int

    @property
    def won(self) -> bool:
        """Whether the spirits won, derived from the endingResult prefix."""
        return self.endingResult.startswith("Win")


def _validate_uid(uid: str) -> str:
    uid = uid.strip()
    if not UID_RE.match(uid):
        raise MindWandererError(f"{uid!r} doesn't look like a mindwanderer device UID")
    return uid


def fetch_raw_games(uid: str, *, timeout: float = 30.0) -> List[Dict[str, Any]]:
    """
    Fetch the raw (unvalidated) list of game dicts for a device UID.

    Raises MindWandererError on network failure, a non-JSON response (which
    means the UID was rejected - mindwanderer.net returns an HTML error page
    with a 404 for a missing uid or 406 for an unrecognized one), or a
    malformed JSON body.
    """
    uid = _validate_uid(uid)

    try:
        response = requests.get(BASE_URL, params={"uid": uid}, timeout=timeout)
    except requests.RequestException as e:
        raise MindWandererError(f"Request to mindwanderer.net failed: {e}") from e

    content_type = response.headers.get("Content-Type", "")
    if "json" not in content_type:
        if response.status_code == 404:
            raise MindWandererError(f"No device found for uid={uid}")
        raise MindWandererError(
            f"Unexpected response for uid={uid} "
            f"(HTTP {response.status_code}, Content-Type: {content_type or 'unknown'}); "
            "the uid was likely rejected"
        )

    try:
        data = response.json()
    except ValueError as e:
        raise MindWandererError(f"Response body wasn't valid JSON: {e}") from e

    if not isinstance(data, list):
        raise MindWandererError(f"Expected a JSON list of games, got {type(data).__name__}")

    return data


def fetch_games(uid: str, *, timeout: float = 30.0) -> List[GameRecord]:
    """
    Fetch and validate all games recorded for a device UID.

    Records that fail validation are logged and skipped rather than aborting
    the whole fetch, matching how blighted_island/game_history.py already
    handles per-record validation errors when loading saved games.
    """
    raw_games = fetch_raw_games(uid, timeout=timeout)

    games: List[GameRecord] = []
    for i, raw in enumerate(raw_games):
        try:
            games.append(GameRecord.model_validate(raw))
        except ValidationError as e:
            logger.warning("Skipping unparseable game record %d: %s", i, e)

    return sorted(games, key=lambda g: g.createdAt)


def summarize(games: List[GameRecord]) -> str:
    """Build a short human-readable summary of a list of games."""
    if not games:
        return "No games found."

    wins = sum(1 for g in games if g.won)
    total = len(games)
    win_rate = round(wins / total * 100, 1)

    spirit_counts: Counter = Counter()
    for g in games:
        spirit_counts.update(g.spirits)
    top_spirits = ", ".join(f"{name} ({count})" for name, count in spirit_counts.most_common(5))

    lines = [
        f"Games: {total}",
        f"Wins: {wins} ({win_rate}%)",
        f"Date range: {games[0].createdAt.date()} to {games[-1].createdAt.date()}",
        f"Most-played spirits: {top_spirits}",
    ]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch a player's Spirit Island Digital game history from mindwanderer.net"
    )
    parser.add_argument("uid", help="mindwanderer.net device UID, e.g. from your stats page URL")
    parser.add_argument(
        "-o", "--output", metavar="PATH", help="Write the fetched games as JSON to this file"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Skip pydantic validation; fetch and store/print the server's JSON as-is",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress the summary printed to stdout"
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    try:
        if args.raw:
            raw_games = fetch_raw_games(args.uid)
            output_text = json.dumps(raw_games, indent=2)
            game_count = len(raw_games)
            summary_text = f"Games: {game_count}"
        else:
            games = fetch_games(args.uid)
            output_text = json.dumps([g.model_dump(mode="json") for g in games], indent=2)
            summary_text = summarize(games)
    except MindWandererError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w") as f:
            f.write(output_text)
        if not args.quiet:
            print(f"Wrote {args.output}")
    elif not args.quiet:
        print(output_text)

    if not args.quiet:
        print(summary_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
