#!/usr/bin/env python3

import requests
import json
import os
import logging
import apprise
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from http.cookiejar import MozillaCookieJar
from dotenv import load_dotenv, set_key
from inquirer.shortcuts import text as text_input, confirm as confirm_input, list_input
from collections import defaultdict

# Modul Infos
__version__ = "2.1.0"
__author__ = "L0rdEnki, MisterX2000"

# Konst Variablen
BASE_URL = "https://www.leitstellenspiel.de"
USERINFO_API = BASE_URL + "/api/userinfo"
BUILDINGS_API = BASE_URL + "/api/buildings"
SCHOOLINGS_URL = BASE_URL + "/schoolings"

CONFIG_FILE = ".env"
COOKIES_FILE = "cookies.txt"

# Objekte Initialisieren
log = logging.getLogger(__name__)
appr = apprise.Apprise()

# region CONFIG/UTILS
# Funktion zum Laden oder Abfragen der Konfiguration
def get_setting(name, message, confirm=False, choices=None, default=None):
    env_val = os.getenv(name)

    if env_val:
        log.info(f"{name} = {(str(env_val)[:77] + '...') if len(str(env_val)) > 80 else str(env_val)}")
        
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
        send_error("cookies.txt nicht gefunden")
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
def get_response(URL):
    response = requests.get(URL, cookies=COOKIES)
    if response.status_code != 200:
        send_error(f"Fehler beim Abrufen der Daten ({URL}): {response.status_code}")
    return response

def get_profileID():
    response = get_response(USERINFO_API)
    try:
        data = response.json()
        return data.get("user_id")
    except json.JSONDecodeError:
        send_error(f"Ungültige JSON-Antwort von {USERINFO_API}")

def get_buildings():
    response = get_response(BUILDINGS_API)
    try:
        data = response.json()
        return data
    except json.JSONDecodeError:
        send_error(f"Ungültige JSON-Antwort von {BUILDINGS_API}")

def get_schoolings():
    response = get_response(SCHOOLINGS_URL)
    
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
    response = get_response(schooling_url)
    
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

# Funktion zum Senden von Fehlermeldungen
def send_error(error_message):
    log.error(error_message)
    appr.notify(body=error_message, title='⚠️ ERROR', notify_type=apprise.NotifyType.FAILURE)
    exit(1)

# region MAIN
if __name__ == "__main__":    
    # Einstellungen aus der Environment laden
    load_dotenv(CONFIG_FILE)

    # Logging einrichten
    logging.basicConfig(
        level=os.getenv("LOGGING_LEVEL", "INFO"),
        format="%(asctime)s %(name)-8s %(levelname)-8s %(message)s")
    log.info("v" + str(__version__))

    # Einstellungen abfragen
    SEND_ALWAYS = get_setting("SEND_ALWAYS", message="Soll immer eine Nachricht gesendet werden?", confirm=True)
    APPRISE_URL = get_setting("APPRISE_URL", message="Apprise URL [Siehe README]")
    appr.add(APPRISE_URL)

    # Weitere Daten laden
    COOKIES = load_cookies(COOKIES_FILE)
    PROFILE_ID = get_profileID()
    log.info("Ermittelte Profil ID: " + str(PROFILE_ID))

    webhook_results = False
    # DEBUG: Um ein Zukünftiges Datum zu testen.
    # PowerShell: $env:DEBUG_DAYS=3; python lss_daily_discord_overview.py
    today = date.today() + timedelta(days=int(os.getenv("DEBUG_DAYS", 0)))
    log.info("Startdatum: " + str(today))
    msg = f"## 📢 Einträge für heute [{today.strftime('%d.%m.%Y')}]\n"

    # Gebäude-Erweiterungen auslesen
    log.info("Gebäude-Erweiterungen auslesen...")
    results = False
    msg += "\n### 🏢 Gebäude-Erweiterungen:\n\n"
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

    # Lagerräume (Storage Upgrades) auslesen
    log.info("Lagerräume-Erweiterungen auslesen...")
    results = False
    msg += "\n### 📦 Lagerräume:\n\n"

    if buildings_data:
        for building in buildings_data:
            if isinstance(building, dict) and "storage_upgrades" in building:
                for storage in building["storage_upgrades"]:
                    if "available_at" in storage and storage["available_at"]:
                        formatted_date, parsed_date = format_timestamp(storage["available_at"])
                        if parsed_date == today:
                            webhook_results = True
                            results = True
                            msg += f"- {building['caption']}: {storage['upgrade_type']} (Fertig am: {formatted_date or 'Unbekannt'})\n"

    if not results:
        msg += "Heute keine Einträge vorhanden.\n"

    # Spezialisierungen auslesen
    log.info("Spezialisierungen auslesen...")
    results = False
    msg += "\n### 🔧 Spezialisierungen:\n\n"

    if buildings_data:
        for building in buildings_data:
            if isinstance(building, dict) and "specialization" in building:
                specialization = building["specialization"]
                if "available_at" in specialization and specialization["available_at"]:
                    formatted_date, parsed_date = format_timestamp(specialization["available_at"])
                    if parsed_date == today:
                        webhook_results = True
                        results = True
                        msg += f"- {building['caption']}: {specialization['caption']} (Fertig am: {formatted_date or 'Unbekannt'})\n"

    if not results:
        msg += "Heute keine Einträge vorhanden.\n"

    # Schulungen auslesen
    log.info("Überprüfe Schulungen...")
    results = False
    msg += "\n### 🎓 Schulungen:\n\n"

    schoolings = get_schoolings()
    for schooling in schoolings:
        enddatum = schooling["Enddatum"].date()
        log.info(f"==> {schooling['Lehrgang']} ({str(enddatum)})")
        if enddatum == today:
            log.info("    --> HEUTE")
            webhook_results = True
            results = True
            participants = get_schooling_details(schooling['URL'], PROFILE_ID)
            msg += f"- {schooling['Lehrgang']} (Fertig am: {schooling['Enddatum'].strftime('%d.%m.%Y %H:%M')}) teilgenommen haben:\n"
            for building, count in participants.items():
                msg += f"  - {count} Person(en) aus *{building}*\n"
    if not results:
        msg += "Heute keine Einträge vorhanden.\n"

    # Nachricht vorbereiten und senden
    if webhook_results:
        log.info("Nachricht senden...")
        appr.notify(body=msg, body_format=apprise.NotifyFormat.MARKDOWN)
    elif SEND_ALWAYS:
        # Nachricht nur senden, wenn gewünscht
        log.info("Nachricht senden...")
        msg = f"## 📢 Einträge für heute [{today.strftime('%d.%m.%Y')}]\n\n🚫 Heute wird keine Erweiterung fertig und keine Schulung endet."
        appr.notify(body=msg, body_format=apprise.NotifyFormat.MARKDOWN)

# endregion Hauptprogramm
