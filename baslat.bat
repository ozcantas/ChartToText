@echo off
title DePlot Vision Studio (FastAPI + React)
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo  🚀 DePlot Vision Studio Baslatiliyor...
echo  Moduler Backend + React Arayuzu yukleniyor...
echo ========================================================
.\env\Scripts\python.exe main.py
pause
