# Car Hunter — React + GitHub Pages Migration Guide

Migration from Streamlit to a static React app served via GitHub Pages.
Data layer stays on Supabase; the Supabase anon key is safe to ship in the
client bundle because security is enforced by RLS policies, not key secrecy.

---

## 0. How to Work — Agent Setup & Workflow

### 0.1 Install the Agency agents

Clone and install the three specialist agents you'll use throughout this project:

```bash
# Clone agency-agents (no git history needed)
degit msitarzewski/agency-agents /tmp/agency-agents
cd /tmp/agency-agents

# Install only the three agents you need directly into Claude Code
mkdir -p ~/.claude/agents
cp engineering/engineering-frontend-developer.md ~/.claude/agents/
cp engineering/engineering-code-reviewer.md      ~/.claude/agents/
cp testing/testing-reality-checker.md            ~/.claude/agents/
```

Alternatively, run the full install script to get everything:

```bash
./scripts/install.sh --tool claude-code
```

**The three agents and when to invoke them:**

| Agent | File | When |
|-------|------|------|
| Frontend Developer | `engineering-frontend-developer.md` | Implementation — all UI work, component builds, Supabase wiring |
| Code Reviewer | `engineering-code-reviewer.md` | After each implementation chunk, before marking done |
| Reality Checker | `testing/testing-reality-checker.md` | Browser verification — takes Playwright screenshots, checks behaviours against spec |

Invoke any agent in Claude Code by starting your message with its name:

```
@Frontend Developer implement the CarCard component using shadcn Card...
@Code Reviewer review the CarCard and FilterBar I just built...
@Reality Checker verify the filter behaviour and hide/delete actions at localhost:5173
```

---

### 0.2 Workflow

Work is strictly sequential — complete one task fully before starting the next.
No parallel branches, no half-finished components sitting open.

```
┌─────────────────────────────────────────────────────┐
│ PLAN                                                │
│  Break work into independently deployable chunks.   │
│  A chunk = something that builds, renders, and      │
│  can be pushed to gh-pages on its own.              │
└───────────────────┬─────────────────────────────────┘
                    │ for each chunk:
                    ▼
┌─────────────────────────────────────────────────────┐
│ IMPLEMENT  (@Frontend Developer)                    │
│  Build the chunk. shadcn components only.           │
│  No custom CSS classes where a shadcn primitive     │
│  exists. Tailwind utility classes for layout only.  │
└───────────────────┬─────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│ LINT + TYPE CHECK  (automated, run yourself)        │
│  pnpm run lint     (Biome — must be clean)          │
│  pnpm run build    (tsc + vite — must be clean)     │
│  Fix all errors before continuing.                  │
└───────────────────┬─────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│ REVIEW  (@Code Reviewer)                            │
│  Full review of the chunk just built.               │
│  Issues flagged as 🔴 blocker / 🟡 suggestion / 💭 nit │
└───────────────────┬─────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│ ADDRESS  (loop × 1)                                 │
│  Fix all 🔴 blockers. Address 🟡 suggestions if    │
│  quick. Ignore 💭 nits. Re-run lint + build.       │
│  One address round only — don't loop forever.       │
└───────────────────┬─────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────┐
│ BROWSER VERIFY  (@Reality Checker)                  │
│  Start dev server (pnpm run dev).                   │
│  Reality Checker uses Playwright to screenshot and  │
│  verify behaviours against spec (see §0.3).         │
│  It is fine to hit the real Supabase DB — no        │
│  mocks, no fixtures. At the end of each session,    │
│  un-hide any listings you hid during testing        │
│  (set is_active = true where is_active = false).    │
└───────────────────┬─────────────────────────────────┘
                    │ chunk done → pick next chunk
                    ▼
                (repeat)
```

---

### 0.3 UI Spec

Match the Streamlit layout exactly — users already have muscle memory for it.

**Mobile (< 768 px)**
- Single-column card list
- Hamburger icon (top-right) opens a `Sheet` (shadcn) from the right side
- Sheet contains all filters: Make, Model, Year range, Max KMs, Sort

**Desktop (≥ 768 px)**
- Two-column card grid
- No hamburger — filters live in a horizontally-scrollable pill/chip bar
  pinned below the header. Overflow scrolls left–right, no wrapping, no
  vertical expansion. Each filter is a shadcn `Select` or `ToggleGroup`.

