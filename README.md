<h1 align="center">JADON</h1>
<p align="center"><i>Schnell · Schlicht · Dein</i></p>
<p align="center">
  Ein schlanker, schöner Desktop-Browser – gebaut mit Python und Qt.<br>
  <b>Kein Electron.</b>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.9%2B-blue">
  <img alt="Qt" src="https://img.shields.io/badge/Qt-PyQt6-41cd52">
  <img alt="Lizenz" src="https://img.shields.io/badge/Lizenz-MIT-green">
  <img alt="Plattformen" src="https://img.shields.io/badge/Windows%20%7C%20macOS%20%7C%20Linux-lightgrey">
</p>

---

## Was ist Jadon?

Jadon ist ein minimalistischer Webbrowser mit dunklem Design, Tabs und einer kombinierten
Adress- und Suchleiste. Der gesamte Code steckt in **einer einzigen Datei** (`jadon.py`) und
ist dadurch leicht zu lesen, zu verändern und zu erweitern.

### Warum nicht Electron?

Electron-Apps bringen eine komplette Node.js-Laufzeit und eine eigene Chromium-Kopie mit.
Jadon ist eine **native Qt-Anwendung**: Die Oberfläche besteht aus echten Qt-Widgets, die
Webseiten werden über das Modul *Qt WebEngine* dargestellt. Das bedeutet:

- kein Node.js, kein JavaScript-Framework, kein `package.json`
- die Oberfläche ist nativ und läuft in Python
- kleiner und übersichtlicher Quellcode

> Hinweis: Qt WebEngine basiert intern auf Chromium. Jadon verwendet also dieselbe
> Rendering-Engine wie Chrome, aber ohne Electron.

## Funktionen

**Wie ein normaler Browser:**

- Tabs (Mittelklick schließt), Favicons, mehrere Fenster und **privates Fenster** (nichts wird gespeichert)
- Adressleiste, die auch als Suchfeld dient (Standard: DuckDuckGo)
- Zurück, Vor, Neu laden/Stopp, Startseite, Ladebalken
- Lesezeichen (★) und Verlauf
- Suche auf der Seite (`Strg + F`), Zoom, Vollbild
- Drucken und „Als PDF speichern"
- Downloads mit Speichern-Dialog und Benachrichtigung
- Entwicklertools (`F12`)
- Integrierter PDF-Viewer
- Cookies, Logins und Berechtigungen bleiben erhalten
- Popups, `target="_blank"` und Login-Fenster (OAuth) öffnen als Tab
- `mailto:`, `tel:` und andere Protokolle werden an das Betriebssystem übergeben
- HTTP-Anmeldung, JavaScript-Dialoge, Datei-Upload, Drag & Drop

**Echtzeit-Kommunikation (WebRTC):**

- Videoanrufe und Telefonie im Browser (z. B. Jitsi, Google Meet, Discord Web)
- **Mikrofon** und **Kamera** mit Berechtigungsabfrage
- **Bildschirmfreigabe** mit Auswahl von Bildschirm oder Fenster
- Benachrichtigungen, Standort, Zwischenablage, Vollbild-Videos

## Installation

Voraussetzung: **Python 3.9 oder neuer** und **PyQt6 6.8 oder neuer** mit PyQt6-WebEngine (wird mit `requirements.txt` installiert).

```bash
git clone https://github.com/DEIN-NAME/jadon.git
cd jadon

# optional, aber empfohlen: virtuelle Umgebung
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python jadon.py
```

Du kannst auch direkt Adressen übergeben:

```bash
python jadon.py https://example.com
```

### Windows: Start ohne `.exe` (z. B. bei Smart App Control)

Smart App Control blockiert unsignierte Programme wie die mit PyInstaller gebaute `Jadon.exe`.
Mit **`Jadon-starten.bat`** (Doppelklick) läuft Jadon stattdessen über das installierte Python – dafür ist
keine `.exe` nötig. Beim ersten Start richtet die Datei automatisch eine Umgebung ein und installiert
die Abhängigkeiten. Voraussetzung ist ein installiertes Python (<https://www.python.org/downloads/>, beim Setup
„Add python.exe to PATH“ ankreuzen). Für eine Desktop-Verknüpfung: Rechtsklick auf die Datei →
*Senden an → Desktop (Verknüpfung erstellen)*.

