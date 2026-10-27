#!/usr/bin/env python3
"""
Jadon – ein schneller, schöner Desktop-Browser.
Gebaut mit Python + Qt (PyQt6, alternativ PySide6). Kein Electron.

Start:
    pip install -r requirements.txt
    python jadon.py [url ...]
"""
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote_plus

# Chromium-Flags müssen gesetzt werden, bevor Qt startet.
_flags = [
    # Beim Teilen ist das Jadon-Fenster oft verdeckt oder minimiert. Ohne diese Flags drosselt Chromium
    # Hintergrund-Seiten, und Anrufe/Streams können ruckeln oder einfrieren.
    "--disable-renderer-backgrounding",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    # Videos (TikTok, Reels, Shorts ...) dürfen ohne Klick starten, auch in eingebetteten Frames.
    "--autoplay-policy=no-user-gesture-required",
]
if sys.platform.startswith("win"):
    _flags.append("--disable-features=CalculateNativeWinOcclusion")
if sys.platform.startswith("linux"):
    _flags.append("--enable-features=WebRTCPipeWireCapturer")  # Bildschirmfreigabe unter Wayland
if _flags:
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "") + " " + " ".join(_flags)
    ).strip()

# PyQt6 wird bevorzugt: Dessen Qt-WebEngine-Pakete spielen H.264/AAC ab (Twitch, YouTube-Livestreams ...).
# Die PySide6-Pakete enthalten diese Codecs nicht (Twitch zeigt dann „Fehler #4000“).
try:
    from PyQt6.QtCore import QCoreApplication, QLocale, QStandardPaths, QStringListModel, Qt, QTimer, QUrl
    from PyQt6.QtGui import (
        QAction, QBrush, QColor, QDesktopServices, QFont, QIcon, QKeySequence,
        QLinearGradient, QPainter, QPixmap, QShortcut,
    )
    from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
    from PyQt6.QtWebEngineCore import (
        QWebEngineDownloadRequest, QWebEnginePage, QWebEngineProfile, QWebEngineScript,
        QWebEngineSettings,
        QWebEngineUrlRequestInterceptor,
    )
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWidgets import (
        QApplication, QCheckBox, QComboBox, QCompleter, QDialog, QDialogButtonBox, QFileDialog,
        QFormLayout, QHBoxLayout,
        QLabel, QLineEdit, QListView, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox,
        QProgressBar, QPushButton,
        QStackedWidget, QSystemTrayIcon, QTabBar, QTabWidget, QToolButton, QVBoxLayout, QWidget,
    )
    BINDING = "PyQt6"
except ImportError:
    from PySide6.QtCore import QCoreApplication, QLocale, QStandardPaths, QStringListModel, Qt, QTimer, QUrl
    from PySide6.QtGui import (
        QAction, QBrush, QColor, QDesktopServices, QFont, QIcon, QKeySequence,
        QLinearGradient, QPainter, QPixmap, QShortcut,
    )
    from PySide6.QtPrintSupport import QPrintDialog, QPrinter
    from PySide6.QtWebEngineCore import (
        QWebEngineDownloadRequest, QWebEnginePage, QWebEngineProfile, QWebEngineScript,
        QWebEngineSettings,
        QWebEngineUrlRequestInterceptor,
    )
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import (
        QApplication, QCheckBox, QComboBox, QCompleter, QDialog, QDialogButtonBox, QFileDialog,
        QFormLayout, QHBoxLayout,
        QLabel, QLineEdit, QListView, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox,
        QProgressBar, QPushButton,
        QStackedWidget, QSystemTrayIcon, QTabBar, QTabWidget, QToolButton, QVBoxLayout, QWidget,
    )
    BINDING = "PySide6"

APP_NAME = "Jadon"
SEARCH_ENGINES = {
    "DuckDuckGo": "https://duckduckgo.com/?q={}",
    "Google": "https://www.google.com/search?q={}",
    "Bing": "https://www.bing.com/search?q={}",
    "Brave": "https://search.brave.com/search?q={}",
    "Ecosia": "https://www.ecosia.org/search?q={}",
    "Startpage": "https://www.startpage.com/do/search?q={}",
}
START_HOST = "jadon.local"
DATA_DIR = Path.home() / ".jadon"
BOOKMARKS_FILE = DATA_DIR / "bookmarks.json"
HISTORY_FILE = DATA_DIR / "history.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

START_PAGE = """
<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Neuer Tab</title>
<style>
  *{box-sizing:border-box}
  html,body{height:100%;margin:0}
  body{display:flex;flex-direction:column;align-items:center;justify-content:center;
       font-family:'Segoe UI',system-ui,-apple-system,sans-serif;color:#e9e7f5;
       background:radial-gradient(1200px 700px at 20% 10%,#2a1f55 0%,transparent 60%),
                  radial-gradient(900px 600px at 85% 90%,#0f3b5c 0%,transparent 60%),#12111a;}
  h1{font-size:76px;font-weight:200;letter-spacing:.35em;margin:0 0 6px .35em;
     background:linear-gradient(90deg,#b69cff,#6ee7f9);-webkit-background-clip:text;
     background-clip:text;color:transparent}
  p{margin:0 0 36px;opacity:.55;letter-spacing:.2em;font-size:13px;text-transform:uppercase}
  form{width:min(620px,86vw)}
  input{width:100%;padding:17px 26px;font-size:17px;color:#fff;border-radius:999px;
        border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.07);
        outline:none;transition:.2s}
  input:focus{border-color:#a78bfa;box-shadow:0 0 0 4px rgba(167,139,250,.25);
              background:rgba(255,255,255,.1)}
  input::placeholder{color:rgba(255,255,255,.4)}
</style></head><body>
  <h1>JADON</h1><p>Schnell · Schlicht · Dein</p>
  <form id="f">
    <input name="q" placeholder="Suchen oder Adresse eingeben …" autofocus autocomplete="off">
  </form>
  <script>
    var SEARCH = {{SEARCH}};
    document.getElementById("f").addEventListener("submit", function (e) {
      e.preventDefault();
      var q = this.q.value.trim();
      if (q) location.href = SEARCH.replace("{}", encodeURIComponent(q));
    });
  </script>
</body></html>
"""

TEST_PAGE = r"""
<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Jadon – Diagnose</title>
<style>
  body{margin:0;padding:32px;font-family:'Segoe UI',system-ui,sans-serif;color:#e9e7f5;background:#12111a;line-height:1.5}
  h1{font-weight:300;letter-spacing:.2em;margin:0 0 4px} h2{font-weight:500;margin:0 0 10px}
  .muted{opacity:.55;font-size:13px;word-break:break-all}
  section{background:#1d1c28;border:1px solid #34324a;border-radius:14px;padding:20px;margin:20px 0;max-width:980px}
  button{background:#7c5cf0;color:#fff;border:0;border-radius:10px;padding:9px 18px;font-size:14px;cursor:pointer;margin:0 6px 8px 0}
  button.g{background:#34324a} button:hover{filter:brightness(1.15)}
  video{width:100%;max-width:460px;background:#000;border-radius:10px;display:block}
  .row{display:flex;gap:18px;flex-wrap:wrap} .row>div{flex:1;min-width:280px}
  pre{background:#16151f;border-radius:10px;padding:12px;font-size:12.5px;white-space:pre-wrap;min-height:40px;margin:10px 0 0}
  .meter{height:10px;background:#16151f;border-radius:6px;overflow:hidden;margin:8px 0;max-width:460px}
  .meter i{display:block;height:100%;width:0;background:linear-gradient(90deg,#a78bfa,#6ee7f9)}
  label{margin-right:12px}
</style></head><body>
<h1>JADON · DIAGNOSE</h1>
<div class="muted" id="env"></div>
<div class="muted">Qt-Bindung: {{BINDING}}</div>

<section>
  <h2>Video-Codecs (Twitch, YouTube-Livestreams …)</h2>
  <pre id="codecs"></pre>
</section>

<section>
  <h2>Browser-Kennung (TikTok &amp; Co.)</h2>
  <pre id="ident"></pre>
</section>

<section>
  <h2>Bildschirmfreigabe</h2>
  <label><input type="checkbox" id="aud"> Systemton anfordern</label><br><br>
  <button id="shareBtn">Bildschirm teilen</button><button class="g" id="stopBtn">Stopp</button>
  <div class="row">
    <div><div class="muted">Dein Bildschirm (Vorschau)</div><video id="vLocal" autoplay muted playsinline></video></div>
    <div><div class="muted">So kommt es bei Freunden an (lokaler Sendetest)</div><video id="vRemote" autoplay muted playsinline></video></div>
  </div>
  <pre id="log1">Noch nichts getestet.</pre>
</section>

<section>
  <h2>Mikrofon &amp; Kamera</h2>
  <button id="micBtn">Mikrofon testen</button><button id="camBtn">Kamera testen</button>
  <div class="meter"><i id="lvl"></i></div>
  <video id="vCam" autoplay muted playsinline></video>
  <pre id="log2">Noch nichts getestet.</pre>
</section>

<script>
const $ = id => document.getElementById(id);
const out = (el, m) => { el.textContent += m + "\n"; };
$("env").textContent = navigator.userAgent;
(function () {
  const v = document.createElement("video");
  const tests = {
    "H.264 (Video)": 'video/mp4; codecs="avc1.42E01E"',
    "AAC (Audio)": 'audio/mp4; codecs="mp4a.40.2"',
    "VP9": 'video/webm; codecs="vp9"',
    "AV1": 'video/mp4; codecs="av01.0.05M.08"',
    "Opus": 'audio/webm; codecs="opus"'
  };
  let txt = "", h264 = false;
  for (const k in tests) {
    const ok = v.canPlayType(tests[k]) !== "";
    if (k.startsWith("H.264")) h264 = ok;
    txt += (ok ? "✔ " : "✘ ") + k + "\n";
  }
  if (!h264) txt += "\nH.264 fehlt: Twitch zeigt „Fehler #4000“. Starte Jadon mit PyQt6 (siehe README).";
  $("codecs").textContent = txt;
})();
(function () {
  const u = navigator.userAgentData;
  const ms = window.MediaSource;
  let t = "User-Agent: " + navigator.userAgent + "\n";
  t += "Client-Hints-Marken: " + (u ? u.brands.map(b => b.brand + " " + b.version).join(", ") : "nicht vorhanden") + "\n";
  t += "window.chrome: " + (window.chrome ? "vorhanden" : "FEHLT") + "\n";
  t += "navigator.webdriver: " + navigator.webdriver + "\n";
  t += "MSE H.264 + AAC: " + (ms && ms.isTypeSupported('video/mp4; codecs="avc1.42E01E, mp4a.40.2"') ? "ja" : "NEIN") + "\n";
  $("ident").textContent = t;
})();
let stream = null, pcA = null, pcB = null;

function stopShare() {
  if (stream) stream.getTracks().forEach(t => t.stop());
  if (pcA) pcA.close(); if (pcB) pcB.close();
  stream = pcA = pcB = null;
  $("vLocal").srcObject = null; $("vRemote").srcObject = null;
}

async function loopback(s) {
  pcA = new RTCPeerConnection(); pcB = new RTCPeerConnection();
  pcA.onicecandidate = e => e.candidate && pcB.addIceCandidate(e.candidate);
  pcB.onicecandidate = e => e.candidate && pcA.addIceCandidate(e.candidate);
  pcB.ontrack = e => { $("vRemote").srcObject = e.streams[0]; };
  pcA.onconnectionstatechange = () => out($("log1"), "Verbindung: " + pcA.connectionState);
  s.getTracks().forEach(t => pcA.addTrack(t, s));
  const offer = await pcA.createOffer();
  await pcA.setLocalDescription(offer); await pcB.setRemoteDescription(offer);
  const answer = await pcB.createAnswer();
  await pcB.setLocalDescription(answer); await pcA.setRemoteDescription(answer);
  setTimeout(async () => {
    if (!pcA) return;
    const stats = await pcA.getStats();
    let found = false;
    stats.forEach(r => {
      if (r.type === "outbound-rtp" && r.kind === "video") {
        found = true;
        out($("log1"), "Gesendet: " + r.bytesSent + " Bytes, " + (r.frameWidth || "?") + "x" + (r.frameHeight || "?") +
          (r.bytesSent > 0 ? "  → OK, es wird Bild übertragen." : "  → es wird KEIN Bild übertragen!"));
      }
    });
    if (!found) out($("log1"), "Keine Video-Statistik gefunden.");
  }, 3000);
}

$("shareBtn").onclick = async () => {
  stopShare(); $("log1").textContent = "";
  try {
    stream = await navigator.mediaDevices.getDisplayMedia({ video: { frameRate: 30 }, audio: $("aud").checked });
    $("vLocal").srcObject = stream;
    stream.getTracks().forEach(t => {
      out($("log1"), t.kind + ": " + t.label + " " + JSON.stringify(t.getSettings()));
      t.onended = () => out($("log1"), t.kind + "-Spur beendet");
    });
    if ($("aud").checked && stream.getAudioTracks().length === 0)
      out($("log1"), "Hinweis: Es ist kein Systemton im Stream (bei Windows nur mit „Gesamter Bildschirm“).");
    await loopback(stream);
  } catch (e) {
    out($("log1"), "Fehler: " + e.name + " – " + e.message);
  }
};
$("stopBtn").onclick = stopShare;

$("micBtn").onclick = async () => {
  $("log2").textContent = "";
  try {
    const s = await navigator.mediaDevices.getUserMedia({ audio: true });
    out($("log2"), "Mikrofon: " + s.getAudioTracks()[0].label + " – sprich etwas, der Balken sollte ausschlagen.");
    const ctx = new AudioContext(), an = ctx.createAnalyser(), data = new Uint8Array(an.fftSize);
    ctx.createMediaStreamSource(s).connect(an);
    (function tick() {
      an.getByteTimeDomainData(data);
      let peak = 0; for (const v of data) peak = Math.max(peak, Math.abs(v - 128));
      $("lvl").style.width = Math.min(100, peak * 2.2) + "%";
      requestAnimationFrame(tick);
    })();
  } catch (e) { out($("log2"), "Fehler: " + e.name + " – " + e.message); }
};
$("camBtn").onclick = async () => {
  try {
    const s = await navigator.mediaDevices.getUserMedia({ video: true });
    $("vCam").srcObject = s;
    out($("log2"), "Kamera: " + s.getVideoTracks()[0].label);
  } catch (e) { out($("log2"), "Fehler: " + e.name + " – " + e.message); }
};
</script></body></html>
"""

STYLE = """
QMainWindow, QWidget#root { background:#16151f; }
QTabBar { background:#16151f; }
QTabBar::tab {
    background:transparent; color:#9d9bb5; padding:9px 16px; margin:6px 2px 0 2px;
    border-top-left-radius:10px; border-top-right-radius:10px; min-width:110px; max-width:220px;
}
QTabBar::tab:selected { background:#23222f; color:#f1efff; }
QTabBar::tab:hover:!selected { background:#1d1c28; color:#d6d4ee; }
QWidget#bar, QWidget#find { background:#23222f; }
QToolButton {
    background:transparent; color:#cfcde6; border:0; border-radius:8px;
    font-size:17px; padding:5px 10px; min-width:20px;
}
QToolButton:hover { background:#34324a; color:#fff; }
QToolButton:disabled { color:#5a5870; }
QToolButton::menu-indicator { image:none; }
QLineEdit {
    background:#16151f; color:#f1efff; border:1px solid #34324a; border-radius:15px;
    padding:7px 16px; font-size:14px; selection-background-color:#7c5cf0;
}
QLineEdit:focus { border:1px solid #a78bfa; }
QProgressBar { background:#23222f; border:0; max-height:2px; min-height:2px; }
QProgressBar::chunk { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #a78bfa,stop:1 #6ee7f9); }
QDialog, QMessageBox { background:#1d1c28; }
QLabel { color:#f1efff; }
QPushButton {
    background:#34324a; color:#f1efff; border:0; border-radius:8px; padding:8px 18px; min-width:70px;
}
QPushButton:hover { background:#46436a; }
QPushButton:default { background:#7c5cf0; }
QListView { background:#16151f; color:#f1efff; border:1px solid #34324a; border-radius:8px; padding:4px; }
QListView::item { padding:8px; border-radius:6px; }
QListView::item:selected { background:#7c5cf0; color:#fff; }
QMenu { background:#23222f; color:#e9e7f5; border:1px solid #34324a; padding:6px; }
QMenu::item { padding:7px 28px 7px 18px; border-radius:6px; }
QMenu::item:selected { background:#34324a; }
QMenu::separator { height:1px; background:#34324a; margin:5px 8px; }
QCheckBox { color:#f1efff; }
QComboBox { background:#16151f; color:#f1efff; border:1px solid #34324a; border-radius:8px; padding:6px 12px; }
QComboBox QAbstractItemView { background:#23222f; color:#f1efff; selection-background-color:#7c5cf0; }
QToolTip { background:#23222f; color:#f1efff; border:1px solid #34324a; }
"""

