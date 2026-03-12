from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def _resolve_config_dir(config_dir: Path | str | None = None) -> Path:
    if config_dir is not None:
        return Path(config_dir)
    return _DEFAULT_CONFIG_DIR.resolve()


def load_rules(config_dir: Path | str | None = None) -> dict[str, Any]:
    path = _resolve_config_dir(config_dir) / "rules.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("rules", {})


def load_thresholds(config_dir: Path | str | None = None) -> dict[str, Any]:
    path = _resolve_config_dir(config_dir) / "thresholds.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("thresholds", {})


def load_tiers(config_dir: Path | str | None = None) -> list[dict[str, Any]]:
    path = _resolve_config_dir(config_dir) / "thresholds.yaml"
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("tiers", [])
