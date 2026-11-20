"""
Geo provider abstraction for ComfyHome.

Default provider is "osm" — 100% free, no API key, no billing:
  geocode       → OpenStreetMap Nominatim   (usage policy: 1 req/s, cached below)
  autocomplete  → Photon (OSM-based)        (free public instance)
  route distance→ OSRM public server        (free demo server, driving)

Switching to Google later requires only:
  - a billing-enabled Google Maps project + keys
  - GEO_PROVIDER=google in the environment
No view changes needed — everything goes through the three public functions:
  geocode(address), route_distance_km(origin, destination), autocomplete(query)

All results are cached server-side to stay far below Nominatim's
1-request-per-second usage policy and to keep responses fast.
"""

import hashlib
import time
import requests
from django.conf import settings
from django.core.cache import cache

_UA = {"User-Agent": settings.OSM_USER_AGENT}
_GEO_TTL = 60 * 60 * 24      # 24h for geocodes (addresses don't move)
_ROUTE_TTL = 60 * 60 * 12    # 12h for routes
_BIAS = {"lat": 6.5244, "lon": 3.3792}  # Lagos/Ibadan corridor bias for autocomplete


def _key(prefix, text):
    """Hashed cache key (safe chars only)."""
    return f"geo:{prefix}:{settings.GEO_PROVIDER}:{hashlib.sha1(text.lower().encode()).hexdigest()[:20]}"


# --------------------------------------------------------------------------
# Public interface
# --------------------------------------------------------------------------

def geocode(address):
    """address -> {'lat': float, 'lng': float, 'display': str} or None."""
    if not address:
        return None
    key = _key("geocode", address)
    cached = cache.get(key)
    if cached is not None:
        return cached if cached != "miss" else None
    result = _osm_geocode(address) if settings.GEO_PROVIDER == "osm" else _google_geocode(address)
    cache.set(key, result if result else "miss", _GEO_TTL)
    return result


def route_distance_km(origin, destination, mode="driving"):
    """(lat,lng) -> (lat,lng) -> one-way distance in kilometers, or None.

    mode: only "driving" is supported on the free stack today.
    """
    if not origin or not destination:
        return None
    key = _key(
        "route",
        f"{origin[0]:.5f},{origin[1]:.5f}|{destination[0]:.5f},{destination[1]:.5f}",
    )
    cached = cache.get(key)
    if cached is not None:
        return cached if cached != "miss" else None
    result = _osm_route_km(origin, destination) if settings.GEO_PROVIDER == "osm" else _google_route_km(origin, destination)
    cache.set(key, result if result else "miss", _ROUTE_TTL)
    return result


def autocomplete(query):
    """Partial address -> list of suggestion dicts."""
    if not query or len(query) < 3:
        return []
    if settings.GEO_PROVIDER == "osm":
        return _photon_autocomplete(query)
    return _google_autocomplete(query)


def provider_name():
    return settings.GEO_PROVIDER


# --------------------------------------------------------------------------
# OSM stack (default, zero-cost)
# --------------------------------------------------------------------------

def _osm_geocode(address):
    """Geocode via Nominatim, with a fallback chain that progressively
    simplifies the query — Nigerian listing addresses often contain estate
    names (e.g. 'Aboke Phase 2') that Nominatim doesn't know, but the
    street/area/city parts usually resolve."""
    parts = [p.strip() for p in address.split(",") if p.strip()]
    # candidate queries: full address, then drop leading components
    queries = [", ".join(parts[i:]) for i in range(len(parts))]
    for idx, q in enumerate(queries):
        if idx:  # Nominatim usage policy: max 1 request/second
            time.sleep(1.05)
        try:
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": q, "format": "json", "limit": 1, "countrycodes": "ng"},
                headers=_UA, timeout=10,
            )
            results = r.json()
            if results:
                first = results[0]
                return {
                    "lat": float(first["lat"]),
                    "lng": float(first["lon"]),
                    "display": first.get("display_name", ""),
                    "matched_query": q,
                }
        except (requests.RequestException, ValueError, KeyError, IndexError):
            continue
    return None


def _osm_route_km(origin, destination):
    """OSRM public server. NOTE: OSRM expects lng,lat order."""
    try:
        url = (
            "https://router.project-osrm.org/route/v1/driving/"
            f"{origin[1]:.6f},{origin[0]:.6f};{destination[1]:.6f},{destination[0]:.6f}"
            "?overview=false"
        )
        r = requests.get(url, headers=_UA, timeout=10)
        data = r.json()
        if data.get("code") == "Ok" and data.get("routes"):
            return data["routes"][0]["distance"] / 1000.0
    except (requests.RequestException, ValueError, KeyError, IndexError):
        pass
    return None


def _photon_autocomplete(query):
    try:
        r = requests.get(
            "https://photon.komoot.io/api/",
            params={"q": query, "limit": 5,
                    "lat": _BIAS["lat"], "lon": _BIAS["lon"],
                    "lang": "en"},
            headers=_UA, timeout=10,
        )
        features = r.json().get("features", [])
        out = []
        for f in features:
            p = f.get("properties", {})
            c = f.get("geometry", {}).get("coordinates", [None, None])
            label = ", ".join(
                x for x in [p.get("name"), p.get("city"), p.get("state"), p.get("country")]
                if x
            )
            if label:
                out.append({
                    "label": label,
                    "lat": c[1],
                    "lng": c[0],
                })
        return out
    except (requests.RequestException, ValueError):
        return []


# --------------------------------------------------------------------------
# Google stack (opt-in via GEO_PROVIDER=google; needs billing + keys)
# --------------------------------------------------------------------------

def _google_geocode(address):
    from . import utils as g
    result = g.get_geocode(address, settings.GOOGLE_API_KEY)
    return result  # {'lat','lng'} — display not provided by legacy wrapper


def _google_route_km(origin, destination):
    from . import utils as g
    return g.get_route_distance(origin, destination, settings.GOOGLE_API_KEY)


def _google_autocomplete(query):
    # Google-side autocomplete runs in the browser (Places JS); server-side
    # stub kept for interface parity until Phase 1 wires Places (New).
    return []
