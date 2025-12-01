#!/usr/bin/env python3

import requests
import json
import os
import logging
import apprise
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
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
def parse_iso_epoch(timestamp):
    """Return unix epoch integer (seconds) from an ISO timestamp string or None."""
    dt = parse_iso_datetime(timestamp)
    return int(dt.timestamp()) if dt else None

def parse_iso_datetime(timestamp):
    """Parse an ISO timestamp string into a datetime, return None if parsing fails."""
    if not timestamp:
        return None
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        # Normalize to timezone-aware UTC
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None
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
    
    soup = BeautifulSoup(response.text, "html.parser")
    schoolings = []
    
    table_rows = soup.select("table.table-striped tbody tr")
    for row in table_rows:
        columns = row.find_all("td")
        
        lehrgang_name = columns[0].get_text(strip=True)
        enddatum_sortvalue = columns[1].get("sortvalue")
        # Use timezone-aware datetime in UTC and then store as unix epoch
        end_dt = datetime.now(timezone.utc) + timedelta(seconds=int(enddatum_sortvalue)) if enddatum_sortvalue else None
        end_epoch = int(end_dt.timestamp()) if end_dt else None

        lehrgangsausfuehrer = columns[2].find("a").get_text(strip=True) if columns[2].find("a") else columns[2].get_text(strip=True)
        schooling_id = columns[0].find("a")["href"].split("/")[-1]
        schooling_url = f"{BASE_URL}/schoolings/{schooling_id}"
        
        schoolings.append({
            "Lehrgang": lehrgang_name,
            "Enddatum": end_epoch,
            "Lehrgangsausführer": lehrgangsausfuehrer,
            "URL": schooling_url
        })
    
    return schoolings

def get_schooling_details(schooling_url, profile_id_filter=None):
    response = get_response(schooling_url)
    
    soup = BeautifulSoup(response.text, "html.parser")
    building_count = defaultdict(int)
    
    table_rows = soup.select("table.table-striped tbody tr")
    for row in table_rows:
        columns = row.find_all("td")
        
        profile_link = columns[2].find("a")
        profile_id = profile_link["href"].split("/")[-1] if profile_link else "Unknown"
        building = columns[3].find("a").get_text(strip=True) if columns[3].find("a") else "Unknown"

        if profile_id_filter is None or int(profile_id) == int(profile_id_filter):
            building_count[building] += 1
    
    return dict(building_count)
# endregion FETCH

# Funktion zum Senden von Fehlermeldungen
def send_error(error_message):
    log.error(error_message)
    appr.notify(body=error_message, title="⚠️ ERROR", notify_type=apprise.NotifyType.FAILURE)
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
    # Compute `today` in UTC to align with parsed timezone-aware timestamps
    today_dt = datetime.now(timezone.utc) + timedelta(days=int(os.getenv("DEBUG_DAYS", 0)))
    today_start_dt = datetime(today_dt.year, today_dt.month, today_dt.day, tzinfo=timezone.utc)
    tomorrow_start_dt = today_start_dt + timedelta(days=1)
    today_start_epoch = int(today_start_dt.timestamp())
    tomorrow_start_epoch = int(tomorrow_start_dt.timestamp())
    log.info("Startdatum: " + str(today_start_dt.date()))
    msg = f"## 📢 Einträge für heute [<t:{today_start_epoch}:d>]\n"

    # Gebäude-Erweiterungen auslesen
    log.info("Gebäude-Erweiterungen auslesen...")
    results = False
    msg += "\n### 🏢 Gebäude-Erweiterungen:\n\n"
    buildings_data = get_buildings()

    # Split buildings_data
    if buildings_data:
        extensions_list = [(building, ext) for building in buildings_data if isinstance(building, dict) for ext in building.get("extensions", [])]
        storage_upgrades_list = [(building, st) for building in buildings_data if isinstance(building, dict) for st in building.get("storage_upgrades", [])]
        specialization_list = [(building, building["specialization"]) for building in buildings_data if isinstance(building, dict) and "specialization" in building]
    else:
        extensions_list = []
        storage_upgrades_list = []
        specialization_list = []

    if extensions_list:
        extensions_list.sort(key=lambda be: parse_iso_epoch(be[1].get("available_at")) or float('inf'))
        for building, extension in extensions_list:
            if "available_at" in extension and extension["available_at"]:
                epoch = parse_iso_epoch(extension["available_at"])
                if epoch is not None and epoch >= today_start_epoch and epoch < tomorrow_start_epoch:
                    webhook_results = True
                    results = True
                    msg += f"- {building['caption']}: {extension['caption']} (Fertig am: <t:{epoch}:f> <t:{epoch}:R>)\n"
    if not results:
        msg += "Heute keine Einträge vorhanden.\n"

    # Lagerräume (Storage Upgrades) auslesen
    log.info("Lagerräume-Erweiterungen auslesen...")
    results = False
    msg += "\n### 📦 Lagerräume:\n\n"

    if storage_upgrades_list:
        storage_upgrades_list.sort(key=lambda bs: parse_iso_epoch(bs[1].get("available_at")) or float('inf'))
        for building, storage in storage_upgrades_list:
            if "available_at" in storage and storage["available_at"]:
                epoch = parse_iso_epoch(storage["available_at"])
                if epoch is not None and epoch >= today_start_epoch and epoch < tomorrow_start_epoch:
                    webhook_results = True
                    results = True
                    msg += f"- {building['caption']}: {storage['upgrade_type']} (Fertig am: <t:{epoch}:f> <t:{epoch}:R>)\n"
    if not results:
        msg += "Heute keine Einträge vorhanden.\n"

    # Spezialisierungen auslesen
    log.info("Spezialisierungen auslesen...")
    results = False
    msg += "\n### 🔧 Spezialisierungen:\n\n"

    if specialization_list:
        specialization_list.sort(key=lambda bs: parse_iso_epoch(bs[1].get("available_at")) or float('inf'))
        for building, specialization in specialization_list:
            if "available_at" in specialization and specialization["available_at"]:
                epoch = parse_iso_epoch(specialization["available_at"])
                if epoch is not None and epoch >= today_start_epoch and epoch < tomorrow_start_epoch:
                    webhook_results = True
                    results = True
                    msg += f"- {building['caption']}: {specialization['caption']} (Fertig am: <t:{epoch}:f> <t:{epoch}:R>)\n"
    if not results:
        msg += "Heute keine Einträge vorhanden.\n"

    # Schulungen auslesen
    log.info("Überprüfe Schulungen...")
    results = False
    msg += "\n### 🎓 Schulungen:\n\n"

    schoolings = get_schoolings()
    # Sort schoolings by end date ascending (earliest first)
    if isinstance(schoolings, list):
            schoolings.sort(key=lambda s: (s.get("Enddatum") or float('inf')))
    for schooling in schoolings:
        epoch = schooling.get("Enddatum")
        log.info(f"==> {schooling['Lehrgang']}")
        if epoch is not None and epoch >= today_start_epoch and epoch < tomorrow_start_epoch:
            log.info("    --> HEUTE")
            webhook_results = True
            results = True
            participants = get_schooling_details(schooling["URL"], PROFILE_ID)
            msg += f"- {schooling['Lehrgang']} (Fertig am: <t:{epoch}:f> <t:{epoch}:R>) teilgenommen haben:\n"
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
        msg = f"## 📢 Einträge für heute [<t:{today_start_epoch}:d>]\n\n🚫 Heute wird keine Erweiterung fertig und keine Schulung endet."
        appr.notify(body=msg, body_format=apprise.NotifyFormat.MARKDOWN)

# endregion Hauptprogramm
