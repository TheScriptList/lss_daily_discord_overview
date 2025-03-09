# 🚨 Leitstellenspiel Daily Discord Overview <!-- omit from toc -->

[![Build Executable](https://github.com/TheScriptList/lss_daily_discord_overview_test/actions/workflows/build-exe.yml/badge.svg)](https://github.com/TheScriptList/lss_daily_discord_overview_test/actions/workflows/build-exe.yml) [![Docker Image CI](https://github.com/TheScriptList/lss_daily_discord_overview_test/actions/workflows/docker-image.yml/badge.svg)](https://github.com/TheScriptList/lss_daily_discord_overview_test/actions/workflows/docker-image.yml)

Dieses Skript ruft Daten von **Leitstellenspiel.de** ab und sendet eine tägliche Übersicht zu **Gebäude-Erweiterungen** und **Schulungen**, die heute fertig werden, an einen **Discord-Webhook**.\
💪 **Automatische Benachrichtigung** – Ideal für Spieler, die immer informiert bleiben wollen.\
🕒 **Geplante Ausführung** – Empfohlen als täglicher Cronjob.

## Inhaltsverzeichnis <!-- omit from toc -->

- [Roadmap](#roadmap)
- [✅ Voraussetzungen](#-voraussetzungen)
- [🛠 Installation](#-installation)
- [🚀 Nutzung](#-nutzung)
- [📅 Automatisierung per Cronjob](#-automatisierung-per-cronjob)
- [❌ Fehlerbehebung](#-fehlerbehebung)
- [📊 Beispielausgabe](#-beispielausgabe)
- [💡 Mitwirkende](#-mitwirkende)

## Roadmap

- [ ]  Benachrichtigung auf [apprise](https://github.com/caronc/apprise) umstellen.

## ✅ Voraussetzungen

🔹 **Python** ≥ 3.8 installiert ([Download](https://www.python.org/downloads/))\
🔹 **Python-Bibliotheken:** siehe `requirements.txt` ➡ Installation mit:

```sh
pip install -r requirements.txt
```

🔹 **Alternativ:** Docker-Installation ([Windows](https://docs.docker.com/desktop/setup/install/windows-install/) | [macOS](https://docs.docker.com/desktop/setup/install/mac-install/) | [Linux](https://docs.docker.com/engine/install/))
  
### Notwendige Informationen <!-- omit from toc -->

- Eine **Discord Webhook-URL**, um die Nachrichten zu senden.
- Eine **gültige  `cookies.txt` Datei**, um auf die API von Leitstellenspiel zuzugreifen.
- Deine Leitstellenspiel.de **PROFILE_ID**

## 🛠 Installation

### 1️⃣ **Discord Webhook einrichten** <!-- omit from toc -->

1. **Discord öffnen** ➡ **Servereinstellungen** ➡ **Integrationen**
2. **Webhook erstellen** ➡ **URL kopieren**

### 2️⃣ **Cookies speichern (`cookies.txt`)** <!-- omit from toc -->

1. **Mit Chrome oder Firefox Cookies exportieren:**  
   🔗 [Chrome: Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)  
   🔗 [Firefox: cookies.txt Add-on](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
2. **Auf Leitstellenspiel.de einloggen** ➡ Cookies als `cookies.txt` speichern
3. **Format:** `Netscape HTTP Cookie File` (Tab-getrennte Zeilen)

### 3️⃣ **PROFILE\_ID ermitteln** <!-- omit from toc -->

1. Herausfindbar indem man mit Rechtsklick auf seinen Nutzernamen klickt und **Link in neuem Tab öffnen** auswählt.\
  ![Schritte zur User-ID](/docs/Screenshot_Nutzername.png)
2. Die Zahl am Ende der URL ist die **PROFILE_ID** (wobei die Zahl am Ende 4- bis 7-Stellig sein sollte).\
  ![Beispiel-URL](/docs/Screenshot_ID.png)

### 4️⃣ **Konfiguration (.env-Datei)** <!-- omit from toc -->

Beim ersten Start fragt das Skript nach:

- Webhook-URL
- PROFILE_ID
- Sendeoptionen (Immer oder nur bei fertigen Einträgen)
- Discord Username für Nachrichten
- Discord Avatar

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
-e WEBHOOK_URL='https://discord.com/api/webhooks/<...>' \
-e DISCORD_USERNAME='Aram meldet aus der Leitstelle:' \
-e DISCORD_AVATAR='https://www.leitstellenspiel.de/images/logo-header.png' \
-e SEND_ALWAYS='False' \
-e PROFILE_ID='' \
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
      - "WEBHOOK_URL=https://discord.com/api/webhooks/<...>"
      - "DISCORD_USERNAME=Aram meldet aus der Leitstelle:"
      - "DISCORD_AVATAR=https://www.leitstellenspiel.de/images/logo-header.png"
      - "SEND_ALWAYS=False"
      - "PROFILE_ID="
    volumes:
      - ./cookies.txt:/app/cookies.txt:ro
```

### 🏁 **Executable-Version** <!-- omit from toc -->

Das aktuellste Release kann [hier](https://github.com/TheScriptList/lss_daily_discord_overview_test/releases/latest) gefunden werden.

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
Startdatum: 2025-02-07
Gebäude-Erweiterungen auslesen...
Überprüfe Schulungen...
==> Feuerwehr - ELW 2 Lehrgang (2025-02-07)
    --> HEUTE
==> Rettungsdienst - Rettungshundeführer (2025-02-11)
==> THW - Fachgruppe Schwere Bergung (2025-02-15)
==> Polizei - MEK (2025-02-20)
==> Polizei - SEK (2025-02-20)
Discord Nachricht senden...
✅ Nachricht erfolgreich an Discord gesendet.
```

### Webhook-Nachricht (abhängig von der Einstellung) <!-- omit from toc -->

Falls Einträge vorhanden sind:

```md
📢 Einträge für heute [07.02.2025]

🏢 Gebäude-Erweiterungen:
- THW #1: Fachgruppe Elektroversorgung (Fertig am: 07.02.2025 21:43)

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

🎓 Schulungen:
Heute keine Einträge vorhanden.
```

Falls keine Einträge vorhanden sind und die Einstellung auf immer senden steht:

```md
📢 Einträge für heute [08.02.2025]

🚫 Heute wird keine Erweiterung fertig und keine Schulung endet.
```

Falls ein Fehler im Skript auftritt (z.B. fehlende/abgelaufene Cookies), wird dieser immer an den Webhook gesendet.

## 💡 Mitwirkende

Erstellt von [L0rdEnki](https://github.com/L0rdEnki) und [MisterX2000](https://github.com/MisterX2000).
