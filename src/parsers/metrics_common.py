"""
Shared multi-label scoring used by MetaDent classification and DR.

Reproduces the per-class -> macro/micro aggregation in the research harness
(``src/tasks/classification/evaluator.py``), computed over a fixed label set
with scikit-learn so results are identical regardless of which labels each
sample happens to contain.
"""

from typing import Iterable, Sequence


def to_binary_matrix(label_sets: Iterable[Iterable[str]], labels: Sequence[str]) -> list[list[int]]:
    """Turn an iterable of label sets into a binary indicator matrix over ``labels``."""
    rows = []
    for s in label_sets:
        present = set(s)
        rows.append([1 if lab in present else 0 for lab in labels])
    return rows


def multilabel_macro_micro(
    gt_sets: Sequence[Iterable[str]],
    pred_sets: Sequence[Iterable[str]],
    labels: Sequence[str],
) -> dict:
    """Macro/micro precision, recall, F1 and exact-match over a fixed label set.

    ``gt_sets`` and ``pred_sets`` must be aligned (same length / same order).
    Returns ``{"macro": {...}, "micro": {...}, "exact_match": float, "n": int}``.
    """
    from sklearn.metrics import f1_score, precision_score, recall_score

    assert len(gt_sets) == len(pred_sets), "gt and pred must be aligned"
    if not gt_sets:
        zero = {"P": 0.0, "R": 0.0, "F1": 0.0}
        return {"macro": dict(zero), "micro": dict(zero), "exact_match": 0.0, "n": 0}

    y_true = to_binary_matrix(gt_sets, labels)
    y_pred = to_binary_matrix(pred_sets, labels)

    out: dict = {}
    for avg in ("macro", "micro"):
        out[avg] = {
            "P": float(precision_score(y_true, y_pred, average=avg, zero_division=0)),
            "R": float(recall_score(y_true, y_pred, average=avg, zero_division=0)),
            "F1": float(f1_score(y_true, y_pred, average=avg, zero_division=0)),
        }
    out["exact_match"] = sum(
        1 for g, p in zip(gt_sets, pred_sets) if set(g) == set(p)
    ) / len(gt_sets)
    out["n"] = len(gt_sets)
    return out
