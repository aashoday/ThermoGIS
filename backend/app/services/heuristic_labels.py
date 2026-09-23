"""
Weak-supervision seed labels: encodes domain heuristics (distance to
nearest industrial asset, that asset's specific type, spatio-temporal
persistence from clustering, and landcover) into labels LightGBM can
learn from.

Matches the problem statement's named thermal-anomaly categories —
industrial fires, gas flares, agricultural burning, mining activity,
and wildfires — rather than one generic "industrial" bucket.

These thresholds are intentionally simple and documented so they're
defensible in a demo — the point isn't that these rules are perfect,
it's that they're a transparent starting point the model refines.
"""
import pandas as pd

CLOSE_DISTANCE_M = 1000
NEAR_DISTANCE_M = 2500
FAR_DISTANCE_M = 5000

HIGH_PERSISTENCE = 3       # detections in same cluster
MODERATE_PERSISTENCE = 2

# nearest_asset_type values (from ingest_osm.classify_asset_type) that
# indicate a specific industrial sub-category, not just generic "industrial"
GAS_FLARE_ASSET_TYPES = {"refinery", "oil_well", "petrochemical"}
MINING_ASSET_TYPES = {"mine_quarry"}

# landcover_class values (from ingest_landcover, ESA WorldCover labels)
NATURAL_LANDCOVER = {"Tree Cover", "Shrubland", "Grassland"}
AGRICULTURAL_LANDCOVER = {"Cropland"}

LABELS = [
    "industrial_fire",
    "gas_flare",
    "mining_activity",
    "agricultural_burn",
    "wildfire",
    "uncertain",
]


def assign_heuristic_label(row: pd.Series) -> str:
    dist = row["distance_to_asset_m"]
    persistence = row["detection_count"]
    asset_type = row["nearest_asset_type"]
    landcover = row["landcover_class"]

    is_flare_asset = asset_type in GAS_FLARE_ASSET_TYPES
    is_mining_asset = asset_type in MINING_ASSET_TYPES

    # Close to an industrial asset — the asset's own type tells us which
    # specific kind of industrial thermal source this almost certainly is,
    # instead of lumping everything into one "industrial" bucket.
    if dist <= CLOSE_DISTANCE_M:
        if is_flare_asset:
            return "gas_flare"
        if is_mining_asset:
            return "mining_activity"
        return "industrial_fire"

    # Near-ish but genuinely persistent across many passes — still counts,
    # same asset-type-driven category.
    if dist <= NEAR_DISTANCE_M and persistence >= HIGH_PERSISTENCE:
        if is_flare_asset:
            return "gas_flare"
        if is_mining_asset:
            return "mining_activity"
        return "industrial_fire"

    # Far from any industrial asset — landcover distinguishes agricultural
    # burning from natural/forest wildfire, which distance alone can't do.
    if dist > FAR_DISTANCE_M:
        if landcover in AGRICULTURAL_LANDCOVER:
            return "agricultural_burn"
        if landcover in NATURAL_LANDCOVER:
            return "wildfire"
        # Built-up, Water Bodies, Bare/Sparse Vegetation, or unknown, far
        # from any tracked asset — genuinely ambiguous, don't force a guess
        return "uncertain"

    # Everything else: moderate distance, ambiguous persistence/asset type
    return "uncertain"


def apply_heuristic_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["heuristic_label"] = df.apply(assign_heuristic_label, axis=1)
    return df