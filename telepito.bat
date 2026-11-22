@echo off
chcp 65001 >nul
title WAN2_2 telepito
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0telepito.ps1" %*
echo.
pause
