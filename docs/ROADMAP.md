# ComfyHome 2.0 — Development Roadmap

> Evolution of the final-year project into a market-ready true-cost housing platform.
> Context: Nigerian real estate = $26.7B (2025) growing 6.57% CAGR; affordability is the #1 crisis (rents +20–45%, >50% of Lagos income spent on rent, mortgages <1% GDP). The differentiator — *total cost of living* — is validated by the published research (DOI 10.5281/zenodo.18474673: 20% savings, 76% TAM usefulness).
>
> **Budget constraint: ₦0.** No dollar card yet → Google Maps Platform (requires billing) is deferred. The platform runs on a free, provider-swappable geo stack (`RealEstate/geo.py`, `GEO_PROVIDER=osm`): Leaflet + OpenStreetMap tiles (maps), Nominatim (geocode, cached + fallback chain, 1 req/s respected), Photon (autocomplete), OSRM (routes). Flip `GEO_PROVIDER=google` + add keys when billing is available — no code changes. Transit/okada modes are Google-side features for later; car mode is free today. Render free tier stays (note: spins down when idle; first request is slow — acceptable for demo).

---

## Phase 0 — Stabilize & secure (Week 1–2) 🔴 DO FIRST

The current repo has deploy-breaking and security debt that blocks everything else.

**Security**
- [ ] Move `SECRET_KEY` and `GOOGLE_API_KEY` fully to environment (django-environ or decouple — decouple is already installed).
- [ ] `ALLOWED_HOSTS` from `['*']` → explicit domains.
- [ ] `.gitignore`: add `db.sqlite3`, `media/`, `staticfiles/`, `__pycache__/`, `venv/`; purge committed DB, media & passport photos from git history (`git filter-repo`).
- [ ] Add rate-limiting on login (django-axes); enable the commented EMAIL_* settings for real verification & password reset.

**Deploy blockers**
- [ ] Fix `build.sh`: `collectsatic`→`collectstatic`, `migratelk`→`migrate`, shebang `#!/user/bin/env bash`→`#!/usr/bin/env bash`.
- [ ] Fix `admin.py`: remove invalid `filter=` attrs (Vehicle, User), rename the `User` ModelAdmin class.
- [ ] Fix settings static-files DEBUG branch (string-in-tuple bug).
- [ ] Switch SQLite → PostgreSQL (psycopg2 already installed) before adding real users.

