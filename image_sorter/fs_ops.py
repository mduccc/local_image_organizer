from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator
import shutil


def iter_images(
    src_root: Path,
    extensions: Iterable[str],
) -> Iterator[Path]:
    """
    Recursively yield image files under src_root with the given extensions.
    """
    exts = {ext.lower() for ext in extensions}
    for path in src_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in exts:
            yield path


def build_dest_path(
    src_file: Path,
    src_root: Path,
    dst_root: Path,
    category_id: str,
    keep_structure: bool,
) -> Path:
    """
    Build the destination path for a given source file and category.
    """
    category_root = dst_root / category_id
    if keep_structure:
        rel = src_file.relative_to(src_root).parent
        return category_root / rel / src_file.name
    return category_root / src_file.name


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _resolve_collision(dst: Path) -> Path:
    """
    If dst already exists, append (1), (2), ... before the suffix.
    """
    if not dst.exists():
        return dst

    stem = dst.stem
    suffix = dst.suffix
    parent = dst.parent

    index = 1
    while True:
        candidate = parent / f"{stem} ({index}){suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def move_or_copy(
    src: Path,
    dst: Path,
    move: bool,
    dry_run: bool,
) -> None:
    """
    Move or copy src to dst.
    """
    final_dst = _resolve_collision(dst)
    _ensure_parent_dir(final_dst)

    if dry_run:
        action = "MOVE" if move else "COPY"
        print(f"[DRY-RUN] {action} {src} -> {final_dst}")
        return

    if move:
        shutil.move(str(src), str(final_dst))
    else:
        shutil.copy2(str(src), str(final_dst))


__all__ = [
    "iter_images",
    "build_dest_path",
    "move_or_copy",
]

