import random
from typing import Literal
from pydantic import BaseModel
import streamlit as st
import urllib.parse

Complexity = Literal["Very High", "High", "Moderate", "Low"]


class Spirit(BaseModel):
    name: str
    complexity: Complexity
    aspect: str | None = None

    def __str__(self):
        if self.aspect:
            return f"{self.name}[{self.aspect}]"
        return f"{self.name}"


def spirit_image(spirit: Spirit):
    root = "https://spiritislandwiki.com/images/c/c2/"
    name = spirit.name.replace(" ", "_")
    filename = urllib.parse.quote_plus(name) + ".png"
    path = f"{root}{filename}"
    st.write(path)
    st.image(path)


SPIRITS: list[Spirit] = sorted(
    [
        Spirit(name="Lightning's Swift Strike", complexity="Low"),
        Spirit(name="Lightning's Swift Strike", complexity="Low", aspect="Panda"),
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
        Spirit(name="A Spread of Rampant Green", complexity="Moderate"),
        Spirit(name="Thunderspeaker", complexity="Moderate"),
        Spirit(name="Bringer of Dreams and Nightmares", complexity="High"),
        Spirit(name="Ocean's Hungry Grasp", complexity="High"),
        Spirit(name="Keeper of the Forbidden Wilds", complexity="Moderate"),
        Spirit(name="Sharp Fangs Behind the Leaves", complexity="Moderate"),
        Spirit(name="Heart of the Wildfire", complexity="High"),
        Spirit(name="Serpent Slumbering Beneath the Island", complexity="High"),
        Spirit(name="Lure of the Deep Wilderness", complexity="Moderate"),
        Spirit(name="Many Minds Move as One", complexity="Moderate"),
        Spirit(name="Stone's Unyielding Defiance", complexity="Moderate"),
        Spirit(name="Volcano Looming High", complexity="Moderate"),
        Spirit(name="Vengeance as a Burning Plague", complexity="High"),
        Spirit(name="Fractured Days Split the Sky", complexity="Very High"),
        Spirit(name="Devouring Teeth Lurk Underfoot", complexity="Low"),
        Spirit(name="Eyes Watch from the Trees", complexity="Low"),
        Spirit(name="Fathomless Mud of the Swamp", complexity="Low"),
        Spirit(name="Rising Heat of Stone and Sand", complexity="Low"),
        Spirit(name="Sun-Bright Whirlwind", complexity="Low"),
        Spirit(name="Shroud of Silent Mist", complexity="High"),
    ],
    key=str,
)


def random_spirit():
    """Get a random spirit, don't count aspects twice."""
    spirit_names = {s.name for s in SPIRITS}
    selected_name = random.choice(list(spirit_names))
    aspects = [s for s in SPIRITS if selected_name == s.name]
    return random.choice(aspects)
