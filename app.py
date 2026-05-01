import streamlit as st
from datetime import datetime
import db

st.set_page_config(page_title="Car Hunter", layout="wide")
st.title("🔍 Car Hunter — Karnataka Used Cars")

# ── load data ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load() -> list[dict]:
    return db.fetch_active()

all_rows = load()

# ── derive filter options from actual data ─────────────────────────────────
def _sources(row: dict) -> list[str]:
    return list((row.get("sources") or {}).keys())

all_sources = sorted({s for r in all_rows for s in _sources(r)})
all_makes   = sorted({r["make"] for r in all_rows if r.get("make")})
all_models  = sorted({r["model"] for r in all_rows if r.get("model")})
all_years   = [r["year"] for r in all_rows if r.get("year")]
year_lo     = min(all_years) if all_years else 2017
year_hi     = max(all_years) if all_years else 2025

# ── sidebar filters ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    source_filter = st.multiselect("Source", all_sources)
    make_filter   = st.multiselect("Make", all_makes)
    model_filter  = st.multiselect("Model", all_models)
    year_min, year_max = st.slider("Year", year_lo, year_hi, (year_lo, year_hi))
    price_max = st.number_input("Max Price (₹)", value=2_500_000, step=500_000, format="%d")
    kms_max   = st.number_input("Max KMs", value=150_000, step=10_000, format="%d")
    trans_filter = st.multiselect("Transmission", ["Automatic", "Manual"])
    sort_by = st.selectbox("Sort by", ["Price ↑", "Price ↓", "Year ↓", "KMs ↑", "Newest first"], index=4)
    st.divider()
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

# ── apply filters ──────────────────────────────────────────────────────────
rows = all_rows

if source_filter:
    rows = [r for r in rows if any(s in source_filter for s in _sources(r))]
if make_filter:
    rows = [r for r in rows if r["make"] in make_filter]
if model_filter:
    rows = [r for r in rows if r["model"].upper() in [m.upper() for m in model_filter]]
rows = [r for r in rows if year_min <= (r["year"] or 0) <= year_max]
rows = [r for r in rows if (r["price"] or 0) <= price_max]
rows = [r for r in rows if (r["kms"] or 0) <= kms_max]
if trans_filter:
    rows = [r for r in rows if r.get("transmission") in trans_filter]

# ── sort ───────────────────────────────────────────────────────────────────
sort_key = {
    "Price ↑":      lambda r: r["price"] or 0,
    "Price ↓":      lambda r: -(r["price"] or 0),
    "Year ↓":       lambda r: -(r["year"] or 0),
    "KMs ↑":        lambda r: r["kms"] or 0,
    "Newest first": lambda r: -(datetime.fromisoformat(r["first_seen"]).toordinal() if r.get("first_seen") else 0),
}[sort_by]
rows.sort(key=sort_key)

# ── header row ─────────────────────────────────────────────────────────────
st.caption(f"{len(rows)} listing{'s' if len(rows) != 1 else ''} found")
st.divider()

# ── listing rows ───────────────────────────────────────────────────────────
SOURCE_COLORS = {
    "cars24":   "#e84118", "spinny": "#00a8ff", "olx":      "#3d9970",
    "teambhp":  "#9b59b6", "9thgear": "#f39c12", "carwale": "#2980b9",
    "cardekho": "#27ae60",
}

for row in rows:
    col_img, col_info, col_price, col_del = st.columns([1, 3.5, 1.5, 1.2])

    # Thumbnail
    with col_img:
        img = row.get("image_url") or ""
        if img:
            st.image(img, width=130)
        else:
            st.markdown("<div style='width:130px;height:90px;background:#2a2a2a;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#555'>No image</div>", unsafe_allow_html=True)

    # Info
    with col_info:
        name = f"{row['year']} {row['make']} {row['model']}"
        st.markdown(f"**{name}**")
        st.caption(row.get("variant") or "—")

        meta_parts = []
        if row.get("kms"):
            meta_parts.append(f"{row['kms']:,} km")
        if row.get("transmission"):
            meta_parts.append(row["transmission"])
        if row.get("color"):
            meta_parts.append(row["color"])
        if row.get("location"):
            meta_parts.append(row["location"])
        if meta_parts:
            st.caption(" · ".join(meta_parts))

        # Source badges with links
        sources: dict = row.get("sources") or {}
        badge_html = ""
        for src, info in sources.items():
            color = SOURCE_COLORS.get(src, "#555")
            link  = info.get("url", "#")
            badge_html += (
                f'<a href="{link}" target="_blank" style="'
                f'background:{color};color:white;padding:2px 8px;border-radius:4px;'
                f'font-size:11px;text-decoration:none;margin-right:4px">{src}</a>'
            )
        if badge_html:
            st.markdown(badge_html, unsafe_allow_html=True)

    # Price
    with col_price:
        price = row.get("price") or 0
        lakhs = price / 100_000
        st.markdown(f"### ₹{lakhs:.2f}L")
        first_seen = row.get("first_seen", "")
        if first_seen:
            st.caption(f"Since {first_seen}")

    # Actions
    with col_del:
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        if st.button("Not interested", key=f"hide_{row['id']}", use_container_width=True, help="Hide this listing permanently"):
            db.soft_delete(row["id"])
            st.cache_data.clear()
            st.rerun()
        if st.button("🗑️ Delete", key=f"del_{row['id']}", use_container_width=True, help="Remove from DB — will be re-fetched next scrape run"):
            db.hard_delete(row["id"])
            st.cache_data.clear()
            st.rerun()

    st.divider()

if not rows:
    st.info("No listings match your filters. Try widening the search or wait for the next scrape run.")
