# ComfyHome 2.0 — Design System

> Product: True-cost housing platform (rent + commute + utilities)
> Research basis: *Development of Real Estate Platform with Geolocation for Effective Rent-Cost Estimation* — DOI 10.5281/zenodo.18474673

---

## 1. Design principles

| # | Principle | Rationale |
|---|-----------|-----------|
| 1 | **Show the truth, not just the price** | Every property surface (card, list row, detail, comparison) shows *true cost*, never rent alone. This is the product's moat. |
| 2 | **Cost is the primary sort/filter dimension** | Users proved (TAM, n=34, 76% usefulness) that total-cost visibility drives decisions. |
| 3 | **Trust through transparency** | Every estimate shows its assumptions (fuel price, trips, distance) and data source. Never show a number without "why". |
| 4 | **Nigeria-first** | ₦ everywhere, Nigerian commute modes (danfo, okada, BRT), local landmarks, instalment culture (60/40 rent splits). |
| 5 | **Progressive disclosure** | Simple search first; deep estimator one tap away. Don't front-load complexity. |

---

## 2. Colors

Brand palette is taken directly from the **live site's existing theme tokens** (`static/css/style.css`, homeverse theme) so the redesign keeps brand continuity:

```
Brand — from live site CSS variables
Orange Soda  #FF5A3D  (hsl 9,100%,62%)  → primary accent: buttons, links, logo, active states
  ↳ hover/dark   #C93C25  (hsl 7,72%,46% — the theme's dark-mode override value)
Prussian Blue    #0B2C3C  (hsl 200,69%,14%) → top bar, footer, hero gradient
Dark Jungle Green #071A1D (hsl 188,63%,7%)  → deepest surfaces, hero gradient start
Yellow Green     #76C520  (hsl 89,72%,45%)  → secondary accent (use sparingly; contrast!
Cultured 1/2     #EDEDED / #F4F7F8        → page & section backgrounds
Seashell         #FEF3F1  (hsl 8,100%,97%) → coral tint (chips, avatar bg)
Misty Rose       #F5E4E2  (hsl 7,56%,91%)  → soft highlight tint
Alice Blue       #F0F7FF  (hsl 210,100%,97%) → cool info tint
Cadet            #5E707C  (hsl 200,15%,43%) → secondary text (theme's muted gray-blue)

Functional — cost-tier semantics (NOT brand colors; reserved meanings)
Efficient 🟢  #0E9F6E emerald → transport < 25% of true cost, best-value, positive deltas
Moderate 🟡  #F59E0B amber    → transport 25–40% of true cost, pending states
Cost trap 🔴 #DC2626 red      → transport > 40% of true cost, high-commute warnings
Transit  🔵 #3B82F6 blue      → transit modes, live-data tags
Ink 900/700/500/300/100/50    #0F172A → #F8FAFC (text & neutral surfaces)
```

**Rule**: coral/navy carry the *brand*; emerald/amber/red are reserved exclusively for cost-tier meaning so a coral button never competes with a cost verdict.

### Cost-tier color coding (used consistently everywhere)
| Badge color | Meaning | Rule of thumb |
|---|---|---|
| 🟢 Green | Efficient — transport is a small share of true cost | transport < 25% of true cost |
| 🟡 Amber | Moderate — worth comparing | transport 25–40% |
| 🔴 Red | Cost trap — rent looks cheap, living is expensive | transport > 40% of true cost |

---

## 3. Typography

Matches the live theme's font stack:

- **Headings / brand / numbers**: Poppins (500–800).
- **Body / forms**: Nunito Sans (400–800).
- Scale: H1 32px · H2 24px · H3 17–19px · body 13–14px · caption/hint 11–12px.
- All money values use `tabular-nums` and the `₦` prefix with thousands separators.

## 4. Core components

1. **CostBadge** — the signature component. Gradient tile: label ("True cost / yr") + value + rent/transport split bar. Color = cost tier.
2. **PropertyCard** — image, title, chips (rent/buy), location, rent price, CostBadge, feature row (beds, baths, **commute km**, amenity score).
3. **CostBadge tiers** — gradient variants green/amber/red.
4. **Estimator form** — dynamic vehicle rows (vehicle select + autocomplete destination + trips/week), transport-mode chips, "traffic-aware" toggle.
5. **Results table** — vehicle summary + period summary (weekly/monthly/yearly), with a highlighted True-cost total row.
6. **AmenityPanel** — nearby facilities list with distances (Places API) + AmenityScore chip.
7. **MapBlock** — property pin + amenity pins with legend.
8. **ComparisonCard** — per-property column with per-metric rows; winner gets 🏆 Best value + green border; loser flagged ⚠ Cost trap.
9. **StatTile** — dashboard KPI tiles.
10. **Callout** — insight/education strip (amber = caution, green = savings insight).

## 5. Patterns

- **Sticky cost sidebar** on property detail — the estimate is always one glance away.
- **Autocomplete-first addressing**: any address input uses Google Places Autocomplete; picking a suggestion captures `place_id` (fixes the current bug where place_id is discarded).
- **Assumption chips**: fuel price, profile, trip count shown next to results ("Profile: 1 car · ₦998/L · 10 trips/wk").
- **Empty states**: dashed panels with a single primary action, never blank pages.
- **Honest auth**: no fake "check your email" flows — real verification or no message.

## 6. Accessibility & performance targets

Match/beat the paper's Lighthouse scores (Perf 83, A11y 91, BP 96, SEO 82):

- Contrast ≥ 4.5:1 for all text (never put white text on Yellow Green #76C520; use emerald #0E9F6E or Dark Jungle for text-bearing surfaces).
- All cost data also available as text/tables, not only in graphics.
- Keyboard-navigable estimator; visible focus rings.
- Images lazy-loaded; map iframes deferred; cached geocodes (server-side) — no per-request geocoding.
- Semantic headings, `<label for>` on all inputs, alt text on property photos.