# ----------------------------------------------------------------------------
# Hilfsfunktionen
# ----------------------------------------------------------------------------
TRAY = {"icon": None, "last_note": None}


def add_action(menu, text, fn):
    """Menüeintrag, der mit PyQt6 und PySide6 gleich funktioniert."""
    act = QAction(text, menu)
    act.triggered.connect(fn)
    menu.addAction(act)
    return act


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, data):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(DATA_DIR, 0o700)  # nur der eigene Benutzer (Linux/macOS)
        except OSError:
            pass
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass


DEFAULT_SETTINGS = {"search_engine": "DuckDuckGo", "homepage": "", "ask_download": False,
                    "chrome_version": ""}  # leer = Version der eingebauten Engine; z. B. "130" überschreibt sie
SETTINGS = dict(DEFAULT_SETTINGS)


def load_settings():
    data = load_json(SETTINGS_FILE, {})
    if isinstance(data, dict):
        SETTINGS.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS})
    if SETTINGS["search_engine"] not in SEARCH_ENGINES:
        SETTINGS["search_engine"] = DEFAULT_SETTINGS["search_engine"]


def search_url():
    return SEARCH_ENGINES.get(SETTINGS["search_engine"], SEARCH_ENGINES["DuckDuckGo"])


def resolve_input(text):
    """Adressleisten-Eingabe -> URL oder Suche. Adressen ohne Schema werden mit https:// geöffnet."""
    text = text.strip()
    has_scheme = re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", text)
    looks_like_url = (
        has_scheme
        or text.startswith(("localhost", "about:", "view-source:"))
        or (" " not in text and ("." in text or ":" in text))
    )
    if not looks_like_url:
        return QUrl(search_url().replace("{}", quote_plus(text)))
    if has_scheme or text.startswith(("about:", "view-source:")):
        return QUrl.fromUserInput(text)
    host = re.split(r"[/:?#]", text, maxsplit=1)[0].lower()
    local = host == "localhost" or host.endswith(".local") or re.fullmatch(r"[\d.]+", host)
    return QUrl.fromUserInput(text if local else "https://" + text)


def make_icon():
    pm = QPixmap(256, 256)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    g = QLinearGradient(0, 0, 256, 256)
    g.setColorAt(0, QColor("#a78bfa"))
    g.setColorAt(1, QColor("#6ee7f9"))
    p.setBrush(QBrush(g))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(8, 8, 240, 240, 60, 60)
    p.setPen(QColor("#12111a"))
    font = QFont("Segoe UI", 140)
    font.setWeight(QFont.Weight.DemiBold)
    p.setFont(font)
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "J")
    p.end()
    return QIcon(pm)


def notify(title, message):
    tray = TRAY["icon"]
    if tray is not None:
        tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 6000)


RISKY_EXTENSIONS = {
    ".exe", ".msi", ".bat", ".cmd", ".com", ".scr", ".ps1", ".vbs", ".vbe", ".js", ".jse",
    ".wsf", ".hta", ".jar", ".lnk", ".dll", ".reg", ".cpl", ".msix", ".appx", ".pif",
}


DOWNLOADS = []


def unique_path(directory, name):
    base, ext = os.path.splitext(name)
    path = os.path.join(directory, name)
    n = 1
    while os.path.exists(path):
        path = os.path.join(directory, f"{base} ({n}){ext}")
        n += 1
    return path


def _download_done(dl):
    try:
        if dl.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            notify("Download abgeschlossen", dl.downloadFileName())
    except RuntimeError:
        pass


def on_download(dl):
    name = dl.downloadFileName()
    if os.path.splitext(name)[1].lower() in RISKY_EXTENSIONS:
        answer = QMessageBox.warning(
            QApplication.activeWindow(), "Download-Warnung",
            f"„{name}“ ist ein ausführbares Programm bzw. Skript.\n"
            "Solche Dateien können deinen Computer beschädigen. Lade sie nur von Quellen herunter, denen du vertraust.\n\n"
            "Trotzdem herunterladen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            dl.cancel()
            return
    if SETTINGS.get("ask_download"):
        path, _ = QFileDialog.getSaveFileName(QApplication.activeWindow(), "Datei speichern", name)
        if not path:
            dl.cancel()
            return
    else:
        folder = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation) or str(Path.home())
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError:
            pass
        path = unique_path(folder, name)
    dl.setDownloadDirectory(os.path.dirname(path))
    dl.setDownloadFileName(os.path.basename(path))
    DOWNLOADS.append(dl)
    dl.isFinishedChanged.connect(lambda d=dl: _download_done(d))
    dl.accept()
    notify("Download gestartet", os.path.basename(path))


def on_notification(note):
    note.show()
    TRAY["last_note"] = note
    notify(note.title(), note.message())


# TikTok & Co. prüfen nicht nur den User-Agent, sondern auch die „Client Hints“ (Sec-CH-UA bzw.
# navigator.userAgentData) und ob `window.chrome` existiert. Qt WebEngine meldet dort nur „Chromium“
# und kein „Google Chrome“ – das sieht für die Seiten nach einem eingebetteten Browser aus, und sie
# zeigen dann „Browser wird nicht unterstützt“, Verifizierungsschleifen oder spielen keine Videos ab.
# Dieses Skript läuft vor jeder Seite und macht die Angaben so, wie sie ein normaler Chrome liefert.
# Google lehnt die Anmeldung in eingebetteten Chromium-Browsern oft ab („Dieser Browser ist möglicherweise
# nicht sicher“). Mit einer Firefox-Kennung werden die Login-Seiten dagegen akzeptiert (Trick u. a. von
# qutebrowser). Das gilt NUR für die Anmelde-Hosts; Meet, YouTube, WhatsApp, Discord usw. bleiben „Chrome“.
GOOGLE_LOGIN_HOSTS = {"accounts.google.com", "accounts.youtube.com"}
FIREFOX_VERSION = "140.0"


def firefox_user_agent():
    if sys.platform.startswith("win"):
        os_part = "Windows NT 10.0; Win64; x64"
    elif sys.platform == "darwin":
        os_part = "Macintosh; Intel Mac OS X 10.15"
    else:
        os_part = "X11; Linux x86_64"
    return f"Mozilla/5.0 ({os_part}; rv:{FIREFOX_VERSION}) Gecko/20100101 Firefox/{FIREFOX_VERSION}"


FIREFOX_UA = firefox_user_agent()

