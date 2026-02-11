@echo off
set PROJECT_DIR=%~dp0
cd /d %PROJECT_DIR%

echo ===============================================
echo    VSSP v1.1 - PICO Controller Link (Windows)
echo ===============================================

echo [1/4] 清理旧进程...
taskkill /f /im python.exe /t >nul 2>&1

echo [2/4] 配置 PICO 永不休眠模式 (Stay Awake)...
adb shell settings put system screen_off_timeout 2147483647 >nul 2>&1
adb shell settings put global stay_on_while_plugged_in 3 >nul 2>&1
adb shell svc power stayon true >nul 2>&1
echo ✅ 已设置为永不休眠。

echo [3/4] 建立 ADB 数据隧道...
adb reverse tcp:8000 tcp:8000
adb reverse tcp:8787 tcp:8787
adb reverse tcp:8765 tcp:8765

echo [4/4] 启动 VSSP 服务端...
:: 1. 启动坐标接收中心
start /b python fast_receiver.py
:: 2. 启动视频中转
start /b python video_streamer.py
:: 3. 启动网页服务器
start /b python -m http.server 8000

timeout /t 3 >nul

echo >>> 正在 Pico 中启动 VR 界面...
adb shell am start -a android.intent.action.VIEW -d "http://127.0.0.1:8000"

echo -----------------------------------------------
echo VSSP 系统已激活！
echo 如果黑窗口里出现了 HEAD/LEFT/RIGHT 数据，说明同步正常。
echo -----------------------------------------------

:: 选配：运行 monitor 监控硬件层原始事件
python monitor.py
pause
