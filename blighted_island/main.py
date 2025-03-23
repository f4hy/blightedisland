"""
Main application module for Blighted Island.
Provides UI for tracking Spirit Island board game plays.

This application helps players track their Spirit Island board game sessions,
including which spirits and adversaries were played, game outcomes, and statistical
analysis of play patterns and win rates.
"""

from collections import defaultdict
import streamlit as st
import pandas as pd
import altair as alt
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import date, timedelta
import json
import calendar
import os
import tempfile
from io import StringIO

# Import project modules
import spirits
import adversary
import players
import game_history
from config import (
    APP_TITLE,
    APP_SUBTITLE,
    CHART_COLORS,
    CHART_HEIGHT,
    WIN_LABEL,
    LOSS_LABEL,
    DESYNC_LABEL,
    RESULT_OPTIONS,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    # Set page configuration
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🏝️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Application header
    st.title(f"🏝️ {APP_TITLE}")
    st.subheader(APP_SUBTITLE)

    # Create tabs for different app sections
    tabs = st.tabs(
        [
            "📊 Stats",
            "🎲 Random Spirit",
            "👿 Random Adversary",
            "📝 Record Game",
            "📜 Game History",
            "⚙️ Settings",
        ]
    )

    # Load game data
    games = game_history.list_games()

    # Tab 1: Stats
    with tabs[0]:
        render_stats_tab(games)

    # Tab 2: Random Spirit
    with tabs[1]:
        render_random_spirit_tab()

    # Tab 3: Random Adversary
    with tabs[2]:
        render_random_adversary_tab(games)

    # Tab 4: Record Game
    with tabs[3]:
        render_record_game_tab()

    # Tab 5: Game History
    with tabs[4]:
        render_game_history_tab(games)

    # Tab 6: Settings
    with tabs[5]:
        render_settings_tab(games)

    # Add footer with version info
    st.markdown("---")
    st.markdown("**Blighted Island** v1.1.0 | Made with ❤️ for Spirit Island fans")
    st.markdown("*Remember: The island will endure. The invaders will not.*")


def wins(games: List[game_history.Game]) -> int:
    """Count wins in a list of games."""
    return len([game for game in games if game.won is True])


def losses(games: List[game_history.Game]) -> int:
    """Count losses in a list of games."""
    return len([game for game in games if game.won is False])


def desyncs(games: List[game_history.Game]) -> int:
    """Count desyncs (unfinished games) in a list of games."""
    return len([game for game in games if game.won is None])


def render_stats_tab(games: List[game_history.Game]) -> None:
    """
    Render the statistics tab of the application.

    Args:
        games: List of all recorded games
    """
    st.write("### Game Statistics")

    if not games:
        st.info("No recorded games yet. Start recording games to see statistics!")
        return

    # Set up filters
    filters = game_history.set_filters()
    filtered_games = game_history.filter_games(games, filters)

    if not filtered_games:
        st.warning("No games match the selected filters.")
        return

    # Game count metrics
    total_games = len(filtered_games)
    num_wins = wins(filtered_games)
    num_losses = losses(filtered_games)
    num_desyncs = desyncs(filtered_games)
    win_rate = (
        round(num_wins / (num_wins + num_losses) * 100, 1)
        if (num_wins + num_losses) > 0
        else 0
    )

    # Summary metrics display
    cols = st.columns(4)
    cols[0].metric("Total Games", total_games)
    cols[1].metric("Wins", num_wins)
    cols[2].metric("Losses", num_losses)
    cols[3].metric("Win Rate", f"{win_rate}%")

    # Display trend of wins over time
    st.write("### Win/Loss Trend")
    display_win_loss_trend(filtered_games)

    # Display all the breakdowns
    st.write("### Game Analysis")
    tab1, tab2, tab3 = st.tabs(["By Adversary", "By Spirit", "By Player"])

    with tab1:
        breakdown_by_adversary(filtered_games)

    with tab2:
        breakdown_by_spirit(filtered_games)

    with tab3:
        breakdown_by_player(filtered_games)


def render_random_spirit_tab() -> None:
    """
    Render the random spirit selector tab.
    """
    st.write("### Random Spirit Selector")
    st.write("Get a random spirit to play in your next game!")

    # Add complexity filter
    complexities = ["Any", "Low", "Moderate", "High", "Very High"]
    selected_complexity = st.radio(
        "Filter by complexity:", complexities, horizontal=True
    )

    complexity_filter = None if selected_complexity == "Any" else selected_complexity

    # Randomize button
    if st.button("🎲 Randomize Spirit", type="primary"):
        selected = spirits.random_spirit(complexity_filter)

        # Display in a nice card-like format
        col1, col2 = st.columns([1, 2])

        with col1:
            try:
                spirits.spirit_image(selected)
            except Exception:
                st.image("https://via.placeholder.com/150?text=Spirit+Image", width=150)

        with col2:
            st.subheader(selected.display_name)
            st.write(f"**Complexity:** {selected.complexity}")

            # Get spirit stats if we have game data
            games = game_history.list_games()
            if games:
                spirit_stats = spirits.get_spirit_stats(games)
                spirit_key = str(selected)

                if spirit_key in spirit_stats:
                    stats = spirit_stats[spirit_key]
                    st.write(
                        f"**Win Rate:** {stats['win_pct']}% ({stats['wins']}/{stats['total']} games)"
                    )
                else:
                    st.write("*No recorded games with this spirit yet.*")


def render_random_adversary_tab(games: List[game_history.Game]) -> None:
    """
    Render the random adversary selector tab.

    Args:
        games: List of all recorded games
    """
    st.write("### Random Adversary Selector")
    st.write("Get a random adversary to challenge you in your next game!")

    level = st.slider(
        "Choose adversary level",
        min_value=0,
        max_value=6,
        value=3,
        help="Higher levels are more difficult",
    )

    col1, col2 = st.columns(2)

    picked: Optional[adversary.Adversary] = None

    with col1:
        if st.button("🎲 Random Adversary", type="primary"):
            picked = adversary.random_adversary(level)

    with col2:
        if st.button(
            "⚖️ Weighted Random Adversary",
            help="Selects adversaries you've played less frequently",
        ):
            picked = adversary.weighted_random_adversary(level, games)

    if picked:
        st.success(f"Your adversary: **{picked.name}** (Level {picked.level})")

        # Display adversary stats if available
        adversary_stats = adversary.get_adversary_stats(games)
        adv_key = f"{picked.name} (Lvl {picked.level})"

        if adv_key in adversary_stats:
            stats = adversary_stats[adv_key]
            st.metric(
                "Win Rate",
                f"{stats['win_pct']}% ({stats['wins']}/{stats['total']} games)",
            )


def render_record_game_tab() -> None:
    """
    Render the tab for recording new games.
    """
    st.write("### Record New Game")
    st.write("Enter the details of your game session below:")

    # Game date
    date_played = st.date_input("Date played", value=date.today())

    # Number of players - simplified to avoid select_slider issues
    player_count_options = ["Two", "Three", "Four", "Five", "Six"]
    player_count_values = {"Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6}

    selected_count_name = st.radio(
        "Number of players", options=player_count_options, index=0, horizontal=True
    )

    selected_count_num = player_count_values[selected_count_name]

    # Select adversary
    selected_adversary = adversary.enter_adversary()

    # Create players section
    player_selections = []

    if selected_adversary:
        with st.expander("Enter Players and Spirits", expanded=True):
            for i in range(selected_count_num):
                st.write(f"#### Player {i + 1}")
                col1, col2 = st.columns(2)

                with col1:
                    selected_player = st.selectbox(
                        "Select Player",
                        options=players.PLAYERS,
                        format_func=lambda x: x.name,
                        key=f"select_player{i + 1}",
                    )

                with col2:
                    selected_spirit = spirits.select_spirit(
                        key=f"select_spirit_for_player{i + 1}"
                    )

                if selected_player and selected_spirit:
                    player_selections.append(
                        game_history.PlayerSpirit(
                            player=selected_player, spirit=selected_spirit
                        )
                    )

    # Game result
    result = st.radio("Result", options=RESULT_OPTIONS, horizontal=True, index=None)

    # Notes field
    notes = st.text_area(
        "Game Notes (optional)", placeholder="Enter any observations about the game..."
    )

    # Handle result
    if result is None:
        won, desync = None, None
    elif result == DESYNC_LABEL:
        won, desync = None, True
    else:
        won = result == WIN_LABEL
        desync = False

    # Validation
    all_inputs_valid = (
        date_played is not None
        and selected_adversary is not None
        and len(player_selections) == selected_count_num
        and result is not None
    )

    # Preview and save
    if all_inputs_valid:
        st.write("### Game Summary")

        game = game_history.Game(
            date_played=date_played,
            adversary=selected_adversary,
            players_played=player_selections,
            won=won,
            desync=desync,
            notes=notes if notes else None,
        )

        game.show()

        if st.button("💾 Save Game", type="primary"):
            if game_history.record_game(game):
                st.balloons()
                st.success("Game recorded successfully!")
            else:
                st.error("Failed to save game record!")
    else:
        if not date_played:
            st.warning("Please select a date.")
        if not selected_adversary:
            st.warning("Please select an adversary.")
        if len(player_selections) != selected_count_num:
            st.warning("Please select all players and spirits.")
        if result is None:
            st.warning("Please select a game result.")


def render_game_history_tab(games: List[game_history.Game]) -> None:
    """
    Render the game history tab.

    Args:
        games: List of all recorded games
    """
    st.write("### Game History")

    if not games:
        st.info(
            "No games recorded yet! Use the 'Record Game' tab to add your first game."
        )
        return

    # Search/filter options
    search_term = st.text_input("Search games", placeholder="Type to search...")

    # Sort options
    sort_options = {
        "Newest first": lambda g: g.date_played,
        "Oldest first": lambda g: -g.date_played,
        "Adversary (A-Z)": lambda g: g.adversary.name,
        "Adversary level (high-low)": lambda g: -g.adversary.level,
    }

    sort_by = st.selectbox("Sort by", options=list(sort_options.keys()))
    sort_func = sort_options[sort_by]

    # Filter and sort games
    filtered_games = games

    if search_term:
        search_lower = search_term.lower()
        filtered_games = [
            g
            for g in games
            if (
                search_lower in g.adversary.name.lower()
                or any(
                    search_lower in ps.player.name.lower() for ps in g.players_played
                )
                or any(
                    search_lower in str(ps.spirit).lower() for ps in g.players_played
                )
            )
        ]

    # Sort the games
    sorted_games = sorted(
        filtered_games, key=sort_func, reverse=(sort_by == "Newest first")
    )

    # Display games
    for i, g in enumerate(sorted_games):
        player_str = ", ".join(p.player.name for p in g.players_played)

        # Determine icon based on result
        if g.won is True:
            icon = "🏆"
        elif g.won is False:
            icon = "❌"
        else:
            icon = "⚠️"

        with st.expander(
            f"{icon} | {g.date_played} | {g.adversary} | {player_str} ", expanded=False
        ):
            g.show()

            # Edit and delete buttons with unique key using index
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(
                    "🗑️ Delete",
                    key=f"delete_game_{i}",
                    help="Delete this game record",
                    disabled=True,
                ):
                    # Delete functionality would be implemented here
                    st.warning("Delete functionality not implemented yet")


def render_settings_tab(games: List[game_history.Game]) -> None:
    """
    Render the settings tab.

    Args:
        games: List of all recorded games
    """
    st.write("### Application Settings")

    # Export/import data section
    st.write("#### 📤 Export / Import Data")

    export_col, import_col = st.columns(2)

    with export_col:
        st.write("Export your game history as JSON")
        if st.button("📥 Export Game Data", type="primary"):
            if games:
                export_data = game_history.export_games(games)

                # Create a download button
                st.download_button(
                    label="Download JSON",
                    data=export_data,
                    file_name=f"spirit_island_games_{date.today()}.json",
                    mime="application/json",
                )
            else:
                st.info("No games to export!")

    with import_col:
        st.write("Import game history from JSON")
        uploaded_file = st.file_uploader("Choose a JSON file", type=["json"])

        if uploaded_file is not None:
            import_data = uploaded_file.read().decode("utf-8")

            if st.button("📤 Import Games", type="primary"):
                imported, failed = game_history.import_games(import_data)

                if imported > 0:
                    st.success(f"Successfully imported {imported} games!")

                if failed > 0:
                    st.warning(
                        f"Failed to import {failed} games due to validation errors."
                    )

    # Manage players section
    st.write("#### 👥 Manage Players")

    # This would be more functional in a real implementation
    st.write("Player management functionality would be implemented here")

    # Display app info
    st.write("#### ℹ️ About")
    st.write(
        "**Blighted Island** is a stat tracking app for the Spirit Island board game."
    )
    st.write("Version: 1.1.0")
    st.write("Made with Streamlit and Python")

    # Reset application data
    st.write("#### 🔄 Reset Application")
    if st.button(
        "🗑️ Reset All Data",
        type="primary",
        help="This will delete all your game history!",
        disabled=True,
    ):
        # This would clear all data in a real implementation
        st.warning(
            "This would delete all your data. Reset functionality not implemented in this demo."
        )


def display_win_loss_trend(games: List[game_history.Game]) -> None:
    """
    Display a chart showing the win/loss trend over time.

    Args:
        games: List of games to analyze
    """
    if not games:
        st.info("No games to analyze.")
        return

    # Prepare data for chart
    date_results = [
        {
            "date": g.date_played,
            "result": "Win" if g.won else "Loss" if g.won is False else "Desync",
        }
        for g in sorted(games, key=lambda x: x.date_played)
    ]

    # Convert to DataFrame
    df = pd.DataFrame(date_results)

    # Create running win/loss count
    if not df.empty:
        df["win_count"] = (df["result"] == "Win").cumsum()
        df["loss_count"] = (df["result"] == "Loss").cumsum()
        df["total_count"] = df.index + 1
        df["win_rate"] = (df["win_count"] / (df["win_count"] + df["loss_count"])) * 100

        # Create line chart with Altair
        win_rate_chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y(
                    "win_rate:Q", title="Win Rate (%)", scale=alt.Scale(domain=[0, 100])
                ),
                tooltip=["date", "win_rate", "win_count", "loss_count"],
            )
            .properties(width=800, height=300, title="Win Rate Over Time")
        )

        st.altair_chart(win_rate_chart, use_container_width=True)
    else:
        st.info("No win/loss data to display.")


