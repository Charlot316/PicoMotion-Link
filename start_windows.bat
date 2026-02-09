@echo off
set PROJECT_DIR=%~dp0
cd /d %PROJECT_DIR%

echo ===============================================
echo    VSSP v1.0 - Ultra Low Latency VR Stream
echo ===============================================

echo [1/3] Cleaning up old processes...
taskkill /f /im python.exe /t >nul 2>&1

echo [2/3] Setting up ADB tunnel...
:: Web Content
adb reverse tcp:8000 tcp:8000
:: WebSocket Relay
adb reverse tcp:8787 tcp:8787
:: Pose Data
adb reverse tcp:8765 tcp:8765

echo [3/3] Starting servers...
:: Start HTTPS Static Server
start /b python https_server.py
:: Start VSSP Relay Server
start /b python video_streamer.py

timeout /t 3 >nul

echo >>> Launching VR Interface on Pico...
adb shell am start -a android.intent.action.VIEW -d "https://127.0.0.1:8000"

echo -----------------------------------------------
echo VSSP Streaming System is ACTIVE!
echo 1. Keep this window open.
echo 2. Enter VR mode on your Pico.
echo -----------------------------------------------

:: Run monitor in foreground to see if frames are coming
python monitor.py
pause