**Cards**
- Thumbnail image (click → fullscreen modal, use shadcn `Dialog`)
- Make · Model · Variant · Year · KMs · Colour · Transmission
- Price (bold), sourced from cheapest listing in `sources`
- Source links (one per marketplace) as small badges
- Hide button (soft-delete) and Delete button (hard-delete), icon-only,
  muted until hovered — use shadcn `Button` variant ghost + Lucide icons

**shadcn constraint**
Every interactive or structural element must come from shadcn. Do not reach
for headless-ui, radix directly, or custom components when a shadcn primitive
covers the need. Install components as you need them:

```bash
pnpm dlx shadcn@latest add card button sheet select dialog badge toggle-group
```

---

### 0.4 shadcn Setup with Vite (do this before any UI work)

shadcn expects path aliases. Wire them up first:

```json
// tsconfig.app.json — add under compilerOptions
{
  "baseUrl": ".",
  "paths": {
    "@/*": ["./src/*"]
  }
}
```

```bash
pnpm add -D @types/node
```

```ts
// vite.config.ts — add resolve.alias
import path from 'node:path'

export default defineConfig({
  base: '/car-hunter-ui/',
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
})
```

Then init shadcn (choose the defaults, style: default, base colour: neutral):

```bash
pnpm dlx shadcn@latest init
```

shadcn writes `components/ui/` under `src/`, and updates `tailwind.config.js`
and `globals.css`. Commit this before building any components.

---

### 0.5 Suggested chunk breakdown

| # | Chunk | What ships |
|---|-------|-----------|
| 1 | Scaffold + shadcn init | Repo boots, shadcn wired, placeholder App |
| 2 | Data layer | `useListings` hook, Supabase client, type definitions |
| 3 | CarCard | Single card with all fields, hide/delete wired |
| 4 | Layout + grid | Header, two-column desktop grid, single-column mobile |
| 5 | Filter bar | Desktop scrollable bar + mobile Sheet, client-side filtering |
| 6 | Image modal | Dialog fullscreen on thumbnail click |
| 7 | Deploy | GitHub Actions workflow, gh-pages, env secrets |

Each chunk is independently deployable — chunk 3 can go live showing cards
with no filter bar; chunk 4 can go live with layout but no filtering yet.

---

---

## 1. Prerequisites

```bash
# pnpm (required — the starter enforces it via preinstall hook)
npm install -g pnpm

# degit (zero-history clone of any GitHub repo)
npm install -g degit
```

---

## 2. Bootstrap with degit

```bash
# Clone the starter into a new directory (no git history, no .git folder)
degit ANSH4195/vite-tailwind-biome-starter car-hunter-ui

cd car-hunter-ui
git init && git add -A && git commit -m "chore: init from vite-tailwind-biome-starter"
```

Stack in the starter: React 19 + TypeScript + Vite 7 (SWC) + Tailwind CSS 4 + Biome 2.

---

## 3. Upgrade all packages

The starter pins packages at a point in time. After cloning, bump everything
to the latest compatible versions before writing any app code.

```bash
# Install what the lockfile says first (sanity check)
pnpm install

# Upgrade all deps to latest (rewrites package.json ranges + lockfile)
pnpm update --latest

# Verify nothing is broken
pnpm run build
pnpm run dev   # spot-check in browser
```

If `pnpm update --latest` produces peer-dep warnings, address them before
continuing — Tailwind 4 + Vite integration in particular has moved fast.

Commit after a clean build:

```bash
git add package.json pnpm-lock.yaml && git commit -m "chore: upgrade all packages to latest"
```

---

## 4. Vite config — GitHub Pages base path

GitHub Pages serves your site at `https://ANSH4195.github.io/car-hunter-ui/`
(note the subpath). Vite needs to know this so asset URLs are correct.

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  base: '/car-hunter-ui/',   // <-- match your repo name exactly
  plugins: [react(), tailwindcss()],
})
```

---

## 5. Add Supabase client

```bash
pnpm add @supabase/supabase-js
```

Create `src/lib/supabase.ts`:

```ts
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
)
```

Create `.env.local` (git-ignored):

```
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...
```

**Why the anon key is safe here**: it's a public-facing key designed for
client-side use. Supabase Row Level Security (RLS) policies are what actually
gate reads and writes — the key itself is not the security boundary. Never put
the service role key in client code.

For GitHub Actions (deploy step), add both as repository secrets:
`VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.

---

## 6. GitHub Actions — build and deploy

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: latest

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm

      - run: pnpm install --frozen-lockfile

      - run: pnpm run build
        env:
          VITE_SUPABASE_URL: ${{ secrets.VITE_SUPABASE_URL }}
          VITE_SUPABASE_ANON_KEY: ${{ secrets.VITE_SUPABASE_ANON_KEY }}

      - uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
