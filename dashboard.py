"""Data logic: filters the pre-aggregated Anekal BMTC data (no Streamlit code here)."""
import json
import math
from pathlib import Path

_BASE = Path(__file__).parent
_PATH = _BASE / "data" / "anekal.json"
if not _PATH.exists():  # also works when anekal.json sits next to this file
    _PATH = _BASE / "anekal.json"
D = json.loads(_PATH.read_text(encoding="utf-8"))

LEVELS = ["High (200+)", "Medium (50-199)", "Low (10-49)", "Very low (<10)"]
ZONES = [("a", "All areas"), ("0", "Anekal town (within 4 km)"), ("1", "Wider area (4-12 km)")]
BANDS = [("a", "All day"), ("0", "Morning rush (7-10am)"), ("1", "Evening rush (5-8pm)"),
         ("2", "Midday and quiet hours"), ("3", "Night (9pm-5am)")]
DEST = ["Majestic bus station" if x == "Kempegowda Bus Station" else
        "Anekal (returning buses)" if x == "Anekal (inbound)" else x for x in D["d"]]


def band_of(h):
    return 0 if 7 <= h <= 10 else 1 if 17 <= h <= 20 else 3 if (h >= 21 or h < 5) else 2


def route_label(i):
    n = (D["rl"][i].replace("Anekal ⇔ ", "").replace(" ⇔ Anekal", "")
         .replace("Kempegowda Bus Station", "Majestic").replace("Bommasandra Metro Station", "Bommasandra Metro")
         .replace(" Bus Station", "").replace(" Bus Stand", "").replace(" (Kalasipalya)", "").replace(" (Old)", ""))
    return f"{n} ({D['r'][i]})"


ROUTES = [("a", "All routes")] + [(str(i), route_label(i)) for i in range(12)]


def build(zone="a", band="a", route="a"):
    zo = lambda v: zone == "a" or int(zone) == v
    bo = lambda v: band == "a" or int(band) == v
    ro = lambda v: route == "a" or int(route) == v
    hours = [0] * 24
    per_route = {}
    for z, r, h, n in D["h"]:
        if zo(z) and ro(r) and bo(band_of(h)):
            hours[h] += n
            per_route[r] = per_route.get(r, 0) + n
    trips = sum(hours)
    stops_list = [q for q in D["s"] if zo(q[4]) and (route == "a" or (q[5] >> int(route)) & 1)]
    if route == "a":
        stops = sum(D["st"]) if zone == "a" else D["st"][int(zone)]
    else:
        stops = len(stops_list)
    routes = sum(1 for k in per_route if k < 12)
    if per_route.get(12):
        routes += sum(D["on"]) if zone == "a" else D["on"][int(zone)]
    top = sorted(((route_label(k), n) for k, n in per_route.items() if k < 12), key=lambda x: -x[1])[:8]
    dd = {}
    for z, r, b, d, n in D["b"]:
        if zo(z) and ro(r) and bo(b):
            dd[d] = dd.get(d, 0) + n
    scatter = [{"km": round(min(12, math.hypot((q[0] / 1e4 + 12.6 - 12.7094) * 111.2,
                                               (q[1] / 1e4 + 77.6 - 77.6964) * 108.6)), 2),
                "trips": q[2], "level": LEVELS[q[3]]} for q in stops_list]
    levels = [(name, sum(1 for q in D["s"] if q[4] == 0 and q[3] == i)) for i, name in enumerate(LEVELS)]
    peak = max(range(24), key=lambda h: hours[h])
    h12 = f"{peak % 12 or 12}{'am' if peak < 12 else 'pm'}"
    summary = (f"This selection has {trips:,} bus trips a day across {stops} stops. "
               f"The busiest hour is {h12}, with {hours[peak]} trips.") if trips else "No trips match this selection."
    return {"stops": stops, "routes": routes, "trips": trips, "hours": hours, "top_routes": top,
            "destinations": [(DEST[d], n) for d, n in dd.items()], "scatter": scatter,
            "levels": levels, "summary": summary}


DISTANCE_BANDS = [("0-1 km", 142), ("1-2 km", 5), ("2-4 km", 62), ("4-8 km", 6), ("8-12 km", 22)]
