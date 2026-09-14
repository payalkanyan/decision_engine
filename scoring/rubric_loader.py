from pathlib import Path

import yaml

from scoring.schemas import Rubric


def load_rubric(path: str | Path = "rubric.yaml") -> Rubric:
    """Load and parse rubric.yaml into a typed Rubric model.

    Single entry point for reading the rubric. The YAML is the source of
    truth for weights and criteria — this just validates and types it.
    """
    path = Path(path)
    with open(path) as f:
        raw = yaml.safe_load(f)
    return Rubric(**raw)
