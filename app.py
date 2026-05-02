import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import db

st.set_page_config(page_title="Car Hunter", layout="centered", initial_sidebar_state="collapsed")

# ── handle actions triggered by the in-card dropdown ──────────────────────
_p = st.query_params
if "action" in _p:
    _lid = _p.get("id")
    if _lid:
        if _p["action"] == "hide":
            db.soft_delete(_lid)
        elif _p["action"] == "delete":
            db.hard_delete(_lid)
    st.query_params.clear()
    st.cache_data.clear()
    st.rerun()

st.title("Car Hunter")

# ── JS injected into parent via zero-height iframe ─────────────────────────
# st.markdown strips <script> and onclick — components.html iframe can reach
# window.parent since Streamlit serves both on the same origin.
components.html("""
<script>
(function() {
  var p = window.parent.document;

  // ── fullscreen image modal ──────────────────────────────────────────────
  if (!p.getElementById('img-modal')) {
    var modal = p.createElement('div');
    modal.id = 'img-modal';
    modal.style.cssText = 'display:none;position:fixed;top:0;left:0;width:100%;height:100%;' +
      'background:rgba(0,0,0,0.93);z-index:9999;align-items:center;justify-content:center;cursor:pointer;';
    var mimg = p.createElement('img');
    mimg.id = 'modal-img';
    mimg.style.cssText = 'max-width:95vw;max-height:90vh;object-fit:contain;border-radius:8px;';
    modal.appendChild(mimg);
    modal.addEventListener('click', function() { modal.style.display = 'none'; });
    p.body.appendChild(modal);
  }

  // ── fullscreen image click handler ────────────────────────────────────
  p.addEventListener('click', function(e) {
    if (e.target && e.target.classList.contains('car-thumb')) {
      p.getElementById('modal-img').src = e.target.src;
      p.getElementById('img-modal').style.display = 'flex';
    }
  }, true);
})();
</script>
""", height=0)

# ── styles ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.car-card {
  display:flex;align-items:center;gap:10px;padding:10px 0;
  border-bottom:1px solid #2a2a2a;
}
.car-thumb {
  width:88px;height:64px;object-fit:cover;border-radius:6px;
  cursor:pointer;flex-shrink:0;
}
.car-thumb-placeholder {
  width:88px;height:64px;border-radius:6px;flex-shrink:0;
  background:#222;display:flex;align-items:center;justify-content:center;
  color:#555;font-size:10px;
}
.car-info { flex:1;min-width:0; }
.car-row1 {
  font-size:13px;font-weight:600;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.car-row2 {
  font-size:12px;color:#888;margin-top:2px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.car-row3 { font-size:13px;font-weight:700;margin-top:3px; }

/* Right column: source icon(s) + divider + ⋯ menu */
.car-right {
  border-left:1px solid #333;padding-left:10px;
  display:flex;flex-direction:column;align-items:center;
  gap:0;flex-shrink:0;
}
.src-icons {
  display:flex;flex-direction:column;align-items:center;
  gap:5px;padding-bottom:6px;
}
.src-icon img { width:22px;height:22px;object-fit:contain; }
.src-divider { width:100%;border-top:1px solid #333;margin-bottom:4px; }

/* ⋯ dropdown */
.action-menu { position:relative; }
.action-menu summary {
  list-style:none;cursor:pointer;
  font-size:18px;color:#777;padding:2px 4px;
  user-select:none;
}
.action-menu summary::-webkit-details-marker { display:none; }
.action-menu[open] summary { color:#ccc; }
.action-dropdown {
  position:absolute;right:0;top:calc(100% + 4px);
  background:#1e1e1e;border:1px solid #3a3a3a;border-radius:7px;
  min-width:140px;z-index:300;overflow:hidden;white-space:nowrap;
  box-shadow:0 4px 16px rgba(0,0,0,0.5);
}
.action-item {
  display:block;padding:9px 14px;color:#ccc;font-size:12px;cursor:pointer;
  text-decoration:none;
}
.action-item:hover { background:#2a2a2a; color:#fff; }
.action-divider { border-top:1px solid #333; }
</style>
""", unsafe_allow_html=True)

# ── load data ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load() -> list[dict]:
    return db.fetch_active()

all_rows = load()

# ── derive filter options ──────────────────────────────────────────────────
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
    if st.button("Refresh"):
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

# ── helpers ────────────────────────────────────────────────────────────────
SOURCE_FAVICONS = {
    "cars24":   "https://www.cars24.com/favicon.ico",
    "spinny":   "https://www.spinny.com/favicon.ico",
    "olx":      "https://www.olx.in/favicon.ico",
    "carwale":  "https://www.carwale.com/favicon.ico",
    "cardekho": "https://www.cardekho.com/favicon.ico",
    "teambhp":  "https://www.team-bhp.com/favicon.ico",
    "9thgear":  "https://9thgear.com/favicon.ico",
}

def fmt_price(price: int) -> str:
    lakhs = price / 100_000
    return f"₹{lakhs:.1f}L" if lakhs % 1 else f"₹{int(lakhs)}L"

def fmt_kms(kms: int) -> str:
    return f"{kms // 1000}k km" if kms >= 1000 else f"{kms} km"

def trans_abbr(t: str) -> str:
    if not t:
        return ""
    return "AT" if t.lower().startswith("a") else "MT"

# ── listing count ──────────────────────────────────────────────────────────
st.caption(f"{len(rows)} listing{'s' if len(rows) != 1 else ''} found")

# ── listings ───────────────────────────────────────────────────────────────
for row in rows:
    lid     = row["id"]
    img     = row.get("image_url") or ""
    year    = row.get("year") or ""
    make    = row.get("make") or ""
    model   = row.get("model") or ""
    trans   = trans_abbr(row.get("transmission") or "")
    variant = row.get("variant") or ""
    kms     = fmt_kms(row["kms"]) if row.get("kms") else ""
    price   = fmt_price(row["price"]) if row.get("price") else "—"
    sources: dict = row.get("sources") or {}

    row1 = f"{year} {make} {model}" + (f" · {trans}" if trans else "")
    row2_parts = [p for p in [variant, kms] if p]
    row2 = " · ".join(row2_parts)

    img_html = (
        f'<img class="car-thumb" src="{img}" />'
        if img else
        '<div class="car-thumb-placeholder">No image</div>'
    )

    src_icons_html = ""
    for src, info in sources.items():
        url     = info.get("url", "#")
        favicon = SOURCE_FAVICONS.get(src, "")
        if favicon:
            src_icons_html += (
                f'<a class="src-icon" href="{url}" target="_blank">'
                f'<img src="{favicon}" title="{src}" /></a>'
            )
        else:
            src_icons_html += (
                f'<a href="{url}" target="_blank" '
                f'style="font-size:10px;color:#aaa">{src}</a>'
            )

    st.markdown(f"""
<div class="car-card">
  {img_html}
  <div class="car-info">
    <div class="car-row1">{row1}</div>
    <div class="car-row2">{row2}</div>
    <div class="car-row3">{price}</div>
  </div>
  <div class="car-right">
    <div class="src-icons">{src_icons_html}</div>
    <div class="src-divider"></div>
    <details class="action-menu">
      <summary>&#8943;</summary>
      <div class="action-dropdown">
        <a class="action-item" href="?action=hide&id={lid}">Not interested</a>
        <div class="action-divider"></div>
        <a class="action-item" href="?action=delete&id={lid}">Delete</a>
      </div>
    </details>
  </div>
</div>
""", unsafe_allow_html=True)

if not rows:
    st.info("No listings match your filters.")
