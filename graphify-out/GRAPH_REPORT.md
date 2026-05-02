# Graph Report - .  (2026-05-02)

## Corpus Check
- Corpus is ~6,928 words - fits in a single context window. You may not need a graph.

## Summary
- 136 nodes · 188 edges · 17 communities detected
- Extraction: 70% EXTRACTED · 30% INFERRED · 0% AMBIGUOUS · INFERRED: 57 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Project Docs & Roadmap|Project Docs & Roadmap]]
- [[_COMMUNITY_Listing Parsing Pipeline|Listing Parsing Pipeline]]
- [[_COMMUNITY_Data Normalization Layer|Data Normalization Layer]]
- [[_COMMUNITY_Core Listing Dataclass|Core Listing Dataclass]]
- [[_COMMUNITY_Dashboard & Display|Dashboard & Display]]
- [[_COMMUNITY_Supabase DB Layer|Supabase DB Layer]]
- [[_COMMUNITY_Carwale Scraper|Carwale Scraper]]
- [[_COMMUNITY_OLX Scraper|OLX Scraper]]
- [[_COMMUNITY_Spinny Scraper|Spinny Scraper]]
- [[_COMMUNITY_Orchestrator & Filters|Orchestrator & Filters]]
- [[_COMMUNITY_Listing Lifecycle|Listing Lifecycle]]
- [[_COMMUNITY_OLX Source Constant|OLX Source Constant]]
- [[_COMMUNITY_Spinny Source Constant|Spinny Source Constant]]
- [[_COMMUNITY_TeamBHP Source Constant|TeamBHP Source Constant]]
- [[_COMMUNITY_Project Context (CLAUDE.md)|Project Context (CLAUDE.md)]]
- [[_COMMUNITY_Combined Requirements|Combined Requirements]]
- [[_COMMUNITY_Runtime Config|Runtime Config]]

