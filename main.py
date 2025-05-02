import os
import csv
import threading
from tkinter import Text, END
from pathlib import Path
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import Meter
import requests
from apis.google_search import google_search
from apis.overpass_osm import search_osm

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")

print(f"API Key: {API_KEY}")
print(f"CSE ID: {CSE_ID}")


# Speicherort vorbereiten
DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

class SearchApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Daten-Scraper für Google & OSM")
        self.style = ttk.Style("flatly")

        input_frame = ttk.Frame(root, padding=10)
        input_frame.pack(fill=X)

        ttk.Label(input_frame, text="Suchbegriffe (kommagetrennt):").pack(anchor=W)
        self.keyword_entry = ttk.Entry(input_frame)
        self.keyword_entry.pack(fill=X, pady=5)

        ttk.Label(input_frame, text="Städte (kommagetrennt):").pack(anchor=W)
        self.city_entry = ttk.Entry(input_frame)
        self.city_entry.pack(fill=X, pady=5)

        self.complete_var = ttk.BooleanVar(value=True)
        self.complete_check = ttk.Checkbutton(input_frame, text="Nur vollständige Datensätze", variable=self.complete_var)
        self.complete_check.pack(anchor=W, pady=5)

        self.search_button = ttk.Button(input_frame, text="Suche starten", command=self.start_search)
        self.search_button.pack(pady=10)

        self.console = Text(root, height=20, wrap="word", state="disabled")
        self.console.pack(fill=BOTH, expand=True, padx=10, pady=10)

                # Fortschrittsanzeige
        self.progress = ttk.Meter(
            root,
            bootstyle="info",
            subtext="Fortschritt",
            interactive=False,
            metersize=150
        )
        self.progress.pack(pady=10)

    import time
    time.sleep(1)

    def google_search(query, api_key, cse_id):
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': cse_id,
            'q': query
        }

        response = requests.get(search_url, params=params)

        if response.status_code == 200:
            return response.json().get('items', [])
        else:
            print(f"[Google ERROR] {response.text}")
            return []

    # Sicherstellen, dass API-Key und CSE-ID nicht None sind
    if not API_KEY or not CSE_ID:
        print("Fehler: API-Key oder CSE-ID fehlt.")
    else:
        print("API-Key und CSE-ID erfolgreich geladen.")

    # Beispiel-Aufruf:
    api_key = 'DEIN_GOOGLE_API_KEY'
    cse_id = 'DEIN_CSE_ID'
    results = google_search("pizzeria kassel", api_key, cse_id)
    print(results)


    def log(self, message):
        self.console.config(state="normal")
        self.console.insert(END, f"{message}\n")
        self.console.see(END)
        self.console.config(state="disabled")

    def start_search(self):
        keywords = self.keyword_entry.get().strip()
        cities = self.city_entry.get().strip()
        only_complete = self.complete_var.get()

        if not keywords or not cities:
            self.log("❗ Bitte Suchbegriffe und Städte eingeben.")
            return

        kw_list = [k.strip() for k in keywords.split(",")]
        city_list = [c.strip() for c in cities.split(",")]

        self.log(f"🔍 Starte Suche nach {kw_list} in {city_list} (Nur vollständige: {only_complete})...")
        thread = threading.Thread(target=self.perform_search, args=(kw_list, city_list, only_complete))
        thread.start()

    def perform_search(self, keywords, cities, only_complete):
        all_results = []
        total_tasks = len(keywords) * len(cities)
        current_task = 0
        self.update_progress(0)

        for city in cities:
            for keyword in keywords:
                self.log(f"📍 Suche nach '{keyword}' in '{city}'...")

                g_results = google_search(keyword, city, log=self.log)
                self.log(f"✅ Google: {len(g_results)} Ergebnisse")

                o_results = search_osm(keyword, city, log=self.log)
                self.log(f"✅ OSM: {len(o_results)} Ergebnisse")

                combined = g_results + o_results

                if only_complete:
                    combined = [r for r in combined if r.get("name") or r.get("title")]

                all_results.extend(combined)

                # Speichern pro Suchkombination
                filename = f"{keyword}_{city.replace(' ', '_')}.csv"
                filepath = DOWNLOAD_DIR / filename
                self.save_csv(filepath, combined)
                self.log(f"💾 Gespeichert als: {filepath.name} ({len(combined)} Einträge)\n")
        current_task += 1
        progress_percent = int((current_task / total_tasks) * 100)
        self.update_progress(progress_percent)


        self.log("🎉 Alle Suchen abgeschlossen.")

    def update_progress(self, percent):
        self.progress.configure(amountused=percent)
        self.root.update_idletasks()


    def save_csv(self, filepath, data):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["source", "title", "name", "link", "snippet", "lat", "lon"])
            writer.writeheader()
            for entry in data:
                writer.writerow({
                    "source": entry.get("source"),
                    "title": entry.get("title"),
                    "name": entry.get("name"),
                    "link": entry.get("link"),
                    "snippet": entry.get("snippet"),
                    "lat": entry.get("lat"),
                    "lon": entry.get("lon")
                })

if __name__ == "__main__":
    app = ttk.Window(themename="flatly")
    SearchApp(app)
    app.mainloop()