## Tastenkürzel

| Kürzel                  | Aktion                  |
|-------------------------|-------------------------|
| `Strg + T`              | Neuer Tab               |
| `Strg + W`              | Tab schließen           |
| `Strg + L`              | Adressleiste fokussieren|
| `Strg + R` / `F5`       | Neu laden               |
| `Alt + ←` / `Alt + →`   | Zurück / Vor            |
| `Strg + Tab`            | Nächster Tab            |
| `Strg + Shift + Tab`    | Vorheriger Tab          |
| `Strg + +` / `Strg + -` | Zoom vergrößern/verkleinern |
| `Strg + 0`              | Zoom zurücksetzen       |
| `Strg + N`              | Neues Fenster           |
| `Strg + Shift + N`      | Privates Fenster        |
| `Strg + D`              | Lesezeichen setzen/entfernen |
| `Strg + F`              | Auf Seite suchen        |
| `Strg + P`              | Drucken                 |
| `F12`                   | Entwicklertools         |
| `F11`                   | Vollbild                |

Auf macOS entspricht `Strg` der Taste `Cmd`.

## Anrufe, Mikrofon, Kamera und Bildschirmfreigabe

Wenn eine Seite Mikrofon oder Kamera möchte, fragt Jadon dich. Die Entscheidung wird gespeichert.
Bei der Bildschirmfreigabe öffnet sich ein Fenster, in dem du Bildschirm oder Fenster auswählst.

Je nach Betriebssystem musst du zusätzlich etwas freigeben:

| System  | Hinweis |
|---------|---------|
| Windows | Unter *Einstellungen → Datenschutz* Mikrofon und Kamera für Desktop-Apps erlauben. |
| macOS   | Mikrofon, Kamera und **Bildschirmaufnahme** für das Terminal (oder Python) unter *Systemeinstellungen → Datenschutz & Sicherheit* erlauben. |
| Linux   | Bildschirmfreigabe unter Wayland braucht PipeWire und `xdg-desktop-portal` (Jadon aktiviert die nötige Chromium-Funktion automatisch). |

Zum Ausprobieren eignen sich zum Beispiel <https://meet.jit.si> (Anruf, Mikrofon, Kamera,
Bildschirm) oder <https://webcamtests.com> / <https://mictests.com>.

### Was bei der Bildschirmfreigabe mitgeteilt wird

| Was                          | Windows | macOS | Linux |
|------------------------------|:-------:|:-----:|:-----:|
| Bild (Bildschirm / Fenster)  | ja      | ja    | ja (Wayland: PipeWire nötig) |
| Systemton                    | ja, nur bei „Gesamter Bildschirm“ | nein | nein |
| Mauszeiger                   | ja      | ja    | ja    |

Der Systemton wird nur übertragen, wenn die Seite ihn anfordert (z. B. beim Haken „Audio teilen“
in Meet oder Discord). Dein **Mikrofon** ist davon getrennt und wird in der Anruf-Seite selbst gewählt.
Jadon verhindert außerdem, dass Chromium den Stream drosselt, wenn das Fenster verdeckt oder
minimiert ist.

### Fehlersuche unter Windows 11 (Freunde sehen nichts oder ein schwarzes Bild)

Öffne in Jadon das Menü **⋯ → Bildschirm-/Mikrofon-Diagnose**, klicke auf *Bildschirm teilen* und wähle
*Gesamter Bildschirm*. Rechts siehst du „So kommt es bei Freunden an“ – das ist ein lokaler Sendetest
über dieselbe Technik, die Discord benutzt.