**Dead-code purge (≈50% of views.py is commented variants)**
- [ ] Delete 3 commented `cost_estimation_detail` versions; 3 of 4 stacked versions in `cost_estimation_detail.html`; unused forms (`UserRegistration*`, `PropertySearchForm`, `CostEstimationForm`), orphaned templates (`register.html` — it 500s on a dead URL, `cost_estimation.html`, `property_search_results.html`), misnamed `cost_estimation.py` (it's JS), commented-out `propertylist.js`.
- [ ] Merge `property_list` + `property_search` into one view with consistent `gte` filters.
- [ ] Add a smoke test suite (Django TestCase) — `tests.py` is empty today. Set up CI (GitHub Actions).

**Live-site bugs found during design inspection (Nov 2026)**
- [x] Property detail page throws JS alert "Geocode… REQUEST_DENIED" and the map shows "For development purposes only" — RESOLVED ₦0: Google Maps replaced with Leaflet + Nominatim (key-free, no billing), server-side geocode cache added.
- [x] Stray unrelated screenshot (student dashboard, "NACOSS – TECH-U © 2024") in a property carousel — test data; will be replaced by mock seed data (below).
- [ ] Inner pages (property list/detail) use unstyled default Bootstrap (blue buttons) that clashes with the homeverse home theme — Phase 1 aligns them to the theme (per SCREEN_SPECS.md).

**Mock data seeding (user request: replace old test images)**
- [ ] `seed_demo` management command: 1 demo agent + 1 demo customer, 12–15 properties across Ibadan/Lagos (real streets, area coords), generated placeholder property images (Pillow, no downloads), demo vehicles (Honda Civic 0.068 L/km, Kia Rio 0.071 L/km), 1–2 pre-saved estimates.
- [ ] Purge old test uploads (agent_passports/*, property_images/* test shots) from repo history during git cleanup.

**Exit criteria**: deploys cleanly, zero commented code blocks >20 lines, tests green in CI, estimator works end-to-end on the free geo stack.

---

## Phase 1 — Foundation & data engine (Week 3–6)

**Data model (prerequisite for every new feature)**
- [ ] `Property`: restore `latitude`/`longitude` (dropped in migration 0007) + add `place_id`, `status` (draft/pending/live/archived), utility fields (prepaid_meter, water_source, power_backup, service_charge).
- [ ] `FuelPrice` model (fuel_type, price_per_litre, effective_date) — admin-managed; powers the auto-sync chip.
- [ ] Activate & extend `HistoricalData` → rename `Estimate` (user, property, profile JSON, results JSON, created_at).
- [ ] `EstimateProfile` (default vehicles/destinations per user) for one-tap estimates.
- [ ] `true_cost_cache` fields on Property (rent benchmark estimate for a *typical* profile) so listings/search can sort by true cost with **zero** per-request Google API calls.
- [ ] Cache layer for all geocode/place/route calls (cache表 or django-cacheops); geocode once at listing creation using the captured `place_id` (currently discarded).

**Screens (per SCREEN_SPECS.md)**
- [ ] Design system applied: new base template, tokens, CostBadge component.
- [ ] Home rework (true-cost sort, fuel ticker, stats, cost-trap callout).
- [ ] Search & Listings rebuild (max-true-cost filter, true-cost sort, pagination, map/list toggle skeleton).
- [ ] Auth rebuild (dual-role tabs, real email verification, password reset, axes rate-limit).
- [ ] Create Listing → 5-step wizard incl. place_id capture + utility fields.

**Exit criteria**: listings can be sorted/filtered by cached true cost; all addresses have place_id + coords; auth is honest and rate-limited.

---

## Phase 2 — Flagship features (Week 7–12)

- [ ] **Cost Estimator rebuild**: multi-vehicle/multi-destination (clean rebuild), transport modes (driving/transit/2-wheel/walking), traffic-aware toggle, results incl. optional **Power & Utilities** (extends `Tc = R + Tr` → `Tc = R + Tr + U`, per the paper's future work), server-side Decimal math, results persisted as `Estimate`.
- [ ] **Property Detail**: amenities proximity panel (`Places API Nearby` → hospitals/schools/markets/ATMs + AmenityScore 0–100 cached), sticky True-Cost sidebar, one-tap estimate from profile, working **Request inspection** (new `InspectionRequest` model + agent inbox).
- [ ] **True-Cost Comparison**: 2–4 properties side-by-side, best/worst highlighting, % of income benchmark, insight callouts, shareable link.
- [ ] **Saved Estimates**: history table, KPI tiles, PDF export, WhatsApp share.
- [ ] **Agent Dashboard**: listing manager with true-cost column & views, inspection inbox, listing quality tips; add property **edit/delete** views (missing today).

**Exit criteria**: a user can search → compare by true cost → run a full multi-mode estimate → save/export it; an agent can manage listings and receive inspections. This is the MVP launch bar.

---

## Phase 3 — Growth & intelligence (Week 13–20)

- [ ] **Fuel-price re-valuation**: background job re-runs saved estimates when FuelPrice changes → notification ("Your commute cost rose ₦1,900/mo").
- [ ] **Map search view** with true-cost heat coloring by area.
- [ ] **Amenity-aware recommendation**: rank search results by AmenityScore × commute fit (paper's "proximity to essential amenities" angle).
- [ ] Neighborhood guides (per-area true-cost stats — content/SEO play; Lighthouse SEO was lowest at 82).
- [ ] PWA wrapper (installable, offline shell) — mobile-first Nigeria.
- [ ] Agent subscription tiers (free N listings; paid: verified badge, analytics, boosted placement) — sustainable revenue that doesn't fight landlord economics (unlike failed rent-financing plays such as Spleet/Fibre).
- [ ] Verified listing program (agent KYC + inspection-verified photos) — attacks the #1 trust problem in Nigerian proptech.
- [ ] Blog/CMS with the published paper as anchor content.

## Phase 4 — Scale (post-launch)

- [ ] Price-intelligence dataset: aggregate anonymized true-cost data → rent benchmark API (data-as-a-service, the market's highest-margin PropTech segment).
- [ ] Mortgage/rent-financing affordability pre-check (educational only — measure fit before any lending play).
- [ ] Expansion cities beyond Ibadan/Lagos (Abuja, PH, Kano).
- [ ] Native mobile app if PWA engagement justifies it.

---

## Success metrics

| Metric | Target | Source |
|---|---|---|
| Estimates run / month | 5,000+ (from 4.9k total today) | internal |
| Users reporting ≥15% savings | 20%+ (paper baseline) | in-app survey |
| Saved-estimate → inspection conversion | ≥8% | funnel |
| Lighthouse (Perf/A11y/BP/SEO) | ≥ 90 each (paper: 83/91/96/82) | CI lighthouse job |
| Agent listings with true-cost badge | 80% | dashboard |

## Key risks

1. **Google API cost** — mitigated by aggressive caching, place_id reuse, true_cost_cache, and daily budget caps + billing alerts.
2. **Data accuracy for utilities** — power estimates are labeled as estimates with editable inputs, never asserted.
3. **Listing quality/supply** — agent onboarding + verified-badge incentive; seed with Ibadan (home turf) before Lagos.
4. **Scope creep** — ship Phase 2 bar before any Phase 3 item.
