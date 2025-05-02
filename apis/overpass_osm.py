import time
import random
import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def build_overpass_query(keyword, lat, lon, radius=20000):
    return f"""
    [out:json][timeout:30];
    (
      node["name"~"{keyword}", i](around:{radius},{lat},{lon});
      way["name"~"{keyword}", i](around:{radius},{lat},{lon});
      relation["name"~"{keyword}", i](around:{radius},{lat},{lon});
    );
    out center;
    """

def geocode_city(city_name):
    try:
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            "q": city_name,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "Custom-Search-Script"
        }
        res = requests.get(url, params=params, headers=headers)
        res.raise_for_status()
        data = res.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None, None

def search_osm(keyword, city, log=None):
    lat, lon = geocode_city(city)
    if not lat or not lon:
        if log:
            log(f"[OSM] Konnte '{city}' nicht geokodieren.")
        return []

    query = build_overpass_query(keyword, lat, lon)
    results = []

    try:
        res = requests.post(OVERPASS_URL, data=query, headers={"User-Agent": "Custom-Script"})
        res.raise_for_status()
        data = res.json()

        for element in data.get("elements", []):
            tags = element.get("tags", {})
            results.append({
                "source": "OSM",
                "id": element.get("id"),
                "type": element.get("type"),
                "lat": element.get("lat") or element.get("center", {}).get("lat"),
                "lon": element.get("lon") or element.get("center", {}).get("lon"),
                "name": tags.get("name"),
                "full_data": tags
            })

        time.sleep(random.uniform(1.5, 3.0))  # Overpass rate-limiting

    except Exception as e:
        if log:
            log(f"[OSM ERROR] {e}")

    return results
