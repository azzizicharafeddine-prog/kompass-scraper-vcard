@echo off
chcp 65001 >nul
title Kompass Scraper Automatique
cd /d "%~dp0"

echo ======================================================
echo    KOMPASS SCRAPER AUTOMATIQUE
echo ======================================================
echo.

python kompasScraper.py --auto

pause
