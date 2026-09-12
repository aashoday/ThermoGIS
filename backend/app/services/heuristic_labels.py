"""
Weak-supervision seed labels: encodes domain heuristics (distance to
nearest industrial asset + spatio-temporal persistence from clustering)
into a label LightGBM can learn from.

These thresholds are intentionally simple and documented so they're
defensible in a demo — the point isn't that these rules are perfect,
it's that they're a transparent starting point the model refines.
"""
import pandas as pd

CLOSE_DISTANCE_M = 1000
NEAR_DISTANCE_M = 2500
FAR_DISTANCE_M = 5000

HIGH_PERSISTENCE = 3   # detections in same cluster
MODERATE_PERSISTENCE = 2

LABELS = ["industrial", "non_industrial", "uncertain"]


def assign_heuristic_label(row: pd.Series) -> str:
    dist = row["distance_to_asset_m"]
    persistence = row["detection_count"]

    # Close + persistent = strong industrial signal (e.g. flare stack, kiln)
    if dist <= CLOSE_DISTANCE_M and persistence >= MODERATE_PERSISTENCE:
        return "industrial"

    # Close but only seen once — could be industrial startup/one-off, still likely industrial
    if dist <= CLOSE_DISTANCE_M and persistence == 1:
        return "industrial"

    # Near-ish + genuinely persistent across many passes — still counts as industrial
    if dist <= NEAR_DISTANCE_M and persistence >= HIGH_PERSISTENCE:
        return "industrial"

    # Far from any industrial asset + single detection = classic transient burn signature
    if dist > FAR_DISTANCE_M and persistence == 1:
        return "non_industrial"

    # Everything else (moderate distance, ambiguous persistence) — genuinely unclear
    return "uncertain"


def apply_heuristic_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["heuristic_label"] = df.apply(assign_heuristic_label, axis=1)
    return df