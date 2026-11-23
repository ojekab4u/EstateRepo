# Commute Profile & Estimation Engine — Design Proposal

> Status: PROPOSAL — awaiting approval before the data-model rework.
> This is the platform's core strength, so the model is designed for the
> complexity you described: multiple places, a different vehicle per place,
> household vehicles, and future cost components (electricity etc.).

## 1. Research findings (what mature tools do)

| Source | What it confirms |
|---|---|
| **CNT Housing + Transportation (H+T) Affordability Index** (htaindex.cnt.org) | Transportation cost = auto ownership + auto use + transit use, each modeled separately then priced per unit. Affordability benchmark: housing ≤30% + transport ≤15% of income = **45% combined**. Uses a "regional typical household" for *place-level* estimates — exactly why our per-property cached figure must be labeled "typical household", never personal. |
| **Argonne National Lab "aTravel" tool** (afleet.esia.anl.gov/atravel) | Trip-based input: "Click Add Trip → round trip? → frequency per day/week/month → start & destination." **Confirms the Places × Vehicle × Frequency model.** |
| **ChoiceCalc commute methodology** | Driving cost = fuel + maintenance + repairs + tires + vehicle wear + parking + tolls (+ commute-class insurance). Fuel alone understates the real per-km cost. |
| **SuburbCost (AU)** | Uses the national **ATO per-km running rate** (≈₦ equivalent of $0.91/km) × return trips × weeks — a validated "full running cost" shortcut instead of itemizing. |
| **waocalculator** | Trip rows: one-way distance × 2 = round trip; frequency per day/week; fuel economy + price; optional parking/maintenance; ride-sharing splits cost across occupants. |

**Conclusion:** the industry-standard shape is exactly what you described —
**a list of regular trips, each with its own vehicle and weekly frequency** —
plus an optional "full running cost per km" mode so our numbers aren't
fuel-only (fuel is typically only ~half of real running cost).

## 2. Proposed data model

```
ProfileVehicle   (per user)          ProfilePlace (per user)
├─ name                              ├─ label ("Work", "Market, Church…")
├─ fuel_rate_l_per_km                ├─ address
├─ fuel_type (petrol/diesel/CNG)     └─ lat/lng (geocoded once, cached)
└─ is_default

ProfileTrip (the heart — one row per regular journey)
├─ user (owner)
├─ place      → ProfilePlace
├─ vehicle    → ProfileVehicle
├─ return_trips_per_week  (one visit = go & come back)
└─ notes (optional)

EstimateProfile (existing) keeps: fuel price override, household size (future)
```

### Why this shape handles every case you raised

| Case you described | How the model handles it |
|---|---|
| Multiple usual places (not just "main destination") | Each place is a `ProfilePlace`; estimate = sum over all trips |
| **A different vehicle for a different place** | Each `ProfileTrip` binds place → vehicle (car to work, bike to market) |
| Household: me + wife relocating, 2 vehicles | Two vehicles exist; the same destination can have **two trips** splitting the weekly visits (e.g. car 6/wk + her car 2/wk) — no special-casing needed |
| Remove / adjust a vehicle | Full CRUD (built today). Deleting a vehicle referenced by trips → **soft-block**: "Reassign or remove 3 trips that use this vehicle first" (no silent breakage) |
| Electricity & future factors | Estimate = Σ component costs; today transport, tomorrow `electricity` component with its own inputs on the profile |

### Estimation flow (per property)

```
for trip in user.trips:
    km_round  = distance(property, trip.place) × 2        (cached by OD pair)
    annual_km = km_round × trip.return_trips_per_week × 52
    cost     += annual_km × trip.vehicle.fuel_rate × fuel_price(trip.vehicle.fuel_type)
true_cost = rent + cost (+ electricity later)
```

### Two honesty upgrades to adopt with this model

1. **Fuel-only vs full running cost toggle** — fuel-only is what we compute today.
   Option B: a Nigerian-calibrated per-km running rate (like SuburbCost's ATO
   rate) covering maintenance/tyres/depreciation. Label the result clearly:
   "fuel only" or "full running cost". This makes estimates *defensible*, not
   just bigger.
2. **Saved estimates are snapshots** — already true (HistoricalData stores the
   profile JSON), so editing your profile never silently changes past numbers.
   Keep this, and show the snapshot inputs on the estimate detail.

## 3. UX shape (once approved)

- Profile page = tabs: **Trips** (the list — place, vehicle, visits/week, add/edit/remove) · Vehicles · Fuel & household · Saved estimates
- Adding a trip: place autocomplete (Photon, free) + vehicle dropdown + visits/week stepper
- Estimator page: shows your trip list pre-filled → "Estimate this home for me" → results broken down **per trip**, grouped per vehicle, with the household story visible
- Comparison (next phase): same trips, different homes → one column per home, your life as the constant

## 4. Challenges you didn't mention (flagging now)

1. **Fuel-only understates true cost** — decide whether to adopt the full-running-cost mode above (recommend: yes, as a clearly-labeled option).
2. **Users don't know L/km** — solved today with presets; consider letting users pick "km per litre" instead (common in Nigeria: "my car does 12 km/L") and convert internally.
3. **Fuel type per vehicle** — diesel/CNG vehicles will price differently (model ready).
4. **Transit/okada routes** — mode field on ProfileTrip is future-proofed; needs Google billing or local fare tables (danfo fares are actually knowable — could be a rule-based fallback).
5. **Place geocode failures** — rural/estate addresses; fallback to area-level coords already exists; show a "resolved to area" notice when precision drops.
6. **Traffic/time cost** — H+T counts money only; time cost is a future differentiator (Google duration in traffic later).
7. **Rent instalments** (60/40 culture) — cash-flow display, not just annual totals.
8. **Comparison consistency** — all compared homes must use the *same* trip snapshot, else the comparison lies.
