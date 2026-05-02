import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import db

st.set_page_config(page_title="Car Hunter", layout="centered", initial_sidebar_state="collapsed")

st.title("Car Hunter")

# ── handle action links (?action=hide|del&id=...) ──────────────────────────
qp = st.query_params
_action = qp.get("action")
_lid    = qp.get("id")
if _action and _lid:
    if _action == "hide":
        db.soft_delete(_lid)
    elif _action == "del":
        db.hard_delete(_lid)
    st.query_params.clear()
    st.cache_data.clear()
    st.rerun()

# ── JS injected into parent via zero-height iframe ─────────────────────────
# st.markdown strips <script> and onclick — components.html iframe can reach
# window.parent since Streamlit serves both on the same origin.
components.html("""
<script>
(function() {
  var p  = window.parent.document;
  var pw = window.parent;

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

  // ── scroll restore across action-link reruns ──────────────────────────
  // Save scrollY before an action link navigates; restore on next load.
  p.addEventListener('click', function(e) {
    var a = e.target.closest && e.target.closest('a.action-link');
    if (a) {
      try { pw.sessionStorage.setItem('car-hunter-scroll', String(pw.scrollY)); } catch (_) {}
    }
  }, true);
  try {
    var saved = pw.sessionStorage.getItem('car-hunter-scroll');
    if (saved !== null) {
      pw.sessionStorage.removeItem('car-hunter-scroll');
      pw.scrollTo(0, parseInt(saved, 10) || 0);
    }
  } catch (_) {}
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
  display:flex;align-items:center;gap:5px;
}
.car-row1 img.brand-logo {
  height:18px;width:auto;vertical-align:middle;
  object-fit:contain;
}
.car-row2 {
  font-size:12px;color:#888;margin-top:2px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.car-row3 { font-size:13px;font-weight:700;margin-top:3px; }

/* right column inside .car-card — favicons → divider → ⋯ menu */
.right-col {
  display:flex;flex-direction:column;align-items:center;gap:6px;
  padding-left:10px;border-left:1px solid #333;align-self:stretch;
  justify-content:center;flex-shrink:0;
}
.src-icons { display:flex;flex-direction:column;align-items:center;gap:5px; }
.src-icon img { width:22px;height:22px;object-fit:contain;display:block; }
.src-divider { width:24px;border-top:1px solid #333; }

/* ⋯ menu via <details>/<summary> — no JS needed */
details.actions-menu { position:relative; }
details.actions-menu > summary {
  list-style:none;cursor:pointer;color:#777;font-size:18px;line-height:1;
  padding:2px 6px;user-select:none;
}
details.actions-menu > summary::-webkit-details-marker { display:none; }
details.actions-menu > summary::marker { content:""; }
details.actions-menu > summary:hover { color:#ccc; }
details.actions-menu[open] > summary { color:#ccc; }
.actions-pop {
  position:absolute;right:0;top:100%;z-index:10;
  background:#1a1a1a;border:1px solid #333;border-radius:6px;
  min-width:140px;padding:4px 0;box-shadow:0 4px 12px rgba(0,0,0,0.5);
  margin-top:4px;
}
.actions-pop a.action-link {
  display:block;padding:6px 12px;color:#ddd;text-decoration:none;
  font-size:13px;white-space:nowrap;
}
.actions-pop a.action-link:hover { background:#2a2a2a;color:#fff; }
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

BRAND_LOGO_FILES = {
    "audi": "audi",
    "bmw": "bmw",
    "mercedes-benz": "mercedes-benz",
    "mercedes": "mercedes-benz",
    "volvo": "volvo",
    "volkswagen": "volkswagen",
    "vw": "volkswagen",
    "skoda": "skoda",
    "škoda": "skoda",
    "jeep": "jeep",
    "ford": "ford",
}

def brand_logo_html(make: str) -> str:
    slug = BRAND_LOGO_FILES.get(make.strip().lower())
    if not slug:
        return make
    return (
        f'<img class="brand-logo" src="app/static/logos/{slug}.png" '
        f'alt="{make}" title="{make}" />'
    )

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

    make_html = brand_logo_html(make) if make else ""
    row1 = f"{year} {make_html} {model}" + (f" · {trans}" if trans else "")
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
  <div class="right-col">
    <div class="src-icons">{src_icons_html}</div>
    <div class="src-divider"></div>
    <details class="actions-menu">
      <summary>⋯</summary>
      <div class="actions-pop">
        <a class="action-link" href="?action=hide&id={lid}">Not interested</a>
        <a class="action-link" href="?action=del&id={lid}">Delete</a>
      </div>
    </details>
  </div>
</div>
""", unsafe_allow_html=True)

if not rows:
    st.info("No listings match your filters.")
