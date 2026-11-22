@echo off
chcp 65001 >nul
title ComfyUI - WAN2_2
cd /d "%~dp0ComfyUI_windows_portable"
echo ComfyUI indul... Ha betoltott, a bongeszoben: http://127.0.0.1:8188
.\python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build
pause