def breakdown_by_adversary(games: List[game_history.Game]) -> None:
    """
    Display statistics broken down by adversary.

    Args:
        games: List of games to analyze
    """
    if not games:
        st.info("No games to analyze.")
        return

    # Group games by adversary
    grouped = defaultdict(list)
    for game in games:
        key = f"{game.adversary.name} (Lvl {game.adversary.level})"
        grouped[key].append(game)

    # Prepare data for chart
    data = []
    for adversary_name, games_for_adversary in grouped.items():
        win_count = wins(games_for_adversary)
        loss_count = losses(games_for_adversary)
        total = win_count + loss_count
        win_rate = round(win_count / total * 100, 1) if total > 0 else 0

        data.append(
            {
                "adversary": adversary_name,
                "wins": win_count,
                "losses": loss_count,
                "total": total,
                "win_rate": win_rate,
            }
        )

    # Sort by win rate
    data.sort(key=lambda x: x["win_rate"], reverse=True)

    # Convert to DataFrame for display
    df = pd.DataFrame(data)

    # Display as table
    st.dataframe(
        df,
        column_config={
            "adversary": "Adversary",
            "wins": "Wins",
            "losses": "Losses",
            "total": "Total Games",
            "win_rate": st.column_config.ProgressColumn(
                "Win Rate",
                format="%{.1f}%",
                min_value=0,
                max_value=100,
            ),
        },
        hide_index=True,
    )

    # Create bar chart
    if not df.empty:
        chart_data = pd.melt(
            df,
            id_vars=["adversary"],
            value_vars=["wins", "losses"],
            var_name="result",
            value_name="count",
        )

        # Display horizontal bar chart
        st.bar_chart(
            data=df,
            x="adversary",
            y=["wins", "losses"],
            color=CHART_COLORS,
            height=CHART_HEIGHT,
        )


