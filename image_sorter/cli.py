from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image, UnidentifiedImageError
from tqdm import tqdm

from .config import load_config, AppConfig
from .model import load_clip_model, encode_image
from .categorize import build_categories, categorize_image
from .fs_ops import iter_images, build_dest_path, move_or_copy


@dataclass
class CliArgs:
    src: Path
    dst: Path
    config: Path
    dry_run: Optional[bool]
    move_files: Optional[bool]
    keep_structure: Optional[bool]
    max_images: Optional[int]


def parse_args() -> CliArgs:
    parser = argparse.ArgumentParser(
        description="Organize local images into folders using a local CLIP model."
    )

    parser.add_argument(
        "--src",
        type=Path,
        required=True,
        help="Source directory containing unsorted images.",
    )
    parser.add_argument(
        "--dst",
        type=Path,
        required=True,
        help="Destination directory for sorted images.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to YAML configuration file.",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Print planned actions without actually moving/copying files.",
    )
    parser.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Disable dry-run mode (will actually move/copy files).",
    )
    parser.set_defaults(dry_run=None)

    parser.add_argument(
        "--move",
        dest="move_files",
        action="store_true",
        help="Move files instead of copying.",
    )
    parser.add_argument(
        "--copy",
        dest="move_files",
        action="store_false",
        help="Copy files instead of moving.",
    )
    parser.set_defaults(move_files=None)

    parser.add_argument(
        "--keep-structure",
        dest="keep_structure",
        action="store_true",
        help="Keep original folder structure under each category folder.",
    )
    parser.add_argument(
        "--flat",
        dest="keep_structure",
        action="store_false",
        help="Do not keep original folder structure (default from config).",
    )
    parser.set_defaults(keep_structure=None)

    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="Only process at most this many images (for testing).",
    )

    ns = parser.parse_args()

    return CliArgs(
        src=ns.src,
        dst=ns.dst,
        config=ns.config,
        dry_run=ns.dry_run,
        move_files=ns.move_files,
        keep_structure=ns.keep_structure,
        max_images=ns.max_images,
    )


def _apply_cli_overrides(cfg: AppConfig, args: CliArgs) -> AppConfig:
    # Behavior overrides
    if args.dry_run is not None:
        cfg.behavior.dry_run = bool(args.dry_run)
    if args.move_files is not None:
        cfg.behavior.move_files = bool(args.move_files)
    if args.keep_structure is not None:
        cfg.behavior.keep_folder_structure = bool(args.keep_structure)
    return cfg


def main() -> None:
    args = parse_args()

    if not args.src.is_dir():
        raise SystemExit(f"Source directory does not exist or is not a directory: {args.src}")

    cfg = load_config(args.config)
    cfg = _apply_cli_overrides(cfg, args)

    print(f"Loading CLIP model {cfg.model.name} ({cfg.model.pretrained}) on {cfg.model.device}...")
    resources = load_clip_model(
        model_name=cfg.model.name,
        pretrained=cfg.model.pretrained,
        device_str=cfg.model.device,
    )

    print("Preparing category embeddings...")
    categories = build_categories(cfg, resources)
    print(f"Loaded {len(categories)} categories.")

    # Collect image list
    print(f"Scanning for images under {args.src} ...")
    images = list(iter_images(args.src, cfg.files.extensions))
    if args.max_images is not None:
        images = images[: args.max_images]
    print(f"Found {len(images)} image(s) to process.")

    total = 0
    per_category_counts = {}
    uncategorized_count = 0

    for img_path in tqdm(images, desc="Processing images", unit="img"):
        try:
            with Image.open(img_path) as img:
                img = img.convert("RGB")
                img_emb = encode_image(img, resources)
        except (UnidentifiedImageError, OSError) as e:
            print(f"Skipping unreadable image {img_path}: {e}")
            continue

        cat_id, score = categorize_image(
            image_embedding=img_emb,
            categories=categories,
            similarity_min=cfg.thresholds.similarity_min,
        )

        if cat_id == "uncategorized":
            uncategorized_count += 1
        per_category_counts[cat_id] = per_category_counts.get(cat_id, 0) + 1
        total += 1

        dst_path = build_dest_path(
            src_file=img_path,
            src_root=args.src,
            dst_root=args.dst,
            category_id=cat_id,
            keep_structure=cfg.behavior.keep_folder_structure,
        )
        move_or_copy(
            src=img_path,
            dst=dst_path,
            move=cfg.behavior.move_files,
            dry_run=cfg.behavior.dry_run,
        )

    print("\nSummary:")
    print(f"  Total processed images: {total}")
    for cid, count in sorted(per_category_counts.items(), key=lambda x: x[0]):
        print(f"  {cid}: {count}")
    print(f"  Uncategorized: {uncategorized_count}")
    print(f"  Dry-run mode: {cfg.behavior.dry_run}")
    print(f"  Operation: {'MOVE' if cfg.behavior.move_files else 'COPY'}")


if __name__ == "__main__":
    main()

