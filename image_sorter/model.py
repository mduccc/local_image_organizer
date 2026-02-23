from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

from PIL import Image
import numpy as np
import torch
import open_clip


@dataclass
class ClipResources:
    model: torch.nn.Module
    preprocess: callable
    tokenizer: callable
    device: torch.device


def load_clip_model(
    model_name: str,
    pretrained: str,
    device_str: str = "cpu",
) -> ClipResources:
    """
    Load a CLIP model and preprocessing pipeline.

    Uses open_clip_torch so it runs on CPU-only as well.
    """
    device = torch.device(device_str)
    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name,
        pretrained=pretrained,
    )
    tokenizer = open_clip.get_tokenizer(model_name)

    model.to(device)
    model.eval()

    return ClipResources(
        model=model,
        preprocess=preprocess,
        tokenizer=tokenizer,
        device=device,
    )


def encode_texts(
    texts: Iterable[str],
    resources: ClipResources,
    batch_size: int = 32,
) -> np.ndarray:
    """
    Encode a list of texts into CLIP text embeddings.
    Returns a numpy array of shape (N, D).
    """
    model = resources.model
    tokenizer = resources.tokenizer
    device = resources.device

    texts = list(texts)
    all_embeddings: List[np.ndarray] = []

    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            if not batch:
                continue
            tokens = tokenizer(batch).to(device)
            features = model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
            all_embeddings.append(features.cpu().numpy())

    if not all_embeddings:
        return np.zeros((0, 1), dtype=np.float32)

    return np.concatenate(all_embeddings, axis=0)


def encode_image(
    image: Image.Image,
    resources: ClipResources,
) -> np.ndarray:
    """
    Encode a single PIL image into a CLIP image embedding.
    Returns a numpy array of shape (D,).
    """
    model = resources.model
    preprocess = resources.preprocess
    device = resources.device

    img_tensor = preprocess(image).unsqueeze(0).to(device)

    with torch.no_grad():
        features = model.encode_image(img_tensor)
        features = features / features.norm(dim=-1, keepdim=True)

    return features.squeeze(0).cpu().numpy()


def cosine_similarities(
    image_embedding: np.ndarray,
    text_embeddings: np.ndarray,
) -> np.ndarray:
    """
    Compute cosine similarity between one image embedding (D,)
    and multiple text embeddings (N, D). Returns (N,).
    """
    if text_embeddings.size == 0:
        return np.zeros((0,), dtype=np.float32)

    img = image_embedding.astype(np.float32)
    txt = text_embeddings.astype(np.float32)

    img_norm = np.linalg.norm(img)
    txt_norms = np.linalg.norm(txt, axis=1)
    denom = img_norm * txt_norms
    denom[denom == 0] = 1e-8

    sims = (txt @ img) / denom
    return sims


__all__ = [
    "ClipResources",
    "load_clip_model",
    "encode_texts",
    "encode_image",
    "cosine_similarities",
]

