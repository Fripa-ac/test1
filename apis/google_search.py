import os
import time
import random
import requests
from urllib.parse import quote_plus

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

BASE_URL = "https://www.googleapis.com/customsearch/v1"

def google_search(query, city, max_results=50, log=None):
    results = []
    total_fetched = 0
    start = 1

    while total_fetched < max_results:
        try:
            q = f"{query} in {city}"
            params = {
                "key": GOOGLE_API_KEY,
                "cx": GOOGLE_CSE_ID,
                "q": q,
                "start": start,
                "num": 10
            }
            response = requests.get(BASE_URL, params=params)
            data = response.json()

            if "items" in data:
                for item in data["items"]:
                    results.append({
                        "source": "Google",
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet"),
                        "displayLink": item.get("displayLink"),
                        "full_data": item
                    })

            if "error" in data:
                if log:
                    log(f"[Google ERROR] {data['error']['message']}")
                break

            total_fetched += 10
            start += 10

            time.sleep(random.uniform(1.5, 2.5))  # Respect rate limit

        except Exception as e:
            if log:
                log(f"[Google ERROR] {e}")
            break

    return results
