@echo off
chcp 65001 >nul
title Hosszu video keszito - WAN2_2
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
.\ComfyUI_windows_portable\python_embeded\python.exe -s video_keszito.py
echo.
pause
