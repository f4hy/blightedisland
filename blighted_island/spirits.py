from typing import Literal

Complexity = Literal["Very High", "High", "Moderate", "Low"]

SPIRITS: dict[str, Complexity] = {
    "Lightning's Swift Strike": "Low",
    "River Surges in Sunlight": "Low",
    "Shadows Flicker Like Flame": "Low",
    "Vital Strength of the Earth": "Low",
    "A Spread of Rampant Green": "Moderate",
    "Thunderspeaker": "Moderate",
    "Bringer of Dreams and Nightmares": "High",
    "Ocean's Hungry Grasp": "High",
}
