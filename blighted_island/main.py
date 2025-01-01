from pydantic import BaseModel, Field, ValidationError
from collections import defaultdict
import streamlit as st
import spirits
import random
import time
import game_history
import adversary
import players


def main():
    st.title("Welcome to Blighted Island")
    st.subheader("Stats for spirit island")

    stats, random_spirit, game_tracker, history = st.tabs(
        ["Stats", "Choose a random Spirit", "Record New Game", "Game History"]
    )

    with random_spirit:
        if st.button("Randomize"):
            selected = spirits.random_spirit()
            st.subheader(f"{str(selected)}")
            st.write(f"complexity={selected.complexity}")

    with game_tracker:
        enter_and_record_game()

    games = game_history.list_games()
    with history:
        for g in games:
            player_str = ", ".join(p.player.name for p in g.players_played)
            with st.expander(
                f"{g.date_played} {player_str}  |  {g.adversary}",
                icon=("🏆" if g.won else "❌"),
            ):
                g.show()

    with stats:
        wins_and_losses(games)
        breakdown_by_adversary(games)
        breakdown_by_spirit(games)
        breakdown_by_player(games)


def wins_and_losses(games: list[game_history.Game]):
    col1, col2 = st.columns(2)
    col1.metric("wins", wins(games))
    col2.metric("losses", losses(games))


def wins(games: list[game_history.Game]):
    return len([game for game in games if game.won == True])


def losses(games: list[game_history.Game]):
    return len([game for game in games if game.won == False])


def breakdown_by_adversary(games: list[game_history.Game]):
    grouped = defaultdict(list)
    for game in games:
        grouped[game.adversary].append(game)
    st.divider()
    st.subheader("breakdown by adversary")
    data = [
        {
            "adversary": str(adversary),
            "wins": wins(games_for_adversary),
            "losses:": (-losses(games_for_adversary)),
        }
        for adversary, games_for_adversary in grouped.items()
    ]
    st.bar_chart(
        data, x="adversary", color=["#FF0000", "#0000FF"], height=400, horizontal=True
    )


def breakdown_by_spirit(games: list[game_history.Game]):
    grouped = defaultdict(list)
    for game in games:
        for player in game.players_played:
            grouped[str(player.spirit)].append(game)
    st.divider()
    st.subheader("breakdown by spirit")
    data = [
        {
            "spirit": str(spirit),
            "wins": wins(games_for_spirit),
            "losses:": (-losses(games_for_spirit)),
        }
        for spirit, games_for_spirit in grouped.items()
    ]
    st.bar_chart(
        data, x="spirit", color=["#FF0000", "#0000FF"], height=400, horizontal=True
    )


def breakdown_by_player(games: list[game_history.Game]):
    grouped = defaultdict(list)
    for game in games:
        for player in game.players_played:
            grouped[player.player.name].append(game)
    st.divider()
    st.subheader("breakdown by player")
    data = [
        {
            "player": str(player),
            "wins": wins(games_for_player),
            "losses:": (-losses(games_for_player)),
        }
        for player, games_for_player in grouped.items()
    ]
    st.bar_chart(
        data, x="player", color=["#FF0000", "#0000FF"], height=400, horizontal=True
    )


def enter_and_record_game():
    date_played = st.date_input("date_played")
    if not date_played:
        return
    player_counts = enumerate(["Two", "Three", "Four"], start=2)
    selected_count = st.segmented_control(
        label="Number of players", options=player_counts, format_func=lambda x: x[1]
    )
    if not selected_count:
        return None
    if selected_count:
        selected_adversary = adversary.enter_adversary()
        player_selections = [
            enter_player_spirit(i + 1) for i in range(selected_count[0])
        ]
    if not selected_adversary:
        st.warning("Must select an adversary")
        return None
    if not all(player_selections):
        st.warning("Must select all players and spirits")
        return None

    result = st.segmented_control(
        label="Result?",
        options=["won", "lost", "desync"],
    )
    if result is None:
        return
    if result == "desync":
        won = None
        desync = True
    else:
        desync = False
        won = result == "won"
    game = game_history.Game(
        date_played=date_played,
        adversary=selected_adversary,
        players_played=player_selections,
        won=won,
        desync=desync,
    )
    game.show()
    if st.button("Save", type="primary"):
        game_history.record_game(game)
        st.balloons()


def enter_player_spirit(player_number: int):
    selected_player = st.segmented_control(
        label=f"Player {player_number}",
        options=players.PLAYERS,
        format_func=lambda x: x.name,
        key=f"select_player{player_number}",
    )
    selected_spirit = st.selectbox(
        label="Select Spirit",
        options=spirits.SPIRITS,
        key=f"select_spirit_for_player{player_number}",
        index=None,
    )
    if selected_player and selected_spirit:
        try:
            return game_history.PlayerSpirit(
                player=selected_player, spirit=selected_spirit
            )
        except ValidationError:
            return None
    return None


if __name__ == "__main__":
    main()
