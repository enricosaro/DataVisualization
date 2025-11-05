import pandas as pd
import plotly.express as px

# Path to the Inside Airbnb CSV. Adjust if the data lives elsewhere.
DATA_PATH = "../listings.csv"

# Simple in-memory cache to avoid re-reading the CSV on every callback.
_df_cache = None


def _load_listings() -> pd.DataFrame:
    """
    Load listings from CSV and perform minimal normalization needed by the app.
    Returns a cached DataFrame to keep callbacks responsive.
    """
    global _df_cache
    if _df_cache is not None:
        return _df_cache

    df = pd.read_csv(DATA_PATH)

    # Normalize 'price' to numeric (strip symbols/spaces, keep digits and dot).
    if "price" in df.columns:
        df["price"] = (
            df["price"].astype(str)
            .str.replace(r"[^\d.]", "", regex=True)  # keep digits and dot only
            .replace("", "0")
            .astype(float)
        )
    else:
        df["price"] = 0.0

    # Ensure room_type exists.
    if "room_type" not in df.columns:
        df["room_type"] = "Unknown"
    df["room_type"] = df["room_type"].fillna("Unknown").astype(str)

    # Minimum nights (fallback to 1 if missing).
    if "minimum_nights" not in df.columns:
        df["minimum_nights"] = 1

    _df_cache = df
    return df


def make_map_figure(dff: pd.DataFrame, uirevision=None):
    """
    Build a scatter Mapbox figure from a filtered DataFrame (dff).
    - If coordinates are missing/empty, draw an empty map centered on Ghent.
    - If an ID column exists ('id' or 'listing_id'), include it in custom_data
      so callbacks can match selections by a stable identifier (preferred).
    - Keeps drag/lasso selection enabled.
    """

    # Fallback center: Ghent (Belgium)
    default_center = (51.0543, 3.7174)

    # Compute a reasonable center based on data (median), else default to Ghent.
    if {"latitude", "longitude"}.issubset(dff.columns) and dff["latitude"].notna().any():
        lat = float(dff["latitude"].median())
        lon = float(dff["longitude"].median())
    else:
        lat, lon = default_center

    # If we don't have coordinates or the frame is empty, return a blank map.
    if dff.empty or {"latitude", "longitude"} - set(dff.columns):
        fig = px.scatter_mapbox(
            lat=[lat],
            lon=[lon],
            mapbox_style="open-street-map",
            center={"lat": lat, "lon": lon},
            zoom=11,
            title="Airbnb Listings in Ghent",
        )
        # Hide the single placeholder marker.
        if fig.data:
            fig.data[0].marker.update(size=0, opacity=0)
        fig.update_layout(
            mapbox_style="open-street-map",
            margin=dict(l=10, r=10, t=48, b=10),
            height=520,
            dragmode="lasso",
            clickmode="event+select",
            uirevision=uirevision,
        )
        return fig

    # Downsample to keep interaction smooth on large datasets.
    sample = dff if len(dff) <= 2000 else dff.sample(2000, random_state=0)

    # Hover fields shown in the tooltip if present.
    hover_cols = []
    if "host_name" in sample.columns:
        hover_cols.append("host_name")
    if "price" in sample.columns:
        hover_cols.append("price")
    if "room_type" in sample.columns:
        hover_cols.append("room_type")

    # Prefer a stable ID in custom_data so callbacks can filter by ID instead of lat/lon.
    id_col = "id" if "id" in sample.columns else ("listing_id" if "listing_id" in sample.columns else None)
    custom_data = [id_col] if id_col else None

    fig = px.scatter_mapbox(
        sample,
        lat="latitude",
        lon="longitude",
        hover_name="host_name" if "host_name" in sample.columns else None,
        hover_data=hover_cols,
        custom_data=custom_data,  # enables robust selection handling in callbacks
        mapbox_style="open-street-map",
        center={"lat": lat, "lon": lon},
        zoom=11,
        opacity=0.8,
        title="Airbnb Listings in Ghent",
    )

    fig.update_traces(marker={"size": 9})
    fig.update_layout(
        mapbox_style="open-street-map",
        margin=dict(l=10, r=10, t=48, b=10),
        height=520,
        dragmode="lasso",
        clickmode="event+select",
        uirevision="keep",
    )
    return fig