@echo off
REM ════════════════════════════════════════════════════════════════════════
REM web.cmd - Lance index.html dans une nouvelle fenêtre Chrome
REM ════════════════════════════════════════════════════════════════════════

REM Détection du chemin du script (fonctionne depuis n'importe où)
set "SCRIPT_DIR=%~dp0"

REM Chemin vers web.html (relatif au script)
set "HTML_FILE=%SCRIPT_DIR%index.html"

REM Vérifier que le fichier existe
if not exist "%HTML_FILE%" (
    echo ERREUR: Fichier non trouvé: %HTML_FILE%
    pause
    exit /b 1
)

REM Lancer Chrome dans une nouvelle fenêtre
REM --new-window force une nouvelle fenêtre (pas un onglet)
REM --app= lance en mode application (sans barre d'adresse) - optionnel
start "" "chrome.exe" --new-window "file:///%HTML_FILE:\=/%"

REM Alternative si Chrome n'est pas dans le PATH :
REM start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --new-window "file:///%HTML_FILE:\=/%"

exit /b 0
