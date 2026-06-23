#!/usr/bin/env python3
"""
MetaDent classification scorer — multi-label over 18 dental conditions (C1-C18).

Faithful re-implementation of ``src/tasks/classification/evaluator.py``. The
headline metric is **Macro-F1** across the 18 categories (the label
distribution is long-tailed, so accuracy is misleading). Micro-F1 and
set-level Exact-Match are also reported.

Predicted labels are extracted from the model's JSON array of detected
conditions (``[{"id": "C1", "name": "...", "evidence": "..."}]``). A response
that did not yield any parseable ``id`` falls back to substring matching of
``C1..C18`` against the raw output; responses that produced no JSON at all
(format collapse) contribute an empty prediction set and are penalised by F1.

Inputs
------
  --predictions : results.json  -> {"<image_id>": [ {"id": "C1", ...}, ... ], ...}
  --ground-truth: classification.json -> {"<image_id>": ["C1", "C6"], ...}

Usage
-----
    python -m parsers.metadent_classification \
        --predictions results.json \
        --ground-truth ../qa_pairs/annotations/classification.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # allow sibling imports

from metrics_common import multilabel_macro_micro

LABELS = [f"C{i}" for i in range(1, 19)]
_LABEL_SET = set(LABELS)


def extract_predicted_ids(raw) -> set[str]:
    """Extract the set of predicted ``Ck`` ids from a model classification output.

    Mirrors the harness's tolerant extraction: handle a list of ``{"id": ...}``
    dicts (or ``{"1": ...}`` variants); on any structural surprise, fall back to
    substring matching the 18 labels against the stringified output.
    """
    ids: set[str] = set()
    try:
        seq = raw if isinstance(raw, list) else [raw]
        for item in seq:
            if not item or isinstance(item, str):
                continue
            if isinstance(item, list):
                for tmp in item:
                    if isinstance(tmp, dict):
                        ids.add(tmp.get("id") or tmp.get("1"))
            elif isinstance(item, dict):
                ids.add(item.get("id") or item.get("1"))
    except Exception:
        ids = set()

    ids = {i for i in ids if i in _LABEL_SET}
    if not ids:
        s = str(raw)
        ids = {lab for lab in LABELS if lab in s}
    return ids


def score(pred: dict, gt: dict) -> dict:
    """Score predictions against ground truth for the shared image ids."""
    common = [k for k in gt if k in pred]
    gt_sets = [set(gt[k]) & _LABEL_SET for k in common]
    pred_sets = [extract_predicted_ids(pred[k]) for k in common]
    result = multilabel_macro_micro(gt_sets, pred_sets, LABELS)
    result["n_scored"] = len(common)
    result["n_ground_truth"] = len(gt)
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="MetaDent classification scorer")
    ap.add_argument("--predictions", required=True, help="classification results.json")
    ap.add_argument("--ground-truth", required=True, help="annotations/classification.json")
    args = ap.parse_args()

    with open(args.predictions, encoding="utf-8") as f:
        pred = json.load(f)
    with open(args.ground_truth, encoding="utf-8") as f:
        gt = json.load(f)

    print(json.dumps(score(pred, gt), indent=2))


if __name__ == "__main__":
    main()
