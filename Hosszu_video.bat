@echo off
chcp 65001 >nul
title Hosszu video - WAN2_2
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo (A ComfyUI_inditas.bat-nak futnia kell kozben.)
echo.
rem Ha egy feladat .json-t huzol ra, azt futtatja; ha uresen inditod, listabol valaszthatsz.
.\ComfyUI_windows_portable\python_embeded\python.exe -s hosszu_video.py %1
pause
