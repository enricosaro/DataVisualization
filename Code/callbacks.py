from dash.dependencies import Input, Output, State
import charts


def register_callbacks(app):
    # ---------------------------------------------------------------------
    # 1) Clear selection: explicitly reset map selection & hover.
    #    Paired with the "Clear map selection" button (id="clear-selection").
    # ---------------------------------------------------------------------
    @app.callback(
        Output("listings-map", "selectedData"),
        Output("listings-map", "hoverData"),
        Input("clear-selection", "n_clicks"),
        prevent_initial_call=True,
    )
    def clear_map_selection(n_clicks):
        # Returning None clears these Graph properties on the client.
        return None, None

    # ---------------------------------------------------------------------
    # 2) Main update: apply filters and (optionally) map selection/hover
    #    to produce the histogram, bar chart, and map figure.
    #    Robust selection handling:
    #      - Prefer IDs from custom_data (if charts.py provides them).
    #      - Fallback to lat/lon matching otherwise.
    #      - Ignore stale/empty selections to avoid the “stuck” state.
    # ---------------------------------------------------------------------
    @app.callback(
        [
            Output("price-histogram", "figure"),
            Output("roomtype-composition", "figure"),
            Output("listings-map", "figure"),
        ],
        [
            Input("room-type", "value"),
            Input("price-range", "value"),
            Input("min-nights", "value"),
            Input("listings-map", "selectedData"),
            Input("listings-map", "hoverData"),
            Input("clear-selection", "n_clicks"),
        ],
    )
    def update_all(room_types, price_range, min_nights, selectedData, hoverData, clear_clicks):
        # ---- Load & normalize core columns. Keep this defensive. ----
        df = charts._load_listings().copy()

        if "price" not in df.columns:
            df["price"] = 0
        if "room_type" not in df.columns:
            df["room_type"] = "Unknown"
        if "minimum_nights" not in df.columns:
            df["minimum_nights"] = 1

        s = df["price"].astype(str).str.replace("€", "", regex=False)
        s = s.str.replace("$", "", regex=False).str.replace(",", "", regex=False).str.replace(" ", "", regex=False)
        df["price"] = charts.pd.to_numeric(s, errors="coerce").fillna(0)
        df["room_type"] = df["room_type"].fillna("Unknown").astype(str)
        df["minimum_nights"] = charts.pd.to_numeric(df["minimum_nights"], errors="coerce").fillna(1)

        # ---- Base filters from UI controls. ----
        rtypes = set(room_types or [])
        pr = price_range or [0, 999999]
        pmin = float(pr[0]) if len(pr) > 0 else 0.0
        pmax = float(pr[1]) if len(pr) > 1 else 999999.0
        mnights = float(min_nights or 1)

        cond = (df["price"] >= pmin) & (df["price"] <= pmax) & (df["minimum_nights"] >= mnights)
        if rtypes:
            cond &= df["room_type"].isin(rtypes)
        dff = df[cond].copy()

        # ---- Optional area focus based on hover (zoom to neighborhood). ----
        area_col = None
        for c in ["neighbourhood_cleansed", "neighborhood"]:
            if c in dff.columns:
                area_col = c
                break

        if hoverData and isinstance(hoverData, dict):
            try:
                pt = (hoverData.get("points") or [{}])[0]
                lat = float(pt.get("lat", "nan"))
                lon = float(pt.get("lon", "nan"))
                if "latitude" in dff.columns and "longitude" in dff.columns:
                    dif = (dff["latitude"] - lat).abs() + (dff["longitude"] - lon).abs()
                    idx = dif.idxmin()
                    if area_col and idx in dff.index:
                        nh = dff.loc[idx, area_col]
                        dff = dff[dff[area_col] == nh]
            except Exception:
                # Ignore malformed hover payloads.
                pass

        # ---- Robust selection handling. Prefer stable IDs from custom_data. ----
        selected_ids = None
        if selectedData and isinstance(selectedData, dict):
            pts = selectedData.get("points") or []
            ids = []
            for p in pts:
                cd = p.get("customdata")
                if isinstance(cd, (list, tuple)) and len(cd) > 0:
                    ids.append(cd[0])
            if ids:
                selected_ids = ids

        dff_sel = dff

        if selected_ids is not None and "id" in dff.columns:
            # Selection via IDs (best path).
            subset = dff[dff["id"].isin(selected_ids)]
            if not subset.empty:  # ignore stale selection that yields nothing
                dff_sel = subset
        else:
            # Fallback: match by raw lat/lon (less reliable).
            selected_latlon = []
            if selectedData and isinstance(selectedData, dict):
                for p in selectedData.get("points", []):
                    lat = p.get("lat")
                    lon = p.get("lon")
                    if lat is not None and lon is not None:
                        selected_latlon.append((lat, lon))

            if selected_latlon and {"latitude", "longitude"}.issubset(dff.columns):
                ll = charts.pd.DataFrame(selected_latlon, columns=["_lat", "_lon"])
                merged = dff.merge(ll, left_on=["latitude", "longitude"], right_on=["_lat", "_lon"], how="inner")
                if not merged.empty:  # ignore stale polygon that matches nothing
                    dff_sel = merged

        # ==================== CHART 1: Price Histogram ====================
        if dff_sel.empty:
            fig1 = charts.px.histogram(x=[], title="Nightly Price Distribution (no data)")
        else:
            fig1 = charts.px.histogram(
                dff_sel,
                x="price",
                nbins=60,
                title="Nightly Price Distribution (filtered)",
                labels={"price": "Nightly price (€)"},
            )
        fig1.update_layout(template="plotly_white", height=420, margin=dict(l=10, r=10, t=48, b=10))
        fig1.update_yaxes(rangemode="tozero")

        # ==================== CHART 2: Room Type Share ====================
        if dff_sel.empty:
            fig2 = charts.px.bar(x=[], y=[], title="Room-Type Composition (no data)")
        else:
            counts = dff_sel["room_type"].value_counts(dropna=False)
            total = float(counts.sum()) if counts.sum() else 1.0
            x_vals = list(counts.index)
            y_vals = [(c / total) * 100.0 for c in counts.tolist()]
            fig2 = charts.px.bar(
                x=x_vals,
                y=y_vals,
                title="Room-Type Composition (filtered)",
                labels={"x": "Room type", "y": "Share of listings (%)"},
                text=y_vals,
            )
        fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
        fig2.update_layout(template="plotly_white", height=420, margin=dict(l=10, r=10, t=48, b=10))

        # ==================== CHART 3: Map ====================
        # Build a dynamic uirevision key so that clicking "Clear" forces a fresh UI state.
        clear_clicks = clear_clicks or 0
        uirevision_key = f"{tuple(sorted(room_types or []))}-{tuple(price_range or [])}-{mnights}-{clear_clicks}"

        fig3 = charts.make_map_figure(dff_sel, uirevision=uirevision_key)

        return fig1, fig2, fig3
