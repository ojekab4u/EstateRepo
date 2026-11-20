# ComfyHome 2.0 — Screen Specifications

> **Design language: matched to the LIVE site** (comfyhome.onrender.com), inspected Nov 2026.
> Kept as-is: navy contact strip + coral "Add Listing" topbar · white header with centered nav + square white icon buttons · light hero with eyebrow label + huge navy Poppins heading + left-rule paragraph + coral CTA + house illustration · orange-bordered search strip · homeverse footer.
> Inner pages adopt the homeverse language (they're currently unstyled default Bootstrap): coral price, blue title, photo cards with location overlay, icon feature columns, agent footer with square icon buttons, dark navy table headers.
> **Deliberate deviations (new features only):** ① TrueCost badge — the product's core new component (green/amber/red = cost-tier semantics, never brand colors). ② "Max true cost" filter + true-cost sorting. ③ Power & utilities inputs (extends the published model). ④ Request Inspection flow (replaces dead "Just Book!" button). Everything else follows the existing theme tokens (`--orange-soda`, `--prussian-blue`, `--dark-jungle-green`, `--cultured`, `--cadet`, Poppins/Nunito Sans).

Status legend: `EXISTS` = screen exists today (needs upgrade) · `NEW` = to be built · `REBUILD` = exists but needs significant rework.

---

## A. House-hunter journey

### 1. Home — `EXISTS` (rework)
**Goal**: communicate the differentiator in 5 seconds and start a search.

- Hero: value prop headline ("Know the *real* cost of a home before you rent it") + search bar with **"Max true cost / yr"** selector — new, unique filter no competitor has.
- Live fuel-price ticker chip (petrol/diesel national averages) — signals freshness, doubles as marketing.
- Trust strip: "20% avg savings, research-proven" linking to the published paper (SEO backlink + credibility).
- **Stat tiles**: listings, estimates run, reported savings (social proof).
- Featured properties **sorted by true cost** with CostBadges, incl. one deliberate 🔴 "cost trap" example + green insight callout (educates the core concept instantly).
- "How it works" 3-step strip.
- **Backend**: replace `random.sample` on the full queryset with `Property.objects.all()[:N]` ordered by true cost cache; paginate.

### 2. Search & Listings — `EXISTS` (rebuild; merge `property_list` + `property_search`)
**Goal**: find properties by true cost, not rent.

- Left filter panel: keyword, **max true cost (range slider)**, rent range, bedrooms/bathrooms as `gte` chips, property type, **"Commute to (work)"** autocomplete input.
- Results grid with CostBadge + commute km + amenity score per card; sort dropdown defaults to **"Lowest true cost"**; List/Map toggle (map view in Phase 3).
- Fixed: one unified search endpoint (currently two inconsistent views: exact-match vs `gte`), pagination, `$`→`₦` fix, results count.
- **Backend**: new `true_cost_cache` fields on Property (see ROADMAP) so sorting/filtering is a DB query, not per-row Google API calls.

### 3. Property Detail — `EXISTS` (rebuild)
**Goal**: full picture + one-tap estimate.

- Photo gallery/carousel (exists), map with pin (exists), amenities section **NEW**: `Places API Nearby` for hospitals, schools, markets, ATMs within 2 km + computed **AmenityScore (0–100)** chip.
- Sticky right sidebar "True Cost of Living": CostBadge with rent/transport/power split bar, table of rent/transport/power per month, **"Run full estimate"** CTA (pre-filled with user's saved profile → instant result), Compare + Save buttons.
- Agent card with rating + **Request inspection** (replaces dead "Just Book!" button; creates an InspectionRequest model row).
- Description includes instalment terms (60/40 etc.).

### 4. Cost Estimator — `EXISTS` (major rework — the flagship)
**Goal**: the research-proven core, modernized.

- Property banner with verified geocode (cached `lat/lng` on Property — restores fields removed in migration 0007).
- Step 1: fuel prices with "↻ auto-sync national average" (new FuelPrice model, admin-updated or scraped).
- Step 2: dynamic vehicle rows (vehicle, work/main destination autocomplete, trips/week) + "add another destination" (markets, church, family) — exists today but rebuilt cleanly; delete the 4 stacked template versions and 3 dead JS copies in the current file.
- Transport-mode chips: Car / Danfo-BRT (transit) / Okada (2-wheel) / Walk — maps to Google Directions `mode=transit|driving|walking` (paper's own recommendation: real-time traffic & more modes).
- **Traffic-aware toggle**: uses Directions API with `departure_time` + traffic model.
- Results: vehicle summary + period table (weekly/monthly/yearly) + **optional Power & Utilities inputs** (prepaid meter est., gen/diesel backup) — extends the model `Tc = R + Tr` to `Tc = R + Tr + U`, exactly the paper's stated future work.
- Insight callout (e.g., savings vs. compared property), Save/Export PDF/Compare actions.
- **Backend fixes**: actually persist to HistoricalData (currently dead code); use captured `place_id`s; cache geocodes; server-side compute already OK; Decimal-safe fuel rate math.

### 5. True-Cost Comparison — `NEW`
**Goal**: the decision tool. This screen is the killer feature.

- Pick 2–4 properties (from saved estimates or search).
- Cards per property: 🏆 Best value / ⚠ Cost trap tag, rent, commute (+distance chip), power, true cost/yr & /mo, amenity score.
- Metric table with best/worst cell highlighting; **% of income** benchmark (user-entered or national average) — supports the affordability-ratio research framing.
- Insight callouts generated from the delta ("Cheaper rent beats shorter commute here").
- Backend: `ComparisonSet` model (user FK, M2M properties/estimates).

### 6. Saved Estimates — `NEW` (activates dormant HistoricalData)
- KPI tiles: count, cheapest true cost, est. yearly savings vs. most expensive, current fuel profile.
- History table: property, saved date, rent/transport/true cost per year, actions (Compare, Open, Delete).
- Phase 3: **fuel-price re-valuation** — background job re-runs saved estimates when FuelPrice changes; email/notification with delta ("Your Akobo transport rose ₦1,900/mo").
- Export PDF/share (WhatsApp link — Nigeria-relevant).

### 7. User profile / Settings — `NEW` (small)
- Default commute profile (vehicles, work address, trips) — powers one-tap estimates on property detail.
- Saved properties, comparison sets, notification prefs, password change, delete account.

---

## B. Agent journey

### 8. Agent Dashboard — `NEW`
- KPI tiles: active listings, views 30d, estimate-runs on own listings, inspection requests.
- Listing table: title, rent, **true cost\*** (auto-computed), views, status (Live/Pending review).
- Inspection-request inbox; listing quality tips (photos + true-cost badge → more engagement).
- Listing lifecycle: Draft → Pending review → Live → Archived (fixes today's no-edit/no-delete gap).

### 9. Create Listing — `EXISTS` (rebuild as 5-step wizard)
- Steps: Basics → Location → Photos & details → **Cost inputs** → Review.
- Address field: Google autocomplete; **server must consume `place_id`** (currently captured in JS then discarded).
- **NEW required fields** feeding the power/utilities module: prepaid meter Y/N, water source, gen/inverter backup, estate service charge.
- Multi-image upload retained (use the existing unused `PropertyImageForm`); main image required.
- Review step shows the auto-computed CostBadge preview before publish.
- Backend: property **edit/delete** views (missing today), status field, admin review.

---

## C. Auth & account

### 10. Login / Register — `EXISTS` (rebuild)
- Dual-role tabs: House-hunter / Agent-Landlord (agent adds passport upload + agency name).
- Real email verification (activate the commented-out EMAIL_* settings) and real password reset — today's messages lie ("check your email").
- Google OAuth optional Phase 3.
- Keep `next` redirect behavior; add rate-limiting (django-axes) and delete the broken `register.html` legacy template.

### 11. Static pages (About, Services, Contact, Blog) — `EXISTS` (light touch)
- Contact form wires to real email or creates ContactMessage model rows (currently `pass` stubs).
- Blog becomes simple CMS model or static articles — including the published paper as a post (SEO).
- Add SEO metadata templates + sitemap (Lighthouse SEO was the weakest score at 82).

---

## D. Screen inventory summary

| # | Screen | Status | Phase |
|---|--------|--------|-------|
| 1 | Home | rework | P1 |
| 2 | Search & Listings | rebuild | P1 |
| 3 | Property Detail | rebuild | P1–P2 |
| 4 | Cost Estimator | major rework | P2 |
| 5 | True-Cost Comparison | NEW | P2 |
| 6 | Saved Estimates | NEW | P2 |
| 7 | Profile/Settings | NEW | P3 |
| 8 | Agent Dashboard | NEW | P2–P3 |
| 9 | Create Listing | rebuild | P1–P2 |
| 10 | Auth | rebuild | P1 |
| 11 | Static pages | light touch | P1–P3 |

Mobile: every screen above has a single-column stack variant; the estimator and comparison get bottom-sheet summaries on mobile. PWA wrapper (installable, offline shell) is a Phase 3 stretch goal.
