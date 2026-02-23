from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, UnidentifiedImageError

try:
    import rawpy  # type: ignore
except Exception:  # pragma: no cover
    rawpy = None  # type: ignore


def _load_with_pillow(path: Path) -> Image.Image:
    with Image.open(path) as img:
        return img.convert("RGB")


def _load_with_rawpy(path: Path) -> Image.Image:
    if rawpy is None:
        raise ImportError(
            "rawpy is required to read RAW files. Install dependencies via: pip install -r requirements.txt"
        )

    with rawpy.imread(str(path)) as raw:
        rgb: np.ndarray = raw.postprocess(
            output_color=rawpy.ColorSpace.sRGB,
            use_camera_wb=True,
            no_auto_bright=True,
        )
    return Image.fromarray(rgb, mode="RGB")


def load_image_rgb(path: Path) -> Image.Image:
    """
    Load an image from disk and return an RGB PIL image.

    - For common formats (jpg/png/heic/...), uses Pillow.
    - For RAW files, falls back to rawpy (LibRaw) and converts to sRGB.
    """
    try:
        return _load_with_pillow(path)
    except (UnidentifiedImageError, OSError) as e_pil:
        # Try RAW loader; if that also fails, normalize as an UnidentifiedImageError
        try:
            return _load_with_rawpy(path)
        except Exception as e_raw:
            raise UnidentifiedImageError(
                f"Cannot read image {path}: {e_pil} / {e_raw}"
            ) from e_raw


__all__ = ["load_image_rgb"]

