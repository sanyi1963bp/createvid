@echo off
chcp 65001 >nul
title Hosszu video keszito - grafikus felulet
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
.\ComfyUI_windows_portable\python_embeded\python.exe -s gui_szerver.py
pause