## God Nodes (most connected - your core abstractions)
1. `CarListing` - 18 edges
2. `CarListing` - 10 edges
3. `TeamBHP scrape` - 9 edges
4. `parse_kms()` - 7 edges
5. `OLX scrape` - 7 edges
6. `_parse_card()` - 6 edges
7. `cars24._parse_card()` - 6 edges
8. `cardekho._parse_card()` - 6 edges
9. `nthgear._parse_card()` - 6 edges
10. `Spinny scrape` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Supabase layer — upsert listings, soft-delete, fetch for UI.` --uses--> `CarListing`  [INFERRED]
  db.py → scrapers/base.py
- `Precarmart Scraper (TODO)` --conceptually_related_to--> `crawl4ai + Playwright JS-rendering Pattern`  [EXTRACTED]
  TODO.md → scrapers/olx.py
- `Session-based Pagination Pattern (restore=1)` --conceptually_related_to--> `Incremental Scraping Optimization (TODO)`  [INFERRED]
  scrapers/teambhp.py → TODO.md
- `_parse_card()` --calls--> `normalize()`  [INFERRED]
  scrapers/nthgear.py → normalizer.py
- `_parse_card()` --calls--> `parse_price()`  [INFERRED]
  scrapers/olx.py → normalizer.py

## Hyperedges (group relationships)
- **Scraper → Filter → Upsert Pipeline** — scrape_main, filters_is_valid, db_upsert, base_carlisting [EXTRACTED 0.95]
- **Listing Deduplication via SHA256 Hash** — base_listing_id, db_upsert, schema_listing_id_col [EXTRACTED 0.95]
- **Normalizer Parsing Utilities (Gemini + regex)** — normalizer_normalize, normalizer_parse_price, normalizer_parse_kms [EXTRACTED 0.90]
- **crawl4ai JS-Rendering Scrapers (OLX + Spinny)** — olx__fetch_rendered, spinny__fetch_rendered, crawl4ai_pattern [EXTRACTED 0.95]
- **Make Normalization Maps Across All Three Scrapers** — olx_make_map, spinny_make_norm, teambhp_make_norm [INFERRED 0.90]
- **Pagination with Deduplication Pattern (Spinny + TeamBHP)** — spinny_scrape, teambhp_scrape, pagination_dedup_pattern [INFERRED 0.88]

## Communities

### Community 0 - "Project Docs & Roadmap"
Cohesion: 0.11
Nodes (23): crawl4ai + Playwright JS-rendering Pattern, Gemini Call Caching Optimization (TODO), Incremental Scraping Optimization (TODO), Make Normalization Map Pattern, OLX _fetch_rendered, OLX _listing_url, OLX _parse_card, OLX MAKE_MAP (+15 more)

### Community 1 - "Listing Parsing Pipeline"
Cohesion: 0.16
Nodes (17): CarListing, cardekho._parse_card(), cardekho.scrape(), cars24._listing_url(), MAKE_NORM, cars24._parse_card(), cars24.scrape(), carwale._extract_stocks() (+9 more)

### Community 2 - "Data Normalization Layer"
Cohesion: 0.2
Nodes (12): normalize(), parse_kms(), parse_price(), Gemini Flash-Lite: parse messy listing text → structured fields. Only called whe, _parse_card(), CarDekho scraper — Karnataka, Diesel, target makes. Card structure confirmed:, scrape(), _search_url() (+4 more)

### Community 3 - "Core Listing Dataclass"
Cohesion: 0.2
Nodes (10): CarListing, _fetch_rendered(), _listing_url(), _parse_card(), Cars24 scraper — Bangalore, diesel, target makes. Cars24 uses Next.js App Router, scrape(), _parse_row(), TeamBHP Classifieds scraper — nationwide diesel listings. The site is server-ren (+2 more)

### Community 4 - "Dashboard & Display"
Cohesion: 0.22
Nodes (10): load(), SOURCE_COLORS, listing_id(), fetch_active(), upsert(), id column (sha256 hash), listings table, sources column (jsonb) (+2 more)

### Community 5 - "Supabase DB Layer"
Cohesion: 0.48
Nodes (6): fetch_active(), _get(), hard_delete(), Supabase layer — upsert listings, soft-delete, fetch for UI., soft_delete(), upsert()

### Community 6 - "Carwale Scraper"
Cohesion: 0.53
Nodes (5): _extract_stocks(), CarWale scraper — Karnataka, Diesel, target makes. URL format: /used/{city}/{mak, scrape(), _search_url(), _to_listing()

### Community 7 - "OLX Scraper"
Cohesion: 0.53
Nodes (5): _fetch_rendered(), _listing_url(), _parse_card(), OLX scraper — Karnataka-wide, pre-filtered URL. OLX is JS-heavy; we use crawl4ai, scrape()

### Community 8 - "Spinny Scraper"
Cohesion: 0.53
Nodes (5): _fetch_rendered(), _listing_url(), _parse_card(), Spinny scraper — Bengaluru diesel listings via crawl4ai. Spinny is a client-side, scrape()

### Community 9 - "Orchestrator & Filters"
Cohesion: 0.4
Nodes (3): is_valid(), main(), Main entry point — runs all scrapers, filters results, upserts to Supabase. Run

### Community 11 - "Listing Lifecycle"
Cohesion: 0.67
Nodes (2): soft_delete(), is_active column

### Community 16 - "OLX Source Constant"
Cohesion: 1.0
Nodes (1): OLX Scraper Source Constant

### Community 17 - "Spinny Source Constant"
Cohesion: 1.0
Nodes (1): Spinny Scraper Source Constant

### Community 18 - "TeamBHP Source Constant"
Cohesion: 1.0
Nodes (1): TeamBHP Scraper Source Constant

### Community 19 - "Project Context (CLAUDE.md)"
Cohesion: 1.0
Nodes (1): CLAUDE.md (Project Context)

### Community 20 - "Combined Requirements"
Cohesion: 1.0
Nodes (1): requirements.txt (combined)

### Community 22 - "Runtime Config"
Cohesion: 1.0
Nodes (1): runtime.txt (Python 3.11)

## Knowledge Gaps
- **16 isolated node(s):** `Gemini Flash-Lite: parse messy listing text → structured fields. Only called whe`, `Main entry point — runs all scrapers, filters results, upserts to Supabase. Run`, `SOURCE_COLORS`, `MAKE_NORM`, `id column (sha256 hash)` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Listing Lifecycle`** (3 nodes): `hard_delete()`, `soft_delete()`, `is_active column`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `OLX Source Constant`** (1 nodes): `OLX Scraper Source Constant`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Spinny Source Constant`** (1 nodes): `Spinny Scraper Source Constant`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `TeamBHP Source Constant`** (1 nodes): `TeamBHP Scraper Source Constant`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Project Context (CLAUDE.md)`** (1 nodes): `CLAUDE.md (Project Context)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Combined Requirements`** (1 nodes): `requirements.txt (combined)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Runtime Config`** (1 nodes): `runtime.txt (Python 3.11)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CarListing` connect `Core Listing Dataclass` to `Data Normalization Layer`, `Supabase DB Layer`, `Carwale Scraper`, `OLX Scraper`, `Spinny Scraper`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Why does `Supabase layer — upsert listings, soft-delete, fetch for UI.` connect `Supabase DB Layer` to `Core Listing Dataclass`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `CarListing` connect `Listing Parsing Pipeline` to `Dashboard & Display`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `CarListing` (e.g. with `Supabase layer — upsert listings, soft-delete, fetch for UI.` and `CarDekho scraper — Karnataka, Diesel, target makes. Card structure confirmed:`) actually correct?**
  _`CarListing` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `CarListing` (e.g. with `cars24.scrape()` and `cardekho.scrape()`) actually correct?**
  _`CarListing` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `TeamBHP scrape` (e.g. with `Session-based Pagination Pattern (restore=1)` and `Pagination with URL-based Deduplication Pattern`) actually correct?**
  _`TeamBHP scrape` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `parse_kms()` (e.g. with `_parse_card()` and `_parse_card()`) actually correct?**
  _`parse_kms()` has 6 INFERRED edges - model-reasoned connections that need verification._