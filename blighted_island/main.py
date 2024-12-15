from pydantic import BaseModel, Field, ValidationError

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

    random_spirit, game_tracker, history = st.tabs(
        ["Choose a random Spirit", "Record New Game", "Game History"]
    )

    with random_spirit:
        choices = spirits.SPIRITS
        if st.button("Randomize"):
            selected = random.choice(choices)
            bar = st.progress(0, text="")
            for i in range(50):
                time.sleep(0.01)
                bar.progress(i * 2, text=str(random.choice(choices)))
            time.sleep(0.1)
            bar.empty()
            st.subheader(f"{str(selected)}")
            st.write(f"complexity={selected.complexity}")

    with game_tracker:
        enter_and_record_game()

    with history:
        games = game_history.list_games()
        for g in games:
            player_str = ", ".join(p.player.name for p in g.players_played)
            with st.expander(
                f"{g.date_played} {player_str}", icon=("🏆" if g.won else "❌")
            ):
                g.show()


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
        options=[True, False],
        format_func=lambda x: "Won" if x else "Lost",
    )
    if result is None:
        return
    game = game_history.Game(
        adversary=selected_adversary, players_played=player_selections, won=result
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
