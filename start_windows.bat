@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "PROJECT_DIR=%~dp0"
set "PICO_URL=http://127.0.0.1:8000"

cd /d "%PROJECT_DIR%"
if errorlevel 1 (
  echo ❌ 无法进入目录: "%PROJECT_DIR%"
  pause
  exit /b 1
)

echo ===============================================
echo    VSSP v1.1 - PICO Controller Link (Windows)
echo ===============================================

echo [0/5] 检查 ADB 连接...
adb start-server >nul 2>&1
set "HAS_DEVICE="
for /f "skip=1 tokens=1,2" %%a in ('adb devices') do (
  if "%%b"=="device" set "HAS_DEVICE=1"
)
if not defined HAS_DEVICE (
  echo ❌ 未检测到可用 Pico 设备（或未授权 USB 调试）。
  echo    请先在头显里允许 USB 调试，再重试。
  pause
  exit /b 1
)

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
adb reverse tcp:8786 tcp:8786

echo [4/4] 启动 VSSP 服务端...
:: 1. 启动坐标接收中心
start "vssp_receiver" /b cmd /c "python fast_receiver.py"
:: 2. 启动视频中转
start "vssp_video" /b cmd /c "python video_streamer.py"
:: 3. 启动网页服务器
start "vssp_http" /b cmd /c "python -m http.server 8000"

timeout /t 5 >nul

echo >>> 正在 Pico 中启动 VR 界面...
call :open_pico_browser
if errorlevel 1 (
  echo ❌ 自动拉起浏览器失败，请手动在 Pico 浏览器打开: %PICO_URL%
) else (
  echo ✅ 已触发 Pico 浏览器打开命令: %PICO_URL%
)

echo -----------------------------------------------
echo VSSP 系统已激活！
echo 如果黑窗口里出现了 HEAD/LEFT/RIGHT 数据，说明同步正常。
echo -----------------------------------------------

:: 选配：运行 monitor 监控硬件层原始事件
python monitor.py
pause
exit /b 0

:open_pico_browser
adb shell am start -W -a android.intent.action.VIEW -d "%PICO_URL%" >nul 2>&1 && exit /b 0
adb shell am start -W -a android.intent.action.VIEW -d "%PICO_URL%" com.picovr.browser >nul 2>&1 && exit /b 0
adb shell am start -W -a android.intent.action.VIEW -d "%PICO_URL%" com.pvr.browser >nul 2>&1 && exit /b 0
exit /b 1