| Ergebnis in der Diagnose | Bedeutung / Lösung |
|--------------------------|--------------------|
| Beide Vorschauen zeigen deinen Bildschirm | Jadon ist in Ordnung. Das Problem liegt in Discord (Kanal, Stream-Einstellungen, Seite neu laden mit `Strg + Shift + R`). |
| Vorschau **schwarz** | Meist ein Grafikkarten-Problem. Siehe unten. |
| Fehler `NotAllowedError` / Dialog erscheint nicht | Auswahlfenster abgebrochen oder abgelehnt. Erneut versuchen und „Teilen“ klicken. |
| Links Bild, rechts nichts / „KEIN Bild übertragen“ | Videocodec-Problem. Bitte den Text aus dem Protokoll als Issue melden. |

**Schwarzes Bild beheben:**

1. *Einstellungen → System → Bildschirm → Grafik*: `python.exe` (oder `Jadon.exe`) hinzufügen →
   *Optionen* → **Energiesparen** wählen, damit Jadon auf derselben GPU läuft wie dein Bildschirm (typisch bei Laptops mit zwei Grafikkarten).
2. Teile den **gesamten Bildschirm** statt einzelner Fenster.
3. Starte Jadon testweise ohne GPU-Beschleunigung:
   ```powershell
   $env:QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu"
   python jadon.py
   ```

### Discord im Browser (discord.com/app)

So teilst du mit möglichst vollständiger Übertragung:

