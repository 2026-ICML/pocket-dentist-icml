"""
Loaders for the curated MetaDent QA pairs + image-path resolution.

The QA *annotations* (vqa / classification / captioning) ship in this repo under
``annotations/``. The intraoral *images* they reference are NOT redistributed
here; obtain them from the original source datasets (see ``download_images`` /
``SOURCE_DATASETS``) under their own terms, then point
``$POCKET_DENTIST_IMAGES`` at the directory.

Image resolution order:
  1. ``$POCKET_DENTIST_IMAGES`` if set
  2. ``./images`` next to this file
Each image id resolves to ``<id>.jpg`` or ``<id>.png``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ANN = _HERE / "annotations"

# The benchmark builds on three public dental datasets. Images are NOT
# redistributed here — download them from the original sources under their own
# terms. The released QA annotations correspond to the MetaDent intraoral photos.
SOURCE_DATASETS = {
    "MetaDent (intraoral photos; images for these annotations)":
        "https://doi.org/10.1177/00220345261424242",
    "BRAR (panoramic radiographs)":
        "https://doi.org/10.1038/s41597-025-06400-y",
    "DR (panoramic radiographs)":
        "https://www.kaggle.com/datasets/imtkaggleteam/dental-radiography",
}


def _load(name: str) -> dict:
    path = _ANN / name
    if not path.exists():
        raise FileNotFoundError(f"Annotation file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_vqa() -> dict:
    """``{image_id: [ {question_type, question, choice, answer, reason}, ... ]}``"""
    return _load("vqa.json")


def load_classification() -> dict:
    """``{image_id: [ "C1", "C6", ... ]}`` (subset of the 18 labels)."""
    return _load("classification.json")


def load_captioning() -> dict:
    """``{image_id: {"description": "<clinical caption>"}}``"""
    return _load("captioning.json")


def image_dir() -> Path:
    return Path(os.environ.get("POCKET_DENTIST_IMAGES", _HERE / "images"))


def image_path(image_id: str) -> Path:
    """Resolve an image id to an existing ``.jpg``/``.png`` path, or raise."""
    base = image_dir()
    for ext in (".jpg", ".png"):
        p = base / f"{image_id}{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(
        f"Image '{image_id}' not found under {base}. "
        f"See download_images() / set $POCKET_DENTIST_IMAGES."
    )


def download_images() -> None:
    """Print where to obtain the images (not redistributed / auto-downloaded)."""
    print(
        "Images are not redistributed here. Obtain them from the original\n"
        "datasets under their own terms, name each file <id>.jpg (e.g.\n"
        "000000013.jpg), then export POCKET_DENTIST_IMAGES=/path/to/images.\n\n"
        "Source datasets:\n"
        + "\n".join(f"  - {k}: {v}" for k, v in SOURCE_DATASETS.items())
    )


if __name__ == "__main__":
    vqa, cls, cap = load_vqa(), load_classification(), load_captioning()
    print(f"vqa images:            {len(vqa)}")
    print(f"classification images: {len(cls)}")
    print(f"captioning images:     {len(cap)}")
    n_q = sum(len(v) for v in vqa.values())
    print(f"total VQA questions:   {n_q}")
