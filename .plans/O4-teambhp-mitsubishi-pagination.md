# O4 — TeamBHP: missing Mitsubishi + fragile pagination

## Problems

### 1. Mitsubishi Pajero Sport not scraped at all

`scrapers/teambhp.py` has no Mitsubishi model ID in `MODEL_IDS` and no "mitsubishi" key in
`MAKE_NORM`. The Pajero Sport was added to `filters.py` (commit f9159d7) but the TeamBHP
scraper was never updated. Every TeamBHP Pajero Sport listing is silently skipped.

### 2. Session-based pagination is fragile

Pages 2–9 use `?restore=1&page=N` instead of repeating the full search URL. This relies on
the TeamBHP server remembering the page-1 search in a session keyed by cookie. Failure modes:

- Session TTL shorter than the time between requests → page 2+ returns **no rows** (empty
  search replay) or the front page, breaking silently (the `if not rows: break` exits cleanly
  with truncated results)
- Cookie not set at all (httpx redirect strips cookies, server-side session not created) →
  same silent failure
- Server returns 200 with unrelated content → `_parse_row` returns 0 listings, loop exits
  after first empty page

The current code has up to 9 pages × ~15 listings = ~135 potential results; if the session
lapses after page 1, we get only ~15 listings per run.

---

## Investigation steps

### Step 1 — Find Mitsubishi Pajero Sport model ID

TeamBHP exposes all make/model IDs in a JS variable `tree_MakeModel` on the classifieds
search page (`https://classifieds.team-bhp.com/search_results/`).

**Action**: Fetch that page and grep for `pajero` (case-insensitive) in the raw HTML/JS.

```python
import httpx, re
resp = httpx.get("https://classifieds.team-bhp.com/search_results/", headers=HEADERS)
matches = re.findall(r'"(\d+)"\s*:\s*\{[^}]*pajero[^}]*\}', resp.text, re.IGNORECASE)
# or simpler: find all occurrences of "pajero" with surrounding 100 chars
for m in re.finditer(r'.{50}[Pp]ajero.{50}', resp.text):
    print(m.group())
```

Expected output: a numeric model ID like `3301` mapped to "Pajero Sport".

Also check whether "Mitsubishi" has a make ID needed for the URL (vs. model-only ID).

### Step 2 — Fix MODEL_IDS and MAKE_NORM

Once the ID is found:

```python
MODEL_IDS = [
    ...existing IDs...,
    # Mitsubishi Pajero Sport
    XXXX,  # replace with actual ID
]

MAKE_NORM = {
    ...existing entries...,
    "mitsubishi": "Mitsubishi",
}
```

Also add Mitsubishi Pajero Sport to the title parse: the title format is "YEAR MAKE MODEL",
e.g. "2021 Mitsubishi Pajero Sport". With two-word model name, `title_p[2]` would give
"Pajero" but model should be "Pajero Sport". Verify how TeamBHP renders the model name in
`sr_info` and adjust `_parse_row` if needed (may need `title_p[2:]` joined for multi-word
models).

### Step 3 — Fix pagination: stop using restore=1

Replace the fragile session-replay approach with the full search URL on every page. The
current reason for `restore=1` on page 2+ was likely to avoid URL-length limits or
server-side search ID requirements. Verify:

**Action**: Fetch page 2 with the full `_search_url(page=2)` URL and compare the response
to `restore=1&page=2`. If both return the same rows, drop `restore=1` entirely.

If the full URL works for pagination, change the loop:

```python
# Before
url = _search_url(page) if page == 1 else f"{BASE}/search_results/?restore=1&page={page}"

# After
url = _search_url(page)
```

If TeamBHP rejects page 2+ with the full URL (redirect, 0 rows, or error), document why
and consider an alternative: cache the search ID from the page-1 response (look for a hidden
field or cookie value like `search_id=XXXXX`) and replay that specific ID on subsequent pages
rather than relying on the session.

### Step 4 — Verify crawl4ai fallback gap (low priority)

`CLAUDE.md` documents "crawl4ai fallback on 403" but the code has no 403 handling. Currently
the scraper just prints the status code and breaks. Unless 403s are observed in practice,
defer this — note it as a known gap rather than implementing speculatively.

---

## Expected outcome

| Fix | Impact |
|-----|--------|
| Mitsubishi model ID | All Pajero Sport listings now captured from TeamBHP |
| Pagination fix | Up to ~135 listings/run instead of ~15 on session failures |
| (crawl4ai fallback) | Deferred — only needed if 403s observed in Actions logs |

---

## Implementation changes

- `scrapers/teambhp.py`
  - Add Mitsubishi Pajero Sport ID to `MODEL_IDS`
  - Add `"mitsubishi": "Mitsubishi"` to `MAKE_NORM`
  - Audit `_parse_row` title parsing for multi-word model names
  - Replace `restore=1` pagination with full URL per page (if probe confirms it works)
- No schema, DB, or filter changes needed (filters.py already has Mitsubishi)

---

## Files to change

- `scrapers/teambhp.py` — model ID, MAKE_NORM, _parse_row, pagination URL logic