def breakdown_by_spirit(games: List[game_history.Game]) -> None:
    """
    Display statistics broken down by spirit.

    Args:
        games: List of games to analyze
    """
    if not games:
        st.info("No games to analyze.")
        return

    # Group games by spirit
    grouped = defaultdict(list)
    for game in games:
        for player in game.players_played:
            spirit_name = str(player.spirit)
            grouped[spirit_name].append(game)

    # Prepare data for chart
    data = []
    for spirit_name, games_for_spirit in grouped.items():
        win_count = wins(games_for_spirit)
        loss_count = losses(games_for_spirit)
        total = win_count + loss_count
        win_rate = round(win_count / total * 100, 1) if total > 0 else 0

        data.append(
            {
                "spirit": spirit_name,
                "wins": win_count,
                "losses": loss_count,
                "total": total,
                "win_rate": win_rate,
            }
        )

    # Sort by win rate
    data.sort(key=lambda x: x["win_rate"], reverse=True)

    # Convert to DataFrame for display
    df = pd.DataFrame(data)

    # Display as table
    st.dataframe(
        df,
        column_config={
            "spirit": "Spirit",
            "wins": "Wins",
            "losses": "Losses",
            "total": "Total Games",
            "win_rate": st.column_config.ProgressColumn(
                "Win Rate",
                format="%{.1f}%",
                min_value=0,
                max_value=100,
            ),
        },
        hide_index=True,
    )

    # Create bar chart
    if not df.empty:
        # Display horizontal bar chart
        st.bar_chart(
            data=df,
            x="spirit",
            y=["wins", "losses"],
            color=CHART_COLORS,
            height=CHART_HEIGHT,
        )