```

In the repo Settings → Pages → Source, set branch to `gh-pages` / root.

---

## 7. Core data hook

All Streamlit filtering (make, model, year, kms, sort) moves to client-side
state. With a small dataset (hundreds of listings) this is fine.

```ts
// src/hooks/useListings.ts
import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

export type Listing = {
  id: string
  make: string
  model: string
  variant: string | null
  year: number
  kms: number
  fuel: string
  transmission: string | null
  color: string | null
  location: string | null
  price: number
  image_url: string | null
  sources: Record<string, { url: string; price: number }>
  first_seen: string
  is_active: boolean
}

export function useListings() {
  const [listings, setListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase
      .from('listings')
      .select('*')
      .eq('is_active', true)
      .order('first_seen', { ascending: false })
      .then(({ data }) => {
        setListings(data ?? [])
        setLoading(false)
      })
  }, [])

  const hide = async (id: string) => {
    await supabase.from('listings').update({ is_active: false }).eq('id', id)
    setListings(l => l.filter(x => x.id !== id))
  }

  const remove = async (id: string) => {
    await supabase.from('listings').delete().eq('id', id)
    setListings(l => l.filter(x => x.id !== id))
  }

  return { listings, loading, hide, remove }
}
```

---

## 8. Using context7 MCP during development

context7 is an MCP plugin that fetches **live, version-matched documentation**
for any library and injects it into the Claude Code context window. This means
Claude answers questions about `@supabase/supabase-js`, `react`, `tailwindcss`
etc. using the actual current docs rather than training-data snapshots.

### How to invoke it

Add `use context7` anywhere in your prompt to Claude Code:

```
How do I set up realtime subscriptions in Supabase? use context7
```

```
What's the correct way to use Tailwind CSS v4 arbitrary values? use context7
```

```
Show me how to configure vite base path for GitHub Pages. use context7
```

context7 resolves the library from your prompt, fetches the relevant doc pages
for the version in your `package.json`, and appends them to the context before
Claude answers. You get accurate answers even for APIs that changed after the
model's training cutoff (e.g. Tailwind v4's new `@import` syntax, Vite 7
config changes, React 19 new hooks).

### When it matters most for this project

| Situation | Why context7 helps |
|-----------|-------------------|
| Supabase RLS policy syntax | Changes frequently; training data may be stale |
| Tailwind v4 config | Major syntax break from v3 — `tailwind.config.js` is now mostly optional |
| Vite 7 plugin API | New plugin hooks not in training data |
| `@supabase/supabase-js` v2 → v3 differences | Auth and realtime APIs changed |

### MCP setup (if not already configured)

context7 runs as an MCP server. Add it to Claude Code's MCP config:

```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp
```

Verify it's active:

```bash
claude mcp list
```

---

## 9. Supabase RLS (required before going live)

The anon key is public, so Supabase RLS is your actual security layer.
Minimum policies for this app:

```sql
-- Allow anyone to read active listings (public dashboard)
create policy "read active listings"
  on listings for select
  using (is_active = true);

-- Block anonymous writes (you'll need to be authenticated to hide/delete)
-- OR just allow anon writes if this is a personal-only tool you don't share publicly
create policy "allow anon mutations"
  on listings for update
  using (true);

create policy "allow anon deletes"
  on listings for delete
  using (true);
```

If you want to lock down writes so only you can hide/delete, wire up
Supabase Auth (magic link to your email) and change the policies to
`using (auth.role() = 'authenticated')`.

---

## 10. Project structure (target)

```
car-hunter-ui/
├── src/
│   ├── lib/
│   │   └── supabase.ts
│   ├── hooks/
│   │   └── useListings.ts
│   ├── components/
│   │   ├── CarCard.tsx
│   │   ├── FilterBar.tsx
│   │   └── ImageModal.tsx
│   ├── App.tsx
│   └── main.tsx
├── .env.local          # git-ignored
├── vite.config.ts
├── biome.json
└── package.json
```

The entire Streamlit app (`app.py`) maps to roughly:
- `FilterBar.tsx` — make/model/year/kms dropdowns + sort
- `CarCard.tsx` — image, specs, price, source links, hide/delete buttons
- `ImageModal.tsx` — fullscreen image on click (no iframe hacks needed)
- `App.tsx` — fetches via `useListings`, wires filters, renders grid
