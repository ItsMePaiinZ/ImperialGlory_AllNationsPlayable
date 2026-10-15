@echo off
title Imperial Glory - All Nations Playable - Install
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0patcher.ps1" -Action install
echo.
pause
