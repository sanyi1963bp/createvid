@echo off
chcp 65001 >nul
title Hosszu video - WAN2_2
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set FELADAT=%~1
if "%FELADAT%"=="" set FELADAT=pelda_feladat.json
echo Feladat: %FELADAT%
echo (A ComfyUI_inditas.bat-nak futnia kell kozben.)
.\ComfyUI_windows_portable\python_embeded\python.exe -s hosszu_video.py "%FELADAT%"
pause
