"""Utilities for the spiders."""

import re
from typing import Tuple

type Coordinates = Tuple[float, float]
"""[Longitude, Latitude]"""


def extract_coordinates(text: str) -> Coordinates | None:
    """Extract and parse coordinates substring from a Matricula html document."""
    # coordinates information can be extracted from a script tag inside a Matricula HTML page
    # example: `POINT (16.373 48.208)`
    # this substring
    pattern = r"POINT \((-?\d+\.\d+)\s+(-?\d+\.\d+)\)"
    matches = re.search(pattern, text)
    if not matches:
        return None
    try:
        longitutde = float(matches.group(1))
        latitude = float(matches.group(2))
    except Exception as _:
        return None
    return (longitutde, latitude)
