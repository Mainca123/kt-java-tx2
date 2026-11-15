@echo off
setlocal
title E-Commerce Microservices
set "LAUNCHER=%~dp0scripts\run.ps1"
if exist "%~dp0code\scripts\run.ps1" set "LAUNCHER=%~dp0code\scripts\run.ps1"
if not exist "%LAUNCHER%" (
    echo ERROR: Missing scripts\run.ps1. Extract/download the complete project first.
    if not "%TX2_NO_PAUSE%"=="1" pause
    exit /b 1
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%LAUNCHER%" %*
set "RESULT=%ERRORLEVEL%"
echo.
if not "%TX2_NO_PAUSE%"=="1" pause
exit /b %RESULT%
