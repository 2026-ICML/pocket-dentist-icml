#!/usr/bin/env python3
"""
DR parser + scorer — dental radiography lesion identification.

The paper scores DR as **multi-label classification** over four lesion
categories (Cavity, Fillings, Impacted Tooth, Implant) with **Macro-F1** as the
primary metric (Accuracy secondary). Models emit JSON of the form
``{"objects": [{"label": "Cavity"}, ...]}``; ``parse_labels`` extracts the
label set, tolerating a few shapes seen in practice.

(The full research harness, ``src-DR/``, additionally computes detection-style
IoU/mAP from bounding boxes; the published headline number is the multi-label
Macro-F1 reproduced here.)

Usage
-----
    python -m parsers.dr --predictions predictions.jsonl

``predictions.jsonl``: one object per line with
    {"sample_id": "...", "ground_truth": ["Cavity", ...], "response": "<raw>"}
or a pre-parsed ``"prediction": ["Cavity", ...]``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # allow sibling imports

from json_parse import parse_json
from metrics_common import multilabel_macro_micro

DR_LABELS = ["Cavity", "Fillings", "Impacted Tooth", "Implant"]
_CANON = {lab.lower(): lab for lab in DR_LABELS}


def parse_labels(model_output) -> list[str]:
    """Extract the set of DR lesion labels from a model response.

    Accepts a raw string, a ``{"objects": [...]}`` dict, or a list of objects.
    Unknown labels are dropped; matching is case-insensitive.
    """
    obj = model_output
    if isinstance(model_output, str):
        try:
            obj = parse_json(model_output, dict)
        except Exception:
            # last-resort: substring match against known labels
            s = model_output.lower()
            return [lab for low, lab in _CANON.items() if low in s]

    items = obj.get("objects", []) if isinstance(obj, dict) else obj
    labels: set[str] = set()
    if isinstance(items, list):
        for it in items:
            name = it.get("label") if isinstance(it, dict) else it
            if isinstance(name, str) and name.strip().lower() in _CANON:
                labels.add(_CANON[name.strip().lower()])
    return sorted(labels)


def _resolve_prediction(rec: dict) -> list[str]:
    if rec.get("prediction") is not None:
        return [_CANON[x.lower()] for x in rec["prediction"] if x.lower() in _CANON]
    return parse_labels(rec.get("response") or rec.get("raw_output") or "")


def main() -> None:
    ap = argparse.ArgumentParser(description="DR scorer (multi-label, 4 lesions)")
    ap.add_argument("--predictions", required=True, help="predictions.jsonl")
    args = ap.parse_args()

    gt_sets, pred_sets = [], []
    with open(args.predictions, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            gt_sets.append([x for x in rec["ground_truth"] if x in DR_LABELS])
            pred_sets.append(_resolve_prediction(rec))

    metrics = multilabel_macro_micro(gt_sets, pred_sets, DR_LABELS)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
