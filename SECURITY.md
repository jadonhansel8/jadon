# Sicherheit

## Warum schlägt Windows-Sicherheit (Defender) manchmal an?

Jadon wird mit **PyInstaller** zu einer `.exe` verpackt. Solche Programme werden von Virenscannern
häufig fälschlich markiert („False Positive", oft mit Namen wie `Trojan:Win32/Wacatac.B!ml`).
Gründe sind unter anderem, dass die Datei neu, selten heruntergeladen und nicht digital signiert ist.
Das bedeutet **nicht automatisch**, dass sie Schadcode enthält – ausschließen kann man es ohne Prüfung
aber auch nicht. Deshalb gilt: Prüfe, bevor du vertraust.

## So prüfst du eine heruntergeladene Datei

1. **Prüfsumme vergleichen.** Jedes Release enthält `SHA256SUMS.txt`.

   ```powershell
   Get-FileHash .\Jadon-windows-x64.zip -Algorithm SHA256
   ```
   Linux/macOS: `sha256sum Jadon-linux-x64.tar.gz` bzw. `shasum -a 256 Jadon-macos-arm64.zip`

2. **Herkunft prüfen.** Die Pakete werden von GitHub Actions gebaut und – sobald das Repository
   **öffentlich** ist – mit einem Herkunftsnachweis versehen (bei privaten Repositories bietet GitHub
   das nicht an, dort entfällt dieser Schritt). Mit der [GitHub CLI](https://cli.github.com/) kannst du bestätigen, dass die Datei aus
   diesem Repository stammt:

   ```bash
   gh attestation verify Jadon-windows-x64.zip --repo jadonhansel8/jadon
   ```

3. **Selbst bauen.** Der gesamte Quellcode ist eine einzige lesbare Datei (`jadon.py`).
   Wer keiner fertigen `.exe` traut, startet einfach `python jadon.py` oder baut mit PyInstaller selbst.

4. **Mehrere Scanner fragen.** Lade die Datei auf <https://www.virustotal.com> hoch. Melden nur
   wenige Scanner mit generischen Namen („Gen", „ML", „Heur"), ist es sehr wahrscheinlich ein False Positive.

## Wenn Defender trotzdem anschlägt

- Unter *Windows-Sicherheit → Viren- & Bedrohungsschutz → Schutzverlauf* siehst du den genauen Namen.
- Du kannst die Datei als Fehlalarm bei Microsoft melden:
  <https://www.microsoft.com/wdsi/filesubmission> (Option „Ich glaube, die Datei ist nicht bedrohlich").
- Schalte den Echtzeitschutz **nicht** global aus. Eine Ausnahme setzt du nur für eine Datei, deren
  Prüfsumme (siehe oben) stimmt und der du vertraust.

## Was Jadon selbst für Sicherheit tut

- Die Chromium-Sandbox von Qt WebEngine bleibt eingeschaltet.
- Mikrofon, Kamera, Standort usw. nur nach Rückfrage; Bildschirmfreigabe nur über den Auswahldialog.
- Webseiten dürfen externe Programme nur nach einem Klick, nur aus einer kleinen Liste (z. B. `mailto:`,
  `zoommtg:`) und nach Bestätigung öffnen. Gefährliche Protokolle werden blockiert.
- Warnung vor dem Herunterladen ausführbarer Dateien (`.exe`, `.msi`, `.ps1`, `.js` …).
- Zertifikatsfehler werden nicht umgangen, Hyperlink-Auditing ist aus.
- Lesezeichen und Verlauf liegen lokal in `~/.jadon/`; im privaten Fenster wird nichts gespeichert.
- Der Build verzichtet auf UPX-Packer, enthält Versionsinformationen, erzeugt Prüfsummen und
  Herkunftsnachweise und kann Windows-Programme digital signieren (siehe unten).

## Für Maintainer: digitale Signatur (empfohlen)

Eine Codesignatur ist die wirksamste Maßnahme gegen Warnungen von Windows (SmartScreen/Defender).

1. Besorge ein Code-Signing-Zertifikat (kostenpflichtig) oder bewirb dich für das kostenlose
   Programm [SignPath Foundation](https://signpath.org/) für Open-Source-Projekte.
2. Lege im Repository unter *Settings → Secrets and variables → Actions* an:
   - `WINDOWS_CERT_BASE64` – die `.pfx`-Datei als Base64 (`certutil -encode` bzw. `base64`)
   - `WINDOWS_CERT_PASSWORD` – das Passwort der `.pfx`
3. Der Workflow signiert `Jadon.exe` dann automatisch. Ohne diese Secrets wird der Schritt übersprungen.

## Sicherheitslücke melden

Bitte öffne ein [privates Security Advisory](../../security/advisories/new) im Repository
(*Security → Report a vulnerability*) und poste Details nicht öffentlich als Issue.
