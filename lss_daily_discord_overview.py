#!/usr/bin/env python3

import requests
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from http.cookiejar import MozillaCookieJar
from dotenv import load_dotenv, set_key
from inquirer.shortcuts import text as text_input, confirm as confirm_input, list_input
from collections import defaultdict

__version__ = "1.0.0"
__author__ = "L0rdEnki, MisterX2000"

BASE_URL = "https://www.leitstellenspiel.de"
BUILDINGS_API = BASE_URL + "/api/buildings"
SCHOOLINGS_URL = BASE_URL + "/schoolings"

CONFIG_FILE = ".env"
COOKIES_FILE = "cookies.txt"
load_dotenv(CONFIG_FILE)

# region CONFIG/UTILS
# Funktion zum Laden oder Abfragen der Konfiguration
def get_setting(name, message, confirm=False, choices=None, default=None):
    env_val = os.getenv(name)

    if env_val:
        print(f"{name} = {(str(env_val)[:77] + '...') if len(str(env_val)) > 80 else str(env_val)}")
        
        if confirm:
            env_val = env_val.lower() == "true"

        return env_val

    if confirm:
        ans = confirm_input(message=message, default=default)
    elif choices:
        ans = list_input(message=message, choices=choices, default=default)
    else:
        ans = text_input(message=message, default=default)

    set_key(CONFIG_FILE, name, str(ans))

    return ans

# Funktion zum Laden der Cookies
def load_cookies(file_path):
    cookie_jar = MozillaCookieJar()
    try:
        cookie_jar.load(file_path, ignore_discard=True, ignore_expires=True)
    except FileNotFoundError:
        send_error("Fehler: Die Datei cookies.txt wurde nicht gefunden.")
        exit(1)
    return {cookie.name: cookie.value for cookie in cookie_jar}

# Funktion zur Umwandlung von Timestamps
def format_timestamp(timestamp):
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M"), dt.date()
    except ValueError:
        return "Ungültiges Datum", None
# endregion CONFIG/UTILS

# region FETCH
# Funktion zum Abrufen der API-Daten
def get_buildings():
    cookies = load_cookies(COOKIES_FILE)
    response = requests.get(BUILDINGS_API, cookies=cookies)
    if response.status_code == 200:
        try:
            data = response.json()
            return data
        except json.JSONDecodeError:
            send_error(f"❌ Fehler: Ungültige JSON-Antwort von {BUILDINGS_API}!")
            return []
    else:
        send_error(f"❌ Fehler beim Abrufen der Daten ({BUILDINGS_API}): {response.status_code}")
        return []

