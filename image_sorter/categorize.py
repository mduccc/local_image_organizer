from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional

import numpy as np

from .config import CategoryConfig, AppConfig
from .model import ClipResources, encode_texts, cosine_similarities


@dataclass
class Category:
    id: str
    name: str
    prompts: List[str]
    embedding: np.ndarray  # shape (D,)


def build_categories(
    cfg: AppConfig,
    resources: ClipResources,
) -> List[Category]:
    """
    Build category objects and compute a single embedding per category
    by averaging embeddings of its prompts.
    """
    categories: List[Category] = []

    for cat_cfg in cfg.categories:
        prompts = cat_cfg.prompts or [cat_cfg.name]
        text_embs = encode_texts(prompts, resources)

        if text_embs.size == 0:
            # Fallback to a zero vector; this category will never be picked
            mean_emb = np.zeros((1,), dtype=np.float32)
        else:
            mean_emb = text_embs.mean(axis=0)
            norm = np.linalg.norm(mean_emb)
            if norm > 0:
                mean_emb = mean_emb / norm

        categories.append(
            Category(
                id=cat_cfg.id,
                name=cat_cfg.name,
                prompts=prompts,
                embedding=mean_emb.astype(np.float32),
            )
        )

    return categories


def categorize_image(
    image_embedding: np.ndarray,
    categories: List[Category],
    similarity_min: float,
) -> Tuple[str, float]:
    """
    Given an image embedding, pick the best category.

    Returns:
      (category_id, similarity_score)
      If best similarity < similarity_min, returns ("uncategorized", best_score).
    """
    if not categories:
        return "uncategorized", 0.0

    cat_matrix = np.stack([c.embedding for c in categories], axis=0)
    sims = cosine_similarities(image_embedding, cat_matrix)

    best_idx = int(np.argmax(sims))
    best_score = float(sims[best_idx])
    best_cat = categories[best_idx]

    if best_score < similarity_min:
        return "uncategorized", best_score

    return best_cat.id, best_score


__all__ = [
    "Category",
    "build_categories",
    "categorize_image",
]