COMPAT_JS = r"""
(function () {
  try {
    var host = location.hostname;
    if (host === "accounts.google.com" || host === "accounts.youtube.com") {
      // Login-Seiten: auch per JavaScript wie Firefox auftreten (passend zum HTTP-Header).
      var ua = "__FIREFOX_UA__";
      var nav = Object.getPrototypeOf(navigator);
      var def = function (k, v) {
        try {
          Object.defineProperty(nav, k, { get: function () { return v; }, configurable: true, enumerable: true });
        } catch (e) {}
      };
      def("userAgent", ua);
      def("appVersion", "5.0 (" + ua.substring(ua.indexOf("(") + 1, ua.indexOf(";")) + ")");
      def("vendor", "");
      def("productSub", "20100101");
      def("userAgentData", undefined);
      try { delete window.chrome; } catch (e) {}
      return;
    }
    var major = "__CHROME_MAJOR__", full = major + ".0.0.0";
    var brands = function () { return [
      { brand: "Not)A;Brand", version: "8" },
      { brand: "Chromium", version: major },
      { brand: "Google Chrome", version: major }
    ]; };
    var fullBrands = function () { return [
      { brand: "Not)A;Brand", version: "8.0.0.0" },
      { brand: "Chromium", version: full },
      { brand: "Google Chrome", version: full }
    ]; };
    var uad = navigator.userAgentData;
    if (uad) {
      var has = false;
      for (var i = 0; i < uad.brands.length; i++) {
        if (uad.brands[i].brand === "Google Chrome") has = true;
      }
      if (!has) {
        var proto = Object.getPrototypeOf(uad);
        Object.defineProperty(proto, "brands", {
          get: function () { return brands(); }, configurable: true, enumerable: true
        });
        var origHigh = proto.getHighEntropyValues;
        if (origHigh) {
          proto.getHighEntropyValues = function (hints) {
            return origHigh.call(this, hints).then(function (v) {
              if (v && v.brands) v.brands = brands();
              if (v && v.fullVersionList) v.fullVersionList = fullBrands();
              return v;
            });
          };
        }
        var origJson = proto.toJSON;
        if (origJson) {
          proto.toJSON = function () {
            var o = origJson.call(this);
            o.brands = brands();
            return o;
          };
        }
      }
    }
    if (!window.chrome) {
      window.chrome = {
        app: { isInstalled: false },
        csi: function () { return {}; },
        loadTimes: function () { return {}; }
      };
    }
  } catch (e) {}
})();
"""


class ClientHintsFixer(QWebEngineUrlRequestInterceptor):
    """Schickt in den HTTP-Headern dieselbe Marke („Google Chrome“), die die Seite per JavaScript sieht."""

    def __init__(self, major, parent=None):
        super().__init__(parent)
        self.value = (
            f'"Not)A;Brand";v="8", "Chromium";v="{major}", "Google Chrome";v="{major}"'
        ).encode("ascii")

    def interceptRequest(self, info):
        try:
            url = info.requestUrl()
            if url.scheme() != "https":
                return
            if url.host() in GOOGLE_LOGIN_HOSTS:
                # Google-Anmeldung: Firefox-Kennung, keine Chrome-Client-Hints.
                info.setHttpHeader(b"User-Agent", FIREFOX_UA.encode("ascii"))
                info.setHttpHeader(b"sec-ch-ua", b"")
            else:
                info.setHttpHeader(b"sec-ch-ua", self.value)
        except Exception:
            pass


def install_chrome_compat(profile, major):
    try:
        script = QWebEngineScript()
        script.setName("jadon-chrome-compat")
        script.setSourceCode(
            COMPAT_JS.replace("__CHROME_MAJOR__", str(major)).replace("__FIREFOX_UA__", FIREFOX_UA)
        )
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)
        profile.scripts().insert(script)
        fixer = ClientHintsFixer(major, profile)
        profile.setUrlRequestInterceptor(fixer)
        profile._jadon_hints = fixer  # Referenz behalten, sonst räumt Python das Objekt weg
    except Exception as exc:
        print("Hinweis: Chrome-Kompatibilität konnte nicht aktiviert werden:", exc)


def configure_profile(profile, private=False):
    """Alles, was ein 'normaler' Browser kann: WebRTC, Mikrofon, Kamera, Screen-Sharing, Clipboard ..."""
    ua = re.sub(r"\s*QtWebEngine/[\d.]+", "", profile.httpUserAgent())  # sieht aus wie Chrome → bessere Kompatibilität
    forced = str(SETTINGS.get("chrome_version", "")).strip()
    if forced.isdigit():  # optional: neuere Chrome-Version melden (WhatsApp/Discord prüfen die Mindestversion)
        ua = re.sub(r"Chrome/\d+", f"Chrome/{forced}", ua)
    profile.setHttpUserAgent(ua)
    match = re.search(r"Chrome/(\d+)", ua)
    install_chrome_compat(profile, match.group(1) if match else "130")
    profile.setHttpAcceptLanguage(QLocale.system().name().replace("_", "-") + ",en;q=0.8")
    if not private:
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        try:
            profile.setPersistentPermissionsPolicy(QWebEngineProfile.PersistentPermissionsPolicy.StoreOnDisk)
        except AttributeError:
            pass

    A = QWebEngineSettings.WebAttribute
    wanted = {
        "ScreenCaptureEnabled": True,
        "WebRTCPublicInterfacesOnly": False,
        "JavascriptCanAccessClipboard": True,
        "JavascriptCanPaste": True,
        "JavascriptCanOpenWindows": True,
        "AllowWindowActivationFromJavaScript": True,
        "PlaybackRequiresUserGesture": False,
        "FullScreenSupportEnabled": True,
        "PluginsEnabled": True,
        "PdfViewerEnabled": True,
        "LocalStorageEnabled": True,
        "WebGLEnabled": True,
        "Accelerated2dCanvasEnabled": True,
        "ScrollAnimatorEnabled": True,
        "AutoLoadIconsForPage": True,
        "ErrorPageEnabled": True,
        "DnsPrefetchEnabled": True,
        "HyperlinkAuditingEnabled": False,
    }
    s = profile.settings()
    for name, value in wanted.items():
        attr = getattr(A, name, None)
        if attr is not None:
            s.setAttribute(attr, value)

    profile.downloadRequested.connect(on_download)
    profile.setNotificationPresenter(on_notification)


# ----------------------------------------------------------------------------
# Web-Ansicht
# ----------------------------------------------------------------------------
class Page(QWebEnginePage):
    INTERNAL = {"http", "https", "file", "about", "data", "blob", "javascript", "view-source",
                "qrc", "chrome", "chrome-error", "devtools", "ftp", "filesystem"}
    # Nur diese Programme dürfen von Webseiten gestartet werden – und nur nach einem Klick + Bestätigung.
    # Alles andere (z. B. ms-msdt:, search-ms:, ms-officecmd:) wird blockiert.
    EXTERNAL_ALLOWED = {
        "mailto": "dein E-Mail-Programm", "tel": "die Telefon-App", "sms": "die Nachrichten-App",
        "zoommtg": "Zoom", "zoomus": "Zoom", "msteams": "Microsoft Teams", "slack": "Slack",
        "discord": "Discord", "spotify": "Spotify", "skype": "Skype", "tg": "Telegram",
        "whatsapp": "WhatsApp", "webcal": "deinen Kalender",
    }

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        scheme = url.scheme()
        if is_main_frame and scheme and scheme not in self.INTERNAL:
            clicked = nav_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked
            if clicked and scheme in self.EXTERNAL_ALLOWED:
                answer = QMessageBox.question(
                    QApplication.activeWindow(), "Externes Programm",
                    f"Diese Seite möchte {self.EXTERNAL_ALLOWED[scheme]} öffnen.\nZulassen?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer == QMessageBox.StandardButton.Yes:
                    QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)


class WebView(QWebEngineView):
    def __init__(self, win, profile):
        super().__init__()
        self.win = win
        self.is_popup = False
        self._crashes = []
        page = Page(profile, self)
        self.setPage(page)
        page.fullScreenRequested.connect(self._fullscreen)
        page.permissionRequested.connect(win.on_permission)
        page.desktopMediaRequested.connect(win.on_desktop_media)
        page.authenticationRequired.connect(win.on_auth)
        page.windowCloseRequested.connect(lambda: win.close_view(self))  # window.close() in Popups/OAuth
        page.renderProcessTerminated.connect(self._crashed)

    def createWindow(self, wtype):  # Popups, target="_blank", OAuth-Fenster, Mittelklick
        background = wtype == QWebEnginePage.WebWindowType.WebBrowserBackgroundTab
        view = self.win.new_tab(None, activate=not background).view
        view.is_popup = True
        return view

    def _fullscreen(self, request):
        request.accept()
        self.win.set_fullscreen(request.toggleOn())

    def _crashed(self, status, _code):
        """Stürzt der Seitenprozess ab (z. B. bei schweren Seiten), wird die Seite neu geladen – max. 3x pro Minute."""
        if status == QWebEnginePage.RenderProcessTerminationStatus.NormalTerminationStatus:
            return
        now = time.time()
        self._crashes = [t for t in self._crashes if now - t < 60] + [now]
        if len(self._crashes) <= 3:
            QTimer.singleShot(300, self._reload_after_crash)

    def _reload_after_crash(self):
        try:
            self.reload()
        except RuntimeError:
            pass


