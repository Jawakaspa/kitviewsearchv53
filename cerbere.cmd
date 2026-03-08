@echo off
chcp 65001 >nul
title Cerbere - Gardien des projets

echo ===========================================================
echo  Lancement de Cerbere V2 qui s'appele C:\cerbere\cerbere.py
echo ===========================================================
echo.

REM Lancement avec redirection pour eviter "Terminer le programme (O/N)?"
cmd /c python C:\cerbere\cerbere.py

if errorlevel 1 (
    echo.
    echo [ERREUR] Cerbere s'est arrete avec une erreur.
    pause
)
