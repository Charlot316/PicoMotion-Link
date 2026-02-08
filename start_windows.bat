@echo off
set PROJECT_DIR=%~dp0
cd /d %PROJECT_DIR%

echo ===============================================
echo    PicoMotion-Link (Windows Version)
echo ===============================================

echo [1/3] Cleaning up old processes...
taskkill /f /im python.exe /t >nul 2>&1

echo [2/3] Setting up ADB tunnel...
adb reverse tcp:8000 tcp:8000
adb reverse tcp:8765 tcp:8765

echo [3/3] Starting servers...
start /b python fast_receiver.py
start /b python -m http.server 8000

timeout /t 2 >nul

echo >>> Launching Pico Browser...
adb shell am start -a android.intent.action.VIEW -d "http://127.0.0.1:8000"

echo -----------------------------------------------
echo Data sync is running! 
echo Press Ctrl+C in this window to stop.
echo -----------------------------------------------

:: Keep the window open to see data (though background python might not print here)
:: For Windows, it's better to run fast_receiver in a visible window
python fast_receiver.py
pause
