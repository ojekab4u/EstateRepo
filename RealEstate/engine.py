"""
The estimation engine.

True cost is personal: it is computed from a user's saved trips
(place × vehicle × return-trips-per-week) applied to a specific property.

    transport = Σ over trips:
        round-trip km × trips/week × 52 × vehicle L/km × fuel price

Results are per-trip so the user can see exactly where every naira comes
from. Future components (electricity, service charges) plug in as extra
summands — the function returns a breakdown, not a single number.
"""

from decimal import Decimal, InvalidOperation

from . import geo
from .models import ProfileTrip


def _dec(value):
    return Decimal(str(value))


def _property_coords(prop):
    if prop.latitude is not None and prop.longitude is not None:
        return (prop.latitude, prop.longitude)
    address = f"{prop.address}, {prop.city}, {prop.state}, {prop.zip_code}"
    coords = geo.geocode(address)
    if coords:
        return (coords['lat'], coords['lng'])
    return None


def estimate_for_property(user, prop, fuel_price):
    """Compute the user's personal estimate for a property.

    Returns dict:
      trips: [{label, vehicle, rate, trips_per_week, km_roundtrip,
               annual_km, yearly_cost, skipped}]
      total_transport (Decimal), skipped (int)
    """
    if fuel_price is None:
        return {"trips": [], "total_transport": Decimal("0"), "skipped": 0}

    prop_coords = _property_coords(prop)
    trips = (ProfileTrip.objects.filter(user=user)
             .select_related('place', 'vehicle'))

    results = []
    total = Decimal("0")
    skipped = 0

    for trip in trips:
        base = {
            "label": trip.place.label,
            "vehicle": trip.vehicle.name,
            "rate": _dec(trip.vehicle.fuel_consumption_rate),
            "trips_per_week": trip.return_trips_per_week,
            "address": trip.place.address,
        }
        place_coords = trip.place.coords()
        if place_coords is None:
            g = geo.geocode(trip.place.address)
            place_coords = (g['lat'], g['lng']) if g else None

        if prop_coords is None or place_coords is None:
            base.update({"skipped": True, "reason": "could not resolve location"})
            skipped += 1
            results.append(base)
            continue

        km_oneway = geo.route_distance_km(prop_coords, place_coords)
        if km_oneway is None:
            base.update({"skipped": True, "reason": "no route found"})
            skipped += 1
            results.append(base)
            continue

        km_round = _dec(km_oneway) * 2
        annual_km = km_round * trip.return_trips_per_week * 52
        yearly_cost = annual_km * base["rate"] * _dec(fuel_price)
        total += yearly_cost
        base.update({
            "skipped": False,
            "km_oneway": _dec(km_oneway),
            "km_roundtrip": km_round,
            "annual_km": annual_km,
            "yearly_cost": yearly_cost,
        })
        results.append(base)

    return {"trips": results, "total_transport": total, "skipped": skipped}
