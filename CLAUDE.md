# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Blighted Island is a Streamlit app for tracking Spirit Island (the board game) play sessions — which spirit/adversary combos were played, who won, and stats/win-rate breakdowns over time.

## Running the app

```bash
source venv/bin/activate   # venv already exists at ./venv (Python 3.13)
streamlit run blighted_island/main.py
```

Deployed via `Procfile` (`sh setup.sh && streamlit run blighted_island/main.py`) — `setup.sh` writes `~/.streamlit/credentials.toml` and `~/.streamlit/config.toml` from the `$PORT` env var for the hosting platform (e.g. Heroku-style).

## Dependencies

- `requirements.txt`: runtime deps (`streamlit`, `pydantic`, `fsspec[s3]`).
- `requirements-dev.txt`: adds `ruff`, `flake8`, and `python-lsp-server` + plugins for local dev/linting.

Install with `pip install -r requirements.txt -r requirements-dev.txt`.

## Linting

```bash
ruff check blighted_island/
```

There is no dedicated ruff config file (no `pyproject.toml`/`ruff.toml`) — ruff runs with its defaults.

## Tests

There is no test suite in this repo currently.

## Architecture

All app code lives in `blighted_island/` as a flat set of modules imported by bare name (e.g. `import spirits`, `from config import ...`) — there's no package-relative import structure, so scripts assume `blighted_island/` itself is on `sys.path` (true when running `streamlit run blighted_island/main.py`).

- **`main.py`** — the only Streamlit entry point. Builds the six-tab UI (Stats, Random Spirit, Random Adversary, Record Game, Game History, Settings) and contains all the rendering/breakdown functions (`render_*_tab`, `breakdown_by_*`, `display_win_loss_trend`). Business logic for stats aggregation is inlined here rather than in the domain modules.
- **`config.py`** — central constants: storage location, app title, chart colors, result labels (`WIN_LABEL`/`LOSS_LABEL`/`DESYNC_LABEL`), adversary level bounds/descriptions.
- **`game_history.py`** — the persistence layer and domain root:
  - `Game` (pydantic, frozen) is the canonical record: date, `Adversary`, list of `PlayerSpirit` (player+spirit pairs), win/loss/desync result, notes.
  - `GameFilters` encapsulates the stats-tab filtering logic (player count range, player, adversary, adversary level, date range) via `filter_games`.
  - Storage is **content-addressed JSON files on S3** via `fsspec`: each game is serialized with `model_dump_json()`, hashed with sha256, and written to `{STORAGE_ROOT}/{hash}.json`. `STORAGE_ROOT` defaults to `s3://blightedisland/recorded_games/` and is overridable via the `BLIGHTED_ISLAND_STORAGE` env var (e.g. for local testing, point it at a local path fsspec supports).
  - `list_games()` is `@st.cache_resource`/`@st.cache_data(ttl=CACHE_TTL)`-cached; any write (`record_game`, `delete_game`, `import_games`) must call `st.cache_data.clear()` to invalidate it (already done in those functions — replicate this if adding new mutation paths).
  - Because games are content-addressed by hash of their full JSON, editing an existing game isn't supported as an update — it's delete-old/write-new.
- **`spirits.py`** — the `Spirit` pydantic model (name, complexity, optional `aspect`, `primary_elements`) plus the static `SPIRITS` list (all spirits across base game + expansions — Branch & Claw, Promo Packs, Jagged Earth, Nature Incarnate). Spirit aspects (e.g. Lightning's "Wind" aspect) are separate `Spirit` entries sharing a base `name`; `random_spirit()` picks a base name first, then a random aspect variant, so aspects don't skew randomization odds.
- **`adversary.py`** — the `Adversary` model (name, level) and static `ADVERSARY_NAMES` list. `weighted_random_adversary()` down-weights adversaries that have been played more often at a given level, based on `Game` history, so the random picker nudges toward under-played combos.
- **`players.py`** — the `Player` model and static `PLAYERS`/`PLAYER_NAMES` lists (hardcoded to this group's regular players). `add_player()` mutates the in-memory lists only — it is **not persisted**, so new players added at runtime are lost on restart.
- **`elements.py`** — the fixed list of Spirit Island elements (`ELEMENTS`) and their emoji mapping (`ELEMENT_EMOJIS`), used for spirit filtering/display.

## Notable conventions / gotchas

- `DELETE_ENABLED` in `main.py` is gated on `os.getenv("USER") == "f4hy"` — delete-game UI is only enabled for that specific local user; the delete button is otherwise disabled for everyone else (including in deployment).
- Domain models (`Game`, `Adversary`, `Player`) are frozen pydantic models; `PlayerSpirit`/`Spirit`/`GameFilters` are not. Keep new domain records frozen where they represent an immutable saved record (needed since `Game` identity is derived from hashing its serialized content).
- `Spirit.__str__`/`Adversary.__str__` are used as the de facto identity/display key throughout stats code (`spirit_stats[str(spirit)]`, adversary keyed as `f"{name} (Lvl {level})"` in some places vs `str(adversary)` in others) — these two key formats are **not** interchangeable; check which one a given stats dict expects before matching keys.
- TYPE_CHECKING-guarded imports (`if TYPE_CHECKING: from game_history import Game`) are used in `players.py`/`adversary.py` to avoid circular imports with `game_history.py`, which imports from both. Follow this pattern if a domain module needs `Game` for type hints only.