def breakdown_by_player(games: List[game_history.Game]) -> None:
    """
    Display statistics broken down by player.

    Args:
        games: List of games to analyze
    """
    if not games:
        st.info("No games to analyze.")
        return

    # Group games by player
    grouped = defaultdict(list)
    for game in games:
        for player in game.players_played:
            player_name = player.player.name
            grouped[player_name].append(game)

    # Prepare data for chart
    data = []
    for player_name, games_for_player in grouped.items():
        win_count = wins(games_for_player)
        loss_count = losses(games_for_player)
        total = win_count + loss_count
        win_rate = round(win_count / total * 100, 1) if total > 0 else 0

        data.append(
            {
                "player": player_name,
                "wins": win_count,
                "losses": loss_count,
                "total": total,
                "win_rate": win_rate,
            }
        )

    # Sort by win rate
    data.sort(key=lambda x: x["win_rate"], reverse=True)

    # Convert to DataFrame for display
    df = pd.DataFrame(data)

    # Display as table
    st.dataframe(
        df,
        column_config={
            "player": "Player",
            "wins": "Wins",
            "losses": "Losses",
            "total": "Total Games",
            "win_rate": st.column_config.ProgressColumn(
                "Win Rate",
                format="%{.1f}%",
                min_value=0,
                max_value=100,
            ),
        },
        hide_index=True,
    )

    # Create bar chart
    if not df.empty:
        # Display horizontal bar chart
        st.bar_chart(
            data=df,
            x="player",
            y=["wins", "losses"],
            color=CHART_COLORS,
            height=CHART_HEIGHT,
        )


if __name__ == "__main__":
    main()