1. Tritt einem Sprachkanal bei und klicke auf **Bildschirm**.
2. Wähle in Jadon den Reiter **Gesamter Bildschirm** (nicht „Fenster").
   Fenster-Aufnahmen sind bei manchen Programmen schwarz, und Systemton gibt es nur beim ganzen Bildschirm.
3. Schalte in Discords Stream-Fenster **Audio** ein (nur Windows).
4. Dein Mikrofon wählst du in Discord unter *Einstellungen → Sprache & Video*.

Grenzen der Web-Version (liegen an Discord, nicht an Jadon): Es gibt keine automatische Spiele-Erkennung,
keinen separaten Spiele-Ton, und hohe Auflösungen/Bildraten (z. B. 1080p60) brauchen Nitro.
Wer das volle Discord-Erlebnis braucht, nutzt dafür die Desktop-App von Discord.

## Twitch, YouTube & Co. („Fehler #4000“)

Twitch und YouTube-Livestreams nutzen **H.264 und AAC**. Diese Codecs sind in den **PySide6**-Paketen
nicht enthalten – dort erscheint bei Twitch „Das Video ist nicht verfügbar oder wird in diesem Browser nicht
unterstützt (Fehler #4000)“. Jadon nutzt deshalb **PyQt6** (`requirements.txt`), sofern es installiert ist:

```bash
pip uninstall -y PySide6 PySide6-Addons PySide6-Essentials shiboken6
pip install -r requirements.txt
python jadon.py
```

Prüfen kannst du es im Menü **⋯ → Bildschirm-/Mikrofon-Diagnose**: Dort steht oben, welche Codecs
(H.264, AAC, VP9, AV1, Opus) verfügbar sind. Steht bei „H.264“ ein ✘, ist die Engine ohne diese Codecs gebaut.

**Lizenz-Hinweis:** PyQt6 steht unter GPLv3. Gibst du Jadon-Programme weiter (z. B. über GitHub-Releases),
müssen sie unter den Bedingungen der GPLv3 bereitgestellt werden – der offene Quellcode im Repository erfüllt das.
Für H.264/AAC können außerdem Patentlizenzen relevant sein. Wer das vermeiden will, nutzt
`requirements-pyside6.txt` (ohne H.264/AAC).

## Bekannte Grenzen

- **DRM-Streaming** (Netflix, Disney+, Prime Video in HD) braucht das Widevine-Modul, das Qt
  nicht mitliefert. Es kann funktionieren, wenn Google Chrome installiert ist und du den Pfad
  per `QTWEBENGINE_CHROMIUM_FLAGS="--widevine-path=..."` angibst.
- Es gibt keine Erweiterungen (Chrome-Web-Store) und keine Passwort-Synchronisierung.
- Einige Dienste (z. B. Google Meet) melden sich mit der Qt-Engine unterschiedlich gut. Jadon gibt sich
  deshalb als Chrome aus; sollte etwas nicht gehen, bitte ein Issue mit Seite und Fehlermeldung öffnen.

## Aufbau des Codes

| Teil                  | Aufgabe                                                           |
|-----------------------|-------------------------------------------------------------------|
| `START_PAGE`          | HTML der Startseite                                               |
| `STYLE`               | Qt-Stylesheet (Farben, Tabs, Menüs, Dialoge)                      |
| `configure_profile()` | Chromium-Einstellungen: WebRTC, Screen-Capture, Clipboard, Downloads |
| `Page` / `WebView`    | Web-Ansicht: Popups, Vollbild, externe Protokolle                 |
| `Jadon`               | Hauptfenster: Tabs, Menü, Lesezeichen, Verlauf, Suche, Druck      |
| `Jadon.on_permission` | Abfrage für Mikrofon, Kamera, Standort, Benachrichtigungen        |
| `Jadon.on_desktop_media` | Auswahldialog für die Bildschirmfreigabe                       |

Lesezeichen und Verlauf liegen als JSON-Dateien im Ordner `~/.jadon/`.

### Design anpassen

Alle Farben stehen im `STYLE`-Block. Der Akzent ist Violett (`#a78bfa`) mit Cyan (`#6ee7f9`).
Ersetze diese Werte, um Jadon in deiner eigenen Farbe zu gestalten. Die Suchmaschine änderst du
über die Konstante `SEARCH_URL` (und das `action`-Attribut in `START_PAGE`).

## Als eigenständige App bauen

### Automatisch über GitHub Actions

Die Datei `.github/workflows/build.yml` baut Jadon bei jedem Push auf `main` für **Windows, macOS
und Linux** und legt die Programme als Download unter *Actions → Lauf auswählen → Artifacts* ab.

Für ein offizielles Release setzt du einen Tag:

```bash
git tag v1.0.0
git push --tags
```

Danach erscheinen unter *Releases* automatisch `Jadon-windows-x64.zip`, `Jadon-macos-arm64.zip`
und `Jadon-linux-x64.tar.gz`. Der Build lässt sich auch manuell über *Actions → Build Jadon → Run workflow* starten.

Hinweise zu den fertigen Paketen:

- **Windows:** `Jadon.exe` im entpackten Ordner starten. SmartScreen warnt bei unsignierten Programmen („Weitere Informationen → Trotzdem ausführen").
- **macOS:** Die App ist nur ad-hoc signiert. Beim ersten Start per Rechtsklick auf *Öffnen* bestätigen. Mikrofon und Kamera fragt macOS dann normal ab.
- **Linux:** Archiv entpacken und `./Jadon/Jadon` starten.

### Lokal bauen

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name Jadon jadon.py
```

Das Ergebnis liegt danach im Ordner `dist/`.

## Sicherheit

Hat Windows-Sicherheit bei der `.exe` angeschlagen? Das passiert bei mit PyInstaller gebauten
Programmen häufig (False Positive). Wie du Downloads per Prüfsumme und Herkunftsnachweis
verifizierst, was du bei einem Alarm tun kannst und wie Jadon selbst geschützt ist, steht in
[SECURITY.md](SECURITY.md).

## Roadmap

- [x] Lesezeichen und Verlauf
- [x] Suche auf der Seite
- [x] Privater Modus
- [x] Mikrofon, Kamera, Bildschirmfreigabe
- [ ] Downloads-Übersicht mit Fortschritt
- [ ] Einstellungsseite (Suchmaschine, Startseite)
- [ ] Rechtschreibprüfung
- [ ] Hell-/Dunkel-Umschaltung

Beiträge sind willkommen: Fork erstellen, Branch anlegen, Pull Request öffnen.

## Lizenz

MIT – siehe [LICENSE](LICENSE).