class Tab(QWidget):
    def __init__(self, win, profile):
        super().__init__()
        self.title = ""
        self.view = WebView(win, profile)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.view)


class TabBar(QTabBar):
    def mouseReleaseEvent(self, e):  # Mittelklick schließt den Tab
        if e.button() == Qt.MouseButton.MiddleButton:
            i = self.tabAt(e.position().toPoint())
            if i >= 0:
                self.tabCloseRequested.emit(i)
                return
        super().mouseReleaseEvent(e)


# ----------------------------------------------------------------------------
# Hauptfenster
# ----------------------------------------------------------------------------
class DownloadsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloads")
        self.resize(620, 380)
        lay = QVBoxLayout(self)
        self.list = QListWidget()
        lay.addWidget(self.list, 1)
        row = QHBoxLayout()
        for text, fn in (("Datei öffnen", self.open_file), ("Ordner zeigen", self.open_folder),
                         ("Abbrechen", self.cancel_download), ("Liste leeren", self.clear)):
            b = QPushButton(text)
            b.clicked.connect(fn)
            row.addWidget(b)
        lay.addLayout(row)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)

    def showEvent(self, e):
        self.refresh()
        self.timer.start(500)
        super().showEvent(e)

    def hideEvent(self, e):
        self.timer.stop()
        super().hideEvent(e)

    @staticmethod
    def _alive():
        alive = []
        for d in DOWNLOADS:
            try:
                d.downloadFileName()
                alive.append(d)
            except RuntimeError:  # Profil (privates Fenster) existiert nicht mehr
                pass
        DOWNLOADS[:] = alive
        return alive

    def refresh(self):
        row = self.list.currentRow()
        self.list.clear()
        S = QWebEngineDownloadRequest.DownloadState
        for d in self._alive():
            st = d.state()
            if st == S.DownloadCompleted:
                info = "fertig"
            elif st == S.DownloadCancelled:
                info = "abgebrochen"
            elif st == S.DownloadInterrupted:
                info = "unterbrochen"
            else:
                got, total = d.receivedBytes(), d.totalBytes()
                info = f"{got / 1048576:.1f} MB"
                if total > 0:
                    info += f" von {total / 1048576:.1f} MB ({int(got * 100 / total)} %)"
            self.list.addItem(f"{d.downloadFileName()}  –  {info}")
        if 0 <= row < self.list.count():
            self.list.setCurrentRow(row)

    def _current(self):
        i, alive = self.list.currentRow(), self._alive()
        return alive[i] if 0 <= i < len(alive) else None

    def open_file(self, *_):
        d = self._current()
        if d is None or d.state() != QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            return
        if os.path.splitext(d.downloadFileName())[1].lower() in RISKY_EXTENSIONS:
            QMessageBox.information(self, "Datei öffnen",
                                    "Ausführbare Dateien öffnet Jadon aus Sicherheitsgründen nicht selbst.\n"
                                    "Nutze „Ordner zeigen“ und prüfe die Datei vorher.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.join(d.downloadDirectory(), d.downloadFileName())))

    def open_folder(self, *_):
        d = self._current()
        if d is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(d.downloadDirectory()))

    def cancel_download(self, *_):
        d = self._current()
        if d is not None and not d.isFinished():
            d.cancel()

    def clear(self, *_):
        DOWNLOADS.clear()
        self.refresh()


class HistoryDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("Verlauf")
        self.resize(720, 460)
        lay = QVBoxLayout(self)
        self.filter = QLineEdit(placeholderText="Verlauf durchsuchen")
        self.filter.textChanged.connect(self._apply)
        self.list = QListWidget()
        self.list.itemActivated.connect(self._open)
        lay.addWidget(self.filter)
        lay.addWidget(self.list, 1)
        row = QHBoxLayout()
        b_clear, b_close = QPushButton("Verlauf löschen"), QPushButton("Schließen")
        b_clear.clicked.connect(self._clear)
        b_close.clicked.connect(self.accept)
        row.addWidget(b_clear)
        row.addStretch()
        row.addWidget(b_close)
        lay.addLayout(row)
        hist = [] if win.private else load_json(HISTORY_FILE, [])
        for h in reversed(hist):
            item = QListWidgetItem(f"{h.get('title', '')[:70]}  –  {h.get('url', '')}")
            item.setData(Qt.ItemDataRole.UserRole, h.get("url", ""))
            self.list.addItem(item)

    def _apply(self, text):
        t = text.lower()
        for i in range(self.list.count()):
            item = self.list.item(i)
            item.setHidden(t not in item.text().lower())

    def _open(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            self.win.new_tab(url)
            self.accept()

    def _clear(self, *_):
        save_json(HISTORY_FILE, [])
        self.list.clear()
        self.win._refresh_completer()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Einstellungen")
        self.resize(460, 200)
        form = QFormLayout(self)
        self.engine = QComboBox()
        self.engine.addItems(list(SEARCH_ENGINES))
        self.engine.setCurrentText(SETTINGS["search_engine"])
        self.home = QLineEdit(SETTINGS["homepage"])
        self.home.setPlaceholderText("leer = Jadon-Startseite")
        self.ask = QCheckBox("Vor jedem Download nach dem Speicherort fragen")
        self.ask.setChecked(bool(SETTINGS["ask_download"]))
        form.addRow("Suchmaschine", self.engine)
        form.addRow("Startseite", self.home)
        form.addRow(self.ask)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._save)
        bb.rejected.connect(self.reject)
        form.addRow(bb)

    def _save(self):
        SETTINGS.update(search_engine=self.engine.currentText(), homepage=self.home.text().strip(),
                        ask_download=self.ask.isChecked())
        save_json(SETTINGS_FILE, SETTINGS)
        self.accept()


PERMISSION_TEXT = {
    "MediaAudioCapture": "dein Mikrofon verwenden",
    "MediaVideoCapture": "deine Kamera verwenden",
    "MediaAudioVideoCapture": "deine Kamera und dein Mikrofon verwenden",
    "Notifications": "dir Benachrichtigungen senden",
    "Geolocation": "deinen Standort abrufen",
    "ClipboardReadWrite": "den Inhalt deiner Zwischenablage lesen",
    "MouseLock": "deinen Mauszeiger sperren",
    "LocalFontsAccess": "auf deine lokalen Schriftarten zugreifen",
}


