import streamlit as st
import spirits
import random
import time


def main():
    st.title("Welcome to Blighted Island")
    st.subheader("Stats for spirit island")

    random_spirit, game_tracker = st.tabs(
        ["Choose a random Spirit", "Track Game Stats"]
    )

    with random_spirit:
        choices = list(spirits.SPIRITS.keys())
        if st.button("Randomize"):
            selected = random.choice(choices)
            bar = st.progress(0, text="")
            for i in range(50):
                time.sleep(0.1)
                bar.progress(i * 2, text=random.choice(choices))
            time.sleep(0.1)
            bar.empty()
            st.write(selected)
            st.write(f"Complexity: {spirits.SPIRITS[selected]}")

    with game_tracker:
        st.write("soon.")


if __name__ == "__main__":
    main()
