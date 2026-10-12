"""Shared offline birthplace reference points; never geocode personal inputs."""
import json
from pathlib import Path

CATALOG = json.loads((Path(__file__).resolve().parents[1] / 'dist/assets/birthplaces.json').read_text())
PLACES = {p['id']: p for p in CATALOG['places']}


def birthplace(city):
    return PLACES[city]
