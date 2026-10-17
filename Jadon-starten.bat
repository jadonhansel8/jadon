@echo off
setlocal
cd /d "%~dp0"

rem Startet Jadon ueber das (signierte) Python statt ueber eine unsignierte .exe.
rem So blockiert Smart App Control den Browser nicht. Beim ersten Start wird alles eingerichtet.

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo Python wurde nicht gefunden.
  echo Bitte von https://www.python.org/downloads/ installieren und beim Setup
  echo "Add python.exe to PATH" ankreuzen. Danach diese Datei noch einmal starten.
  pause
  exit /b 1
)

if not exist ".venv\jadon_ready" (
  echo Erster Start: Die Umgebung wird eingerichtet. Das dauert einige Minuten ...
  if exist ".venv" rmdir /s /q ".venv"
  %PY% -m venv .venv || goto :fehler
  ".venv\Scripts\python.exe" -m pip install --upgrade pip || goto :fehler
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :fehler
  echo ok> ".venv\jadon_ready"
)

start "" ".venv\Scripts\pythonw.exe" jadon.py %*
exit /b 0

:fehler
echo.
echo Die Einrichtung ist fehlgeschlagen. Bitte die Meldungen oben lesen.
echo Tipp: Fuer genaue Fehlermeldungen im Browser selbst in diesem Ordner
echo   .venv\Scripts\python.exe jadon.py
echo ausfuehren.
pause
exit /b 1