def get_schoolings():
    cookies = load_cookies(COOKIES_FILE)
    response = requests.get(SCHOOLINGS_URL, cookies=cookies)
    if response.status_code != 200:
        send_error(f"❌ Fehler beim Abrufen der Daten ({SCHOOLINGS_URL}): {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    schoolings = []
    
    table_rows = soup.select("table.table-striped tbody tr")
    for row in table_rows:
        columns = row.find_all("td")
        
        lehrgang_name = columns[0].get_text(strip=True)
        enddatum_sortvalue = columns[1].get("sortvalue")
        enddatum = datetime.now() + timedelta(seconds=int(enddatum_sortvalue)) if enddatum_sortvalue else None

        lehrgangsausfuehrer = columns[2].find("a").get_text(strip=True) if columns[2].find("a") else columns[2].get_text(strip=True)
        schooling_id = columns[0].find("a")["href"].split("/")[-1]
        schooling_url = f"{BASE_URL}/schoolings/{schooling_id}"
        
        schoolings.append({
            "Lehrgang": lehrgang_name,
            "Enddatum": enddatum,
            "Lehrgangsausführer": lehrgangsausfuehrer,
            "URL": schooling_url
        })
    
    return schoolings

def get_schooling_details(schooling_url, profile_id_filter=None):
    cookies = load_cookies(COOKIES_FILE)
    response = requests.get(schooling_url, cookies=cookies)
    if response.status_code != 200:
        send_error(f"❌ Fehler beim Abrufen der Daten ({schooling_url}): {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    building_count = defaultdict(int)
    
    table_rows = soup.select("table.table-striped tbody tr")
    for row in table_rows:
        columns = row.find_all("td")
        
        profile_link = columns[2].find("a")
        profile_id = profile_link["href"].split("/")[-1] if profile_link else "Unknown"
        building = columns[3].find("a").get_text(strip=True) if columns[3].find("a") else "Unknown"
        
        if profile_id_filter is None or profile_id == profile_id_filter:
            building_count[building] += 1
    
    return dict(building_count)
# endregion FETCH

# Funktion zum Senden einer Nachricht an Discord
def send_to_discord(message, username, avatar):
    payload = {
        "username": username,
        "avatar_url": avatar,
        "content": message
    }
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print("✅ Nachricht erfolgreich an Discord gesendet.")
    else:
        print(f"❌ Fehler beim Senden an Discord: {response.status_code} - {response.text}")

# Funktion zum Senden von Fehlermeldungen an Discord
def send_error(error_message):
    print(error_message)
    send_to_discord(f"⚠️ **Fehlermeldung:**\n{error_message}", DISCORD_USERNAME, DISCORD_AVATAR)

# region MAIN
if __name__ == "__main__":
    # Einstellungen abrufen
    WEBHOOK_URL = get_setting("WEBHOOK_URL", message="Bitte Webhook-URL eingeben")
    PROFILE_ID = get_setting("PROFILE_ID", message="LSS Profil ID (leitstellenspiel.de/profile/<ID>)")
    SEND_ALWAYS = get_setting("SEND_ALWAYS", message="Soll immer eine Discord-Nachricht gesendet werden?", confirm=True)
    DISCORD_USERNAME = get_setting("DISCORD_USERNAME", message="Discord Bot Name", default="Aram meldet aus der Leitstelle:")
    DISCORD_AVATAR = get_setting("DISCORD_AVATAR", message="Discord Bot Avatar (Als URL zum Bild)", default="https://www.leitstellenspiel.de/images/logo-header.png")
    
    webhook_results = False
    # DEBUG: Um ein Zukünftiges Datum zu testen.
    today = date.today() + timedelta(days=0)
    print("Startdatum: " + str(today))
    msg = f"## 📢 Einträge für heute [{today.strftime('%d.%m.%Y')}]\n\n"

    # Gebäude-Erweiterungen auslesen
    print("Gebäude-Erweiterungen auslesen...")
    results = False
    msg += "### 🏢 Gebäude-Erweiterungen:\n"
    buildings_data = get_buildings()
    if buildings_data:
        for building in buildings_data:
            if isinstance(building, dict) and "extensions" in building:
                for extension in building["extensions"]:
                    if "available_at" in extension and extension["available_at"]:
                        formatted_date, parsed_date = format_timestamp(extension["available_at"])
                        if parsed_date == today:
                            webhook_results = True
                            results = True
                            msg += f"- {building['caption']}: {extension['caption']} (Fertig am: {formatted_date or 'Unbekannt'})\n"
    if not results:
        msg += "Heute keine Einträge vorhanden.\n"

    # Schulungen auslesen
    print("Überprüfe Schulungen...")
    results = False
    msg += "### \n🎓 Schulungen:\n"

    schoolings = get_schoolings()
    for schooling in schoolings:
        enddatum = schooling["Enddatum"].date()
        print(f"==> {schooling['Lehrgang']} ({str(enddatum)})")
        if enddatum == today:
            print("    --> HEUTE")
            webhook_results = True
            results = True
            participants = get_schooling_details(schooling['URL'], PROFILE_ID)
            msg += f"- {schooling['Lehrgang']} (Fertig am: {schooling['Enddatum'].strftime('%d.%m.%Y %H:%M')}) teilgenommen haben:\n"
            for building, count in participants.items():
                msg += f"  - {count} Person(en) aus *{building}*\n"
    if not results:
        msg += "Heute keine Einträge vorhanden.\n"

    # Nachricht für Discord vorbereiten
    if webhook_results:
        print("Discord Nachricht senden...")
        send_to_discord(msg, DISCORD_USERNAME, DISCORD_AVATAR)
    elif SEND_ALWAYS:
        # Nachricht nur senden, wenn gewünscht
        print("Discord Nachricht senden...")
        msg = f"## 📢 Einträge für heute [{today.strftime('%d.%m.%Y')}]\n\n🚫 Heute wird keine Erweiterung fertig und keine Schulung endet."
        send_to_discord(msg, DISCORD_USERNAME, DISCORD_AVATAR)

# endregion Hauptprogramm
