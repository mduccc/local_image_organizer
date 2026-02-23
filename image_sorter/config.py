from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

import yaml


@dataclass
class CategoryConfig:
    id: str
    name: str
    prompts: List[str]


@dataclass
class ModelConfig:
    name: str
    pretrained: str
    device: str = "cpu"


@dataclass
class ThresholdConfig:
    similarity_min: float = 0.22


@dataclass
class BehaviorConfig:
    move_files: bool = True
    keep_folder_structure: bool = False
    dry_run: bool = True


@dataclass
class FilesConfig:
    extensions: List[str]


@dataclass
class AppConfig:
    model: ModelConfig
    categories: List[CategoryConfig]
    thresholds: ThresholdConfig
    behavior: BehaviorConfig
    files: FilesConfig


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(path: Path) -> AppConfig:
    """Load application configuration from a YAML file."""
    raw = _load_yaml(path)

    model_raw = raw.get("model") or {}
    model_cfg = ModelConfig(
        name=str(model_raw.get("name", "ViT-B-32")),
        pretrained=str(model_raw.get("pretrained", "laion2b_s34b_b79k")),
        device=str(model_raw.get("device", "cpu")),
    )

    categories_raw = raw.get("categories") or []
    categories_cfg = [
        CategoryConfig(
            id=str(item["id"]),
            name=str(item.get("name", item["id"])),
            prompts=[str(p) for p in item.get("prompts") or []],
        )
        for item in categories_raw
        if "id" in item
    ]

    thresholds_raw = raw.get("thresholds") or {}
    thresholds_cfg = ThresholdConfig(
        similarity_min=float(thresholds_raw.get("similarity_min", 0.22)),
    )

    behavior_raw = raw.get("behavior") or {}
    behavior_cfg = BehaviorConfig(
        move_files=bool(behavior_raw.get("move_files", True)),
        keep_folder_structure=bool(behavior_raw.get("keep_folder_structure", False)),
        dry_run=bool(behavior_raw.get("dry_run", True)),
    )

    files_raw = raw.get("files") or {}
    extensions_raw = files_raw.get("extensions") or [".jpg", ".jpeg", ".png"]
    files_cfg = FilesConfig(
        extensions=[ext.lower() for ext in extensions_raw],
    )

    return AppConfig(
        model=model_cfg,
        categories=categories_cfg,
        thresholds=thresholds_cfg,
        behavior=behavior_cfg,
        files=files_cfg,
    )


__all__ = [
    "CategoryConfig",
    "ModelConfig",
    "ThresholdConfig",
    "BehaviorConfig",
    "FilesConfig",
    "AppConfig",
    "load_config",
]