class Jadon(QMainWindow):
    windows = []
    shared_profile = None

    def __init__(self, private=False, first_tab=True):
        super().__init__()
        self.private = private
        self.setWindowTitle(APP_NAME + (" – Privat" if private else ""))
        self.resize(1280, 820)
        Jadon.windows.append(self)

        if private:
            self.profile = QWebEngineProfile(self)  # ohne Namen = nichts wird gespeichert
            configure_profile(self.profile, private=True)
        else:
            self.profile = Jadon.shared_profile

        self.bookmarks = load_json(BOOKMARKS_FILE, [])
        self._printer = None
        self.tabs = []
        self.closed_tabs = []
        self._dl_dialog = None

        root = QWidget(objectName="root")
        self.setCentralWidget(root)
        col = QVBoxLayout(root)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)

        # Tableiste
        self.tabbar = TabBar(tabsClosable=True, movable=True, expanding=False, drawBase=False)
        self.tabbar.setElideMode(Qt.TextElideMode.ElideRight)
        self.tabbar.tabCloseRequested.connect(self.close_tab)
        self.tabbar.currentChanged.connect(self._tab_changed)
        self.tabbar.tabMoved.connect(self._tab_moved)
        self.tabbar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabbar.customContextMenuRequested.connect(self._tab_menu)
        self.stack = QStackedWidget()
        self.holder = QWidget()
        self.holder.setStyleSheet("background:#16151f;")
        hl = QHBoxLayout(self.holder)
        hl.setContentsMargins(8, 0, 8, 0)
        hl.addWidget(self.tabbar)
        hl.addStretch()

        # Werkzeugleiste
        self.bar = QWidget(objectName="bar")
        row = QHBoxLayout(self.bar)
        row.setContentsMargins(10, 7, 10, 7)
        row.setSpacing(4)
        self.btn_back = self._btn("‹", "Zurück (Alt+←)", lambda: self.view().back())
        self.btn_fwd = self._btn("›", "Vor (Alt+→)", lambda: self.view().forward())
        self.btn_reload = self._btn("⟳", "Neu laden (F5)", self._reload_or_stop)
        self.btn_home = self._btn("⌂", "Startseite", lambda: self.home())
        self.urlbar = QLineEdit(placeholderText="Suchen oder Adresse eingeben")
        self.urlbar.returnPressed.connect(self._navigate)
        self.completer_model = QStringListModel(self)
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setMaxVisibleItems(8)
        self.urlbar.setCompleter(self.completer)
        self.completer.activated.connect(lambda *_: QTimer.singleShot(0, self._navigate))
        self._refresh_completer()
        self.btn_star = self._btn("☆", "Lesezeichen (Strg+D)", lambda: self.toggle_bookmark())
        self.btn_new = self._btn("+", "Neuer Tab (Strg+T)", lambda: self.new_tab())
        self.btn_menu = QToolButton()
        self.btn_menu.setText("⋯")
        self.btn_menu.setToolTip("Menü")
        self.btn_menu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_menu.setMenu(self._build_menu())
        for w in (self.btn_back, self.btn_fwd, self.btn_reload, self.btn_home):
            row.addWidget(w)
        row.addWidget(self.urlbar, 1)
        for w in (self.btn_star, self.btn_new, self.btn_menu):
            row.addWidget(w)

        self.progress = QProgressBar(textVisible=False)
        self.progress.setRange(0, 100)

        # Suchleiste (Strg+F)
        self.findbar = QWidget(objectName="find")
        fl = QHBoxLayout(self.findbar)
        fl.setContentsMargins(10, 5, 10, 5)
        self.find_edit = QLineEdit(placeholderText="Auf der Seite suchen")
        self.find_edit.textChanged.connect(lambda t: self.view().findText(t))
        self.find_edit.returnPressed.connect(lambda: self.find_next())
        fl.addWidget(self.find_edit, 1)
        fl.addWidget(self._btn("↑", "Vorheriger Treffer", lambda: self.find_next(True)))
        fl.addWidget(self._btn("↓", "Nächster Treffer", lambda: self.find_next()))
        fl.addWidget(self._btn("✕", "Schließen (Esc)", lambda: self.hide_find()))
        self.findbar.hide()
        esc = QShortcut(QKeySequence("Esc"), self.findbar)
        esc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        esc.activated.connect(self.hide_find)

        col.addWidget(self.holder)
        col.addWidget(self.bar)
        col.addWidget(self.progress)
        col.addWidget(self.findbar)
        col.addWidget(self.stack, 1)

        self._shortcuts()
        if first_tab:
            self.new_tab()

    # ---------- Aufbau ----------
    def _btn(self, text, tip, slot):
        b = QToolButton()
        b.setText(text)
        b.setToolTip(tip)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.clicked.connect(slot)
        return b

    def _opener(self, url):
        return lambda *_: self.view().setUrl(QUrl(url))

    def _build_menu(self):
        m = QMenu(self)
        add_action(m, "Neuer Tab\tStrg+T", lambda: self.new_tab())
        add_action(m, "Geschlossenen Tab öffnen\tStrg+Shift+T", lambda: self.reopen_closed_tab())
        add_action(m, "Neues Fenster\tStrg+N", lambda: self.new_window())
        add_action(m, "Privates Fenster\tStrg+Shift+N", lambda: self.new_window(True))
        m.addSeparator()
        self.menu_bookmarks = m.addMenu("Lesezeichen")
        self.menu_bookmarks.aboutToShow.connect(self._fill_bookmarks)
        self.menu_history = m.addMenu("Verlauf (zuletzt besucht)")
        self.menu_history.aboutToShow.connect(self._fill_history)
        add_action(m, "Verlauf anzeigen …\tStrg+H", lambda: self.show_history())
        add_action(m, "Downloads …\tStrg+J", lambda: self.show_downloads())
        add_action(m, "Browserdaten löschen …\tStrg+Shift+Entf", lambda: self.clear_data())
        m.addSeparator()
        add_action(m, "Auf Seite suchen\tStrg+F", lambda: self.show_find())
        add_action(m, "Drucken …\tStrg+P", lambda: self.print_page())
        add_action(m, "Als PDF speichern …", lambda: self.save_pdf())
        add_action(m, "Seite speichern …\tStrg+S", lambda: self.save_page())
        add_action(m, "Seitenquelltext anzeigen\tStrg+U", lambda: self.view_source())
        m.addSeparator()
        add_action(m, "Vergrößern\tStrg++", lambda: self._zoom(+0.1))
        add_action(m, "Verkleinern\tStrg+-", lambda: self._zoom(-0.1))
        add_action(m, "Zoom zurücksetzen\tStrg+0", lambda: self.view().setZoomFactor(1.0))
        add_action(m, "Vollbild\tF11", lambda: self.set_fullscreen(not self.isFullScreen()))
        add_action(m, "Entwicklertools\tF12", lambda: self.dev_tools())
        add_action(m, "Bildschirm-/Mikrofon-Diagnose", lambda: self.open_test())
        m.addSeparator()
        add_action(m, "Einstellungen …\tStrg+,", lambda: self.show_settings())
        add_action(m, "Beenden", lambda: QApplication.closeAllWindows())
        return m

    def _shortcuts(self):
        def sc(keys, fn):
            QShortcut(QKeySequence(keys), self, activated=fn)
        sc("Ctrl+T", lambda: self.new_tab())
        sc("Ctrl+Shift+T", lambda: self.reopen_closed_tab())
        sc("Ctrl+W", lambda: self.close_tab(self.tabbar.currentIndex()))
        sc("Ctrl+N", lambda: self.new_window())
        sc("Ctrl+Shift+N", lambda: self.new_window(True))
        sc("Ctrl+L", lambda: (self.urlbar.setFocus(), self.urlbar.selectAll()))
        sc("Ctrl+R", lambda: self.view().reload())
        sc("F5", lambda: self.view().reload())
        sc("Ctrl+Shift+R", lambda: self.hard_reload())
        sc("Ctrl+F5", lambda: self.hard_reload())
        sc("Ctrl+D", lambda: self.toggle_bookmark())
        sc("Ctrl+F", lambda: self.show_find())
        sc("Ctrl+P", lambda: self.print_page())
        sc("Ctrl+S", lambda: self.save_page())
        sc("Ctrl+U", lambda: self.view_source())
        sc("Ctrl+H", lambda: self.show_history())
        sc("Ctrl+J", lambda: self.show_downloads())
        sc("Ctrl+Shift+Del", lambda: self.clear_data())
        sc("Ctrl+,", lambda: self.show_settings())
        sc("F12", lambda: self.dev_tools())
        sc("Alt+Left", lambda: self.view().back())
        sc("Alt+Right", lambda: self.view().forward())
        sc("Alt+Home", lambda: self.home())
        sc("Ctrl++", lambda: self._zoom(+0.1))
        sc("Ctrl+=", lambda: self._zoom(+0.1))
        sc("Ctrl+-", lambda: self._zoom(-0.1))
        sc("Ctrl+0", lambda: self.view().setZoomFactor(1.0))
        sc("Ctrl+Tab", lambda: self.tabbar.setCurrentIndex((self.tabbar.currentIndex() + 1) % self.tabbar.count()))
        sc("Ctrl+Shift+Tab", lambda: self.tabbar.setCurrentIndex((self.tabbar.currentIndex() - 1) % self.tabbar.count()))
        sc("Ctrl+PgDown", lambda: self.tabbar.setCurrentIndex((self.tabbar.currentIndex() + 1) % self.tabbar.count()))
        sc("Ctrl+PgUp", lambda: self.tabbar.setCurrentIndex((self.tabbar.currentIndex() - 1) % self.tabbar.count()))
        for n in range(1, 9):
            sc(f"Ctrl+{n}", lambda n=n: self.tabbar.setCurrentIndex(n - 1) if n - 1 < len(self.tabs) else None)
        sc("Ctrl+9", lambda: self.tabbar.setCurrentIndex(len(self.tabs) - 1))
        sc("F11", lambda: self.set_fullscreen(not self.isFullScreen()))

    # ---------- Dialoge und Extras ----------
    def show_downloads(self):
        if self._dl_dialog is None:
            self._dl_dialog = DownloadsDialog(self)
        self._dl_dialog.show()
        self._dl_dialog.raise_()
        self._dl_dialog.activateWindow()

    def show_history(self):
        HistoryDialog(self).exec()

    def show_settings(self):
        SettingsDialog(self).exec()

    def clear_data(self):
        answer = QMessageBox.question(
            self, "Browserdaten löschen",
            "Cookies, Cache und Verlauf löschen?\nDu wirst dabei auf Webseiten abgemeldet.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.profile.clearHttpCache()
        self.profile.cookieStore().deleteAllCookies()
        self.profile.clearAllVisitedLinks()
        save_json(HISTORY_FILE, [])
        self._refresh_completer()
        notify(APP_NAME, "Cookies, Cache und Verlauf wurden gelöscht.")

    def reopen_closed_tab(self):
        if self.closed_tabs:
            self.new_tab(self.closed_tabs.pop())

    def hard_reload(self):
        self.view().triggerPageAction(QWebEnginePage.WebAction.ReloadAndBypassCache)

    def view_source(self):
        url = self.view().url()
        if url.scheme() in ("http", "https"):
            self.new_tab("view-source:" + url.toString())

    def save_page(self):
        self.view().triggerPageAction(QWebEnginePage.WebAction.SavePage)

    def _refresh_completer(self):
        urls = []
        if not self.private:
            urls += [h.get("url", "") for h in reversed(load_json(HISTORY_FILE, [])[-300:])]
        urls += [b.get("url", "") for b in load_json(BOOKMARKS_FILE, [])]
        seen = set()
        self.completer_model.setStringList([u for u in urls if u and not (u in seen or seen.add(u))])

    # ---------- Fenster ----------
    def new_window(self, private=False):
        Jadon(private=private).show()

    def set_fullscreen(self, on):
        self.holder.setVisible(not on)
        self.bar.setVisible(not on)
        self.showFullScreen() if on else self.showNormal()

    def closeEvent(self, e):
        if self in Jadon.windows:
            Jadon.windows.remove(self)
        for i in range(self.stack.count()):
            self.stack.widget(i).deleteLater()
        if self.private:
            self.profile.deleteLater()
        super().closeEvent(e)

    # ---------- Tabs ----------
    def view(self):
        return self.stack.currentWidget().view

    def home(self, view=None):
        v = view or self.view()
        homepage = SETTINGS.get("homepage", "").strip()
        if homepage:
            v.setUrl(resolve_input(homepage))
        else:
            v.setHtml(START_PAGE.replace("{{SEARCH}}", json.dumps(search_url())), QUrl(f"https://{START_HOST}/"))

    def new_tab(self, url="start", activate=True):
        tab = Tab(self, self.profile)
        self.tabs.append(tab)
        self.stack.addWidget(tab)
        i = self.tabbar.addTab("Neuer Tab")
        if activate or len(self.tabs) == 1:
            self.tabbar.setCurrentIndex(i)
        v = tab.view
        v.titleChanged.connect(lambda t, tab=tab: self._set_title(tab, t))
        v.urlChanged.connect(lambda u, v=v: self._url_changed(v, u))
        v.iconChanged.connect(lambda ic, tab=tab: self._set_icon(tab, ic))
        v.loadProgress.connect(lambda p, v=v: self._progress(v, p))
        v.loadFinished.connect(lambda ok, v=v: self._load_finished(v, ok))
        v.page().recentlyAudibleChanged.connect(lambda _a, tab=tab: self.refresh_tab_label(tab))
        if url == "start":
            self.home(v)
            if activate:
                self.urlbar.setFocus()
        elif url:
            v.setUrl(QUrl(url))
        return tab

    def close_tab(self, i):
        if not 0 <= i < len(self.tabs):
            return
        if len(self.tabs) <= 1:
            self.close()
            return
        tab = self.tabs[i]
        u = tab.view.url()
        if not u.isEmpty() and u.host() != START_HOST and u.toString() != "about:blank":
            self.closed_tabs.append(u.toString())
        self.tabs.pop(i)
        self.tabbar.removeTab(i)
        self.stack.removeWidget(tab)
        tab.deleteLater()

    def close_view(self, view):
        """window.close() von der Seite – nur für Popups/Login-Fenster erlaubt, nicht für normale Tabs."""
        if not getattr(view, "is_popup", False):
            return
        for tab in self.tabs:
            if tab.view is view:
                QTimer.singleShot(0, lambda t=tab: self.close_tab(self.tabs.index(t)) if t in self.tabs else None)
                return

    def _tab_moved(self, frm, to):
        self.tabs.insert(to, self.tabs.pop(frm))

    def _tab_menu(self, pos):
        i = self.tabbar.tabAt(pos)
        if not 0 <= i < len(self.tabs):
            return
        tab = self.tabs[i]
        m = QMenu(self)
        add_action(m, "Neuer Tab", lambda: self.new_tab())
        add_action(m, "Neu laden", lambda: tab.view.reload())
        add_action(m, "Tab duplizieren", lambda: self._duplicate(tab))
        muted = tab.view.page().isAudioMuted()
        add_action(m, "Ton einschalten" if muted else "Tab stummschalten", lambda: self._toggle_mute(tab))
        m.addSeparator()
        add_action(m, "Tab schließen", lambda: self.close_tab(self.tabs.index(tab)))
        add_action(m, "Andere Tabs schließen", lambda: self._close_others(tab))
        m.exec(self.tabbar.mapToGlobal(pos))

    def _duplicate(self, tab):
        u = tab.view.url()
        self.new_tab("start" if u.isEmpty() or u.host() == START_HOST else u.toString())

    def _toggle_mute(self, tab):
        page = tab.view.page()
        page.setAudioMuted(not page.isAudioMuted())
        self.refresh_tab_label(tab)

    def _close_others(self, keep):
        for t in list(self.tabs):
            if t is not keep and t in self.tabs:
                self.close_tab(self.tabs.index(t))

    def _set_title(self, tab, title):
        if tab not in self.tabs:
            return
        tab.title = title
        self.refresh_tab_label(tab)
        if tab is self.tabs[self.tabbar.currentIndex()]:
            self.setWindowTitle(f"{title} – {APP_NAME}" if title else APP_NAME)

    def refresh_tab_label(self, tab):
        """Tab-Beschriftung mit Lautsprecher-Symbol, wenn die Seite Ton abspielt (🔇 = stummgeschaltet)."""
        if tab not in self.tabs:
            return
        i = self.tabs.index(tab)
        page = tab.view.page()
        prefix = "🔇 " if page.isAudioMuted() else ("🔊 " if page.recentlyAudible() else "")
        title = tab.title or "Neuer Tab"
        self.tabbar.setTabText(i, prefix + title[:40])
        self.tabbar.setTabToolTip(i, title)

    def _set_icon(self, tab, icon):
        if tab in self.tabs:
            self.tabbar.setTabIcon(self.tabs.index(tab), icon)

    def _tab_changed(self, i):
        if i < 0 or i >= len(self.tabs):
            return
        self.stack.setCurrentWidget(self.tabs[i])
        v = self.view()
        self._url_changed(v, v.url())
        self.setWindowTitle(f"{v.title()} – {APP_NAME}" if v.title() else APP_NAME)

    # ---------- Navigation ----------
    def _navigate(self):
        text = self.urlbar.text().strip()
        if not text:
            return
        url = resolve_input(text)
        self.view().setUrl(url)
        self.view().setFocus()

    def _url_changed(self, view, url):
        if view is not self.view():
            return
        internal = url.isEmpty() or url.host() == START_HOST
        self.urlbar.setText("" if internal else url.toString())
        self.urlbar.setCursorPosition(0)
        self.btn_back.setEnabled(view.history().canGoBack())
        self.btn_fwd.setEnabled(view.history().canGoForward())
        starred = any(b["url"] == url.toString() for b in self.bookmarks)
        self.btn_star.setText("★" if starred else "☆")
        self.btn_star.setStyleSheet("color:#fbbf24;" if starred else "")

    def _progress(self, view, p):
        if view is self.view():
            self.progress.setValue(p if p < 100 else 0)
            self.btn_reload.setText("✕" if 0 < p < 100 else "⟳")

    def _load_finished(self, view, ok):
        self._progress(view, 100)
        url = view.url()
        if ok and not self.private and url.host() != START_HOST and url.scheme() in ("http", "https"):
            hist = load_json(HISTORY_FILE, [])
            if not hist or hist[-1]["url"] != url.toString():
                hist.append({"title": view.title() or url.toString(), "url": url.toString(), "t": int(time.time())})
                save_json(HISTORY_FILE, hist[-1000:])
                self._refresh_completer()

    def _reload_or_stop(self):
        self.view().stop() if self.btn_reload.text() == "✕" else self.view().reload()

    def _zoom(self, delta):
        v = self.view()
        v.setZoomFactor(max(0.25, min(5.0, v.zoomFactor() + delta)))

    # ---------- Lesezeichen & Verlauf ----------
    def toggle_bookmark(self):
        v = self.view()
        url = v.url().toString()
        if v.url().isEmpty() or v.url().host() == START_HOST:
            return
        existing = [b for b in self.bookmarks if b["url"] == url]
        if existing:
            self.bookmarks.remove(existing[0])
        else:
            self.bookmarks.append({"title": v.title() or url, "url": url})
        save_json(BOOKMARKS_FILE, self.bookmarks)
        self._refresh_completer()
        self._url_changed(v, v.url())

    def _fill_bookmarks(self):
        self.bookmarks = load_json(BOOKMARKS_FILE, [])
        m = self.menu_bookmarks
        m.clear()
        if not self.bookmarks:
            m.addAction("(keine Lesezeichen)").setEnabled(False)
        for b in self.bookmarks:
            add_action(m, b["title"][:60], self._opener(b["url"]))

    def _fill_history(self):
        m = self.menu_history
        m.clear()
        hist = [] if self.private else load_json(HISTORY_FILE, [])
        if not hist:
            m.addAction("(leer)").setEnabled(False)
        for h in reversed(hist[-25:]):
            add_action(m, h["title"][:60], self._opener(h["url"]))
        if hist:
            m.addSeparator()
            add_action(m, "Verlauf löschen", lambda: save_json(HISTORY_FILE, []))

    # ---------- Suche auf Seite, Druck, DevTools ----------
    def show_find(self):
        self.findbar.show()
        self.find_edit.setFocus()
        self.find_edit.selectAll()

    def hide_find(self):
        self.findbar.hide()
        self.view().findText("")

    def find_next(self, backward=False):
        text = self.find_edit.text()
        if backward:
            self.view().findText(text, QWebEnginePage.FindFlag.FindBackward)
        else:
            self.view().findText(text)

    def print_page(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        if QPrintDialog(printer, self).exec() == QDialog.DialogCode.Accepted:
            self._printer = printer
            self.view().print(printer)

    def save_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Als PDF speichern", "seite.pdf", "PDF (*.pdf)")
        if path:
            self.view().printToPdf(path)

    def open_test(self):
        tab = self.new_tab(None)
        tab.view.setHtml(TEST_PAGE.replace("{{BINDING}}", BINDING), QUrl(f"https://{START_HOST}/diagnose"))

    def dev_tools(self):
        page = self.view().page()
        dev = self.new_tab(None)
        page.setDevToolsPage(dev.view.page())

    # ---------- Berechtigungen: Mikrofon, Kamera, Standort, ... ----------
    def on_permission(self, perm):
        kind = perm.permissionType().name
        if kind.startswith("Desktop"):
            perm.grant()  # Die Auswahl des Bildschirms/Fensters (Dialog) ist die eigentliche Zustimmung.
            return
        what = PERMISSION_TEXT.get(kind, f"auf „{kind}“ zugreifen")
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("Berechtigung")
        box.setText(f"{perm.origin().host() or 'Diese Seite'} möchte {what}.")
        allow = box.addButton("Erlauben", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Blockieren", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        perm.grant() if box.clickedButton() is allow else perm.deny()

    # ---------- Bildschirmfreigabe ----------
    def on_desktop_media(self, request):
        screens_model = request.screensModel()
        windows_model = request.windowsModel()
        dlg = QDialog(self)
        dlg.setWindowTitle("Bildschirm teilen")
        dlg.resize(520, 380)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel("Wähle, was du teilen möchtest:"))
        if sys.platform.startswith("win"):
            audio_hint = "Systemton wird mitgeteilt, wenn die Seite ihn anfordert (nur bei „Gesamter Bildschirm“)."
        else:
            audio_hint = "Hinweis: Systemton kann auf diesem System nicht mitgeteilt werden – nur Bild."
        hint = QLabel(audio_hint)
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#9d9bb5;font-size:12px;")
        tabs = QTabWidget()
        screens = QListView()
        screens.setModel(screens_model)
        windows = QListView()
        windows.setModel(windows_model)
        tabs.addTab(screens, "Gesamter Bildschirm")
        tabs.addTab(windows, "Fenster")
        lay.addWidget(tabs)
        lay.addWidget(hint)
        if screens_model.rowCount() > 0:
            screens.setCurrentIndex(screens_model.index(0, 0))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Teilen")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        lay.addWidget(buttons)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            if tabs.currentIndex() == 0 and screens.currentIndex().isValid():
                notify("Bildschirmfreigabe", f"Du teilst jetzt: {screens.currentIndex().data()}")
                request.selectScreen(screens.currentIndex())
                return
            if tabs.currentIndex() == 1 and windows.currentIndex().isValid():
                notify("Bildschirmfreigabe", f"Du teilst jetzt: {windows.currentIndex().data()}")
                request.selectWindow(windows.currentIndex())
                return
        request.cancel()

    # ---------- Anmeldung (HTTP-Auth) ----------
    def on_auth(self, url, auth):
        dlg = QDialog(self)
        dlg.setWindowTitle("Anmeldung erforderlich")
        form = QFormLayout(dlg)
        form.addRow(QLabel(f"{url.host()} verlangt eine Anmeldung\n{auth.realm()}"))
        user, pw = QLineEdit(), QLineEdit()
        pw.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Benutzer", user)
        form.addRow("Passwort", pw)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            auth.setUser(user.text())
            auth.setPassword(pw.text())


def main():
    if BINDING == "PySide6":
        print("Hinweis: PySide6 spielt kein H.264/AAC ab (Twitch, YouTube-Livestreams). "
              "Installiere für volle Video-Unterstützung: pip install PyQt6 PyQt6-WebEngine")
    load_settings()
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(STYLE)
    icon = make_icon()
    app.setWindowIcon(icon)

    if QSystemTrayIcon.isSystemTrayAvailable():
        TRAY["icon"] = QSystemTrayIcon(icon, app)
        TRAY["icon"].messageClicked.connect(
            lambda: TRAY["last_note"].click() if TRAY["last_note"] is not None else None
        )
        TRAY["icon"].show()

    profile = QWebEngineProfile(APP_NAME, app)  # persistent: Cookies, Logins, Berechtigungen
    configure_profile(profile)
    Jadon.shared_profile = profile

    urls = sys.argv[1:]
    win = Jadon(first_tab=not urls)
    for u in urls:
        win.new_tab(QUrl.fromUserInput(u).toString())
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
