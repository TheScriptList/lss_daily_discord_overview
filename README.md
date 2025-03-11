# 🚨 Leitstellenspiel Daily Discord Overview <!-- omit from toc -->

[![Build Executable](https://github.com/TheScriptList/lss_daily_discord_overview/actions/workflows/build-exe.yml/badge.svg)](https://github.com/TheScriptList/lss_daily_discord_overview/actions/workflows/build-exe.yml)
[![Docker Image CI](https://github.com/TheScriptList/lss_daily_discord_overview/actions/workflows/build-docker.yml/badge.svg)](https://github.com/TheScriptList/lss_daily_discord_overview/actions/workflows/build-docker.yml)
[![GitHub Release](https://img.shields.io/github/v/release/TheScriptList/lss_daily_discord_overview?label=Latest%20Release)](https://github.com/TheScriptList/lss_daily_discord_overview/releases/latest)
[![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/TheScriptList/lss_daily_discord_overview/total?label=Total%20Downloads)](https://github.com/TheScriptList/lss_daily_discord_overview/releases)


Dieses Skript ruft Daten von **Leitstellenspiel.de** ab und sendet eine tägliche Übersicht zu **Gebäude-Erweiterungen** und **Schulungen**, die heute fertig werden, an einen **Discord-Webhook**.\
💪 **Automatische Benachrichtigung** – Ideal für Spieler, die immer informiert bleiben wollen.\
🕒 **Geplante Ausführung** – Empfohlen als täglicher Cronjob.

## Inhaltsverzeichnis <!-- omit from toc -->

- [📅 Roadmap](#-roadmap)
- [✅ Voraussetzungen](#-voraussetzungen)
- [🛠 Installation](#-installation)
- [🚀 Nutzung](#-nutzung)
- [📅 Automatisierung per Cronjob](#-automatisierung-per-cronjob)
- [❌ Fehlerbehebung](#-fehlerbehebung)
- [📊 Beispielausgabe](#-beispielausgabe)
- [💡 Mitwirkende](#-mitwirkende)

## 📅 Roadmap

- [x]  ~~Benachrichtigung auf [apprise](https://github.com/caronc/apprise) umstellen. Siehe [Issue #1](https://github.com/TheScriptList/lss_daily_discord_overview/issues/1)~~
- [x]  ~~Automatische ermittlung der `PROFILE_ID`~~
- [x]  ~~Hinzufügen der Lagerräume~~
- [x]  ~~Hinzufügen der Spezialisierungen~~

## ✅ Voraussetzungen

🔹 **Python** ≥ 3.8 installiert ([Download](https://www.python.org/downloads/))\
🔹 **Python-Bibliotheken:** siehe `requirements.txt` ➡ Installation mit:

```sh
pip install -r requirements.txt
```

🔹 **Alternativ:** Docker-Installation ([Windows](https://docs.docker.com/desktop/setup/install/windows-install/) | [macOS](https://docs.docker.com/desktop/setup/install/mac-install/) | [Linux](https://docs.docker.com/engine/install/))
  
### Notwendige Informationen <!-- omit from toc -->

- Eine **Apprise URL**, um die Nachrichten zu senden.
- Eine **gültige  `cookies.txt` Datei**, um auf die API von Leitstellenspiel zuzugreifen.

> Apprise bietet viele Schnittstellen, über die Benachrichtigungen gesendet werden können, z.B. Discord, E-Mail, Notifiarr und viele mehr (siehe Apprise [Wiki](https://github.com/caronc/apprise/wiki)).\
> In dieser Anleitung zeigen wir die beispielhafte Einrichtung für Discord.\
> Hier findet ihr die Anleitung für das Nutzen der [E-Mail Benachrichtigungen](https://github.com/caronc/apprise/wiki/Notify_email).

## 🛠 Installation

### 1️⃣ **Discord Webhook einrichten** <!-- omit from toc -->

1. **Discord öffnen** ➡ **Servereinstellungen** ➡ **Integrationen**
2. **Webhook erstellen** ➡ **URL kopieren**

### 2️⃣ **Apprise URL Einrichten** <!-- omit from toc -->

Zum Senden an Discord müssen wir diese Apprise URL für Discord anpassen `discord://<BOT-NAME>@<WebhookID>/<WebhookToken>/?avatar_url=https://www.leitstellenspiel.de/images/logo-header.png`
  
Die Discord Webhook URL, die im 1. Schritt kopiert wurde, kann z.B. so aussehen: `https://discordapp.com/api/webhooks/4174216298/JHMHI8qBe7bk2ZwO5U711o3dV_js`
  
Die Bestandteile sind wie folgt:\
`https://discordapp.com/api/webhooks/{WebhookID}/{WebhookToken}`

In diesem Beispiel ist
- die WebhookID `4174216298`
- das WebhookToken `JHMHI8qBe7bk2ZwO5U711o3dV_js`

Der `BOT-NAME` ist frei wählbar, für unser Beispiel nutzen wir `Leitstelle`.

Am Ende sollte die Apprise URL wir folgt aussehen `discord://Leitstelle@4174216298/JHMHI8qBe7bk2ZwO5U711o3dV_js/?avatar_url=https://www.leitstellenspiel.de/images/logo-header.png`

### 3️⃣ **Cookies speichern (`cookies.txt`)** <!-- omit from toc -->

1. **Mit Chrome oder Firefox Cookies exportieren:**  
   🔗 [Chrome: Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)  
   🔗 [Firefox: cookies.txt Add-on](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
2. **Auf Leitstellenspiel.de einloggen** ➡ Cookies als `cookies.txt` speichern
3. **Format:** `Netscape HTTP Cookie File` (Tab-getrennte Zeilen)

### 4️⃣ **Konfiguration (.env-Datei)** <!-- omit from toc -->

Beim ersten Start fragt das Skript nach:

- Sendeoptionen (Immer oder nur bei fertigen Einträgen, `False` oder `True`)
- Apprise URL

Falls Docker genutzt wird, müssen diese Werte im `docker run` Befehl oder der `docker-compose.yml` gesetzt werden.

## 🚀 Nutzung

### 🐍 **Python Skript starten**<!-- omit from toc -->

Das Skript wird mit folgendem Befehl gestartet:

```sh
python lss_daily_discord_overview.py
```

### 🐋 **Docker Container nutzen** <!-- omit from toc -->

Mit folgendem Befehl kann der Container gestartet werden, unter Beachtung folgender Hinweise:

- Werte, die sonst in der `.env` stehen, müssen in dem Befehl ergänzt werden
- `cookies.txt` muss im selben Verzeichnis liegen

````sh
docker run -it --rm --name lss_daily_discord_overview \
-v $PWD/cookies.txt:/app/cookies.txt:ro \
-e APPRISE_URL='discord://<BOT-NAME>@<WebhookID>/<WebhookToken>/?avatar_url=https://www.leitstellenspiel.de/images/logo-header.png' \
-e SEND_ALWAYS='False' \
ghcr.io/thescriptlist/lss_daily_discord_overview:latest
````

Alternativ als `docker-compose.yml`, unter Beachtung folgender Hinweise:

- Werte, die sonst in der `.env` stehen, müssen unter `environment` ergänzt werden
- `cookies.txt` muss im selben Verzeichnis liegen wie die `docker-compose.yml`

```yml
services:
  lss_daily_discord_overview:
    image: ghcr.io/thescriptlist/lss_daily_discord_overview:latest
    container_name: lss_daily_discord_overview
    environment:
      - "APPRISE_URL=discord://<BOT-NAME>@<WebhookID>/<WebhookToken>/?avatar_url=https://www.leitstellenspiel.de/images/logo-header.png"
      - "SEND_ALWAYS=False"
    volumes:
      - ./cookies.txt:/app/cookies.txt:ro
```

### 🏁 **Executable-Version** <!-- omit from toc -->

Das aktuellste Release kann [hier](https://github.com/TheScriptList/lss_daily_discord_overview/releases/latest) gefunden werden.

- **Windows:** `lss_daily_discord_overview-Windows_X64.exe` starten

> Falls eure Antivirensoftware die `lss_daily_discord_overview-Windows_X64.exe` als potenzielle Bedrohung einstuft, keine Sorge – das ist ein bekanntes Problem bei selbst erstellten ausführbaren Dateien. Der Code ist Open Source und kann vollständig eingesehen werden. Wenn ihr der `lss_daily_discord_overview-Windows_X64.exe` nicht traut, nutzt einfach das `lss_daily_discord_overview.py` Skript direkt.

## 📅 Automatisierung per Cronjob

📌 **Täglich um 00:01 Uhr ausführen:**

```sh
1 0 * * * cd /pfad/zum/skript && ./lss_daily_discord_overview.py
```

📌 **Mit Docker Compose:**

```sh
1 0 * * * docker compose -f /pfad/zur/docker-compose.yml up
```

> Vorausgesetzt, dass die `.env` und `cookies.txt` bereits in dem Verzeichnis vorhanden sind. Für Docker müssen die Werte aus der `.env` in der Compose Datei ergänzt werden.

## ❌ Fehlerbehebung

| Fehler                             | Lösung                                                                        |
| ---------------------------------- | ----------------------------------------------------------------------------- |
| `cookies.txt wurde nicht gefunden` | Stelle sicher, dass sich `cookies.txt` im Skript-Ordner befindet.             |
| `403 Fehler (Zugriff verweigert)`  | Prüfe, ob die Cookies korrekt gespeichert sind. Eventuell erneut exportieren. |
| `400 Fehler (Webhook)`             | Überprüfe, ob die Webhook-URL korrekt ist.                                    |

## 📊 Beispielausgabe

### Konsolenausgabe (alle Einträge) <!-- omit from toc -->

```
SEND_ALWAYS = False
APPRISE_URL = discord://Leitstelle@4174216298/JHMHI8qBe7bk2ZwO5U711o3d...
Ermittelte Profil ID: 12345
Startdatum: 2025-02-07
Gebäude-Erweiterungen auslesen...
Lagerräume-Erweiterungen auslesen...
Spezialisierungen auslesen...
Überprüfe Schulungen...
==> Feuerwehr - ELW 2 Lehrgang (2025-02-07)
    --> HEUTE
==> Rettungsdienst - Rettungshundeführer (2025-02-11)
==> THW - Fachgruppe Schwere Bergung (2025-02-15)
==> Polizei - MEK (2025-02-20)
==> Polizei - SEK (2025-02-20)
Nachricht senden...
```

### Webhook-Nachricht (abhängig von der Einstellung) <!-- omit from toc -->

Falls Einträge vorhanden sind:

```md
📢 Einträge für heute [07.02.2025]

🏢 Gebäude-Erweiterungen:
- THW #1: Fachgruppe Elektroversorgung (Fertig am: 07.02.2025 21:43)

📦 Lagerräume:
- Feuerwache Potsdam: Lagerraum (Fertig am: 07.02.2025 17:13)

🔧 Spezialisierungen:
- Feuerwache Berlin: Werkfeuerwehr-Spezialisierung (Fertig am: 07.02.2025 17:14)

🎓 Schulungen:
- Feuerwehr - ELW 2 Lehrgang (Fertig am: 07.02.2025 21:30) teilgenommen haben:
  - 6 Person(en) aus Feuerwache Berlin
  - 1 Person(en) aus Feuerwache Potsdam
```

Falls nur in einem der beiden Teile Einträge vorhanden sind:

```md
📢 Einträge für heute [07.02.2025]

🏢 Gebäude-Erweiterungen:
- THW #1: Fachgruppe Elektroversorgung (Fertig am: 07.02.2025 21:43)

📦 Lagerräume:
Heute keine Einträge vorhanden.

🔧 Spezialisierungen:
Heute keine Einträge vorhanden.

🎓 Schulungen:
Heute keine Einträge vorhanden.
```

Falls keine Einträge vorhanden sind und die Einstellung `SEND_ALWAYS = True` ist:

```md
📢 Einträge für heute [08.02.2025]

🚫 Heute wird keine Erweiterung fertig und keine Schulung endet.
```

Falls ein Fehler im Skript auftritt (z.B. fehlende/abgelaufene Cookies), wird dieser immer an den Webhook gesendet.

## 💡 Mitwirkende

Erstellt von [L0rdEnki](https://github.com/L0rdEnki) und [MisterX2000](https://github.com/MisterX2000).
