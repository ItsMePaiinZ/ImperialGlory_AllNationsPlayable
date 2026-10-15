@echo off
title Imperial Glory - All Nations Playable - Uninstall
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0patcher.ps1" -Action uninstall
echo.
pause
