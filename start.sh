#!/bin/bash

# 获取项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "🚀 正在启动 PICO Controller 适配环境..."
echo "📂 项目目录: $PROJECT_DIR"

# --- [新增加的防休眠逻辑] ---
echo "⚙️  正在配置 PICO 防休眠模式 (Stay Awake)..."
adb shell settings put system screen_off_timeout 2147483647 > /dev/null 2>&1
adb shell settings put global stay_on_while_plugged_in 3 > /dev/null 2>&1
adb shell svc power stayon true > /dev/null 2>&1
echo "✅ PICO 已设置为永不休眠模式。"
# ---------------------------

# 确保在项目根目录下运行，以便 index.html 能被正确找到
cd "$PROJECT_DIR"

echo "=== 正在清理旧进程 (Safe Mode)..."
pkill -f "fast_receiver.py" || true
pkill -f "video_streamer.py" || true
pkill -f "http.server 8000" || true
sleep 1

# 1. 建立 ADB 数据隧道
echo ">>> 建立 ADB 数据隧道 (USB 传输模式)..."
adb reverse tcp:8765 tcp:8765
adb reverse tcp:8787 tcp:8787
adb reverse tcp:8786 tcp:8786
adb reverse tcp:8000 tcp:8000

# 2. 启动服务
echo ">>> 启动数据中心与视频流中转..."
python3 "$PROJECT_DIR/fast_receiver.py" &
RECEIVER_PID=$!

python3 "$PROJECT_DIR/video_streamer.py" &
VIDEO_PID=$!

python3 -m http.server 8000 > /dev/null 2>&1 &
HTTP_PID=$!

sleep 1

# 3. 指挥 Pico 浏览器打开 LOCALHOST 地址
echo ">>> 正在启动 Pico 浏览器..."
adb shell am start -a android.intent.action.VIEW -d "http://127.0.0.1:8000" > /dev/null 2>&1

echo "-----------------------------------------------"
echo "操作提示:"
echo "1. 点击按钮 '启动全量同步'。"
echo "2. 若需防止休眠，请在头显感应器处粘贴遮挡物。"
echo "3. 按 Ctrl+C 退出。"
echo "==============================================="

trap "echo -e '\n正在停止服务...'; kill $RECEIVER_PID $HTTP_PID $VIDEO_PID; exit" SIGINT
wait