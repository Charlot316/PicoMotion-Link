#!/bin/bash

PROJECT_DIR="/Users/charlotfirth/Documents/pico-controller-adb"
cd "$PROJECT_DIR"

echo "=== 正在清理旧进程... ==="
lsof -ti:8000,8765 | xargs kill -9 > /dev/null 2>&1
sleep 1

# 1. 建立 ADB 数据隧道
echo ">>> 建立 ADB 数据隧道 (USB 传输模式)..."
adb reverse tcp:8000 tcp:8000
adb reverse tcp:8765 tcp:8765

# 2. 启动服务
echo ">>> 启动数据中心..."
python3 "$PROJECT_DIR/fast_receiver.py" &
RECEIVER_PID=$!

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

trap "echo -e '\n正在停止服务...'; kill $RECEIVER_PID $HTTP_PID; exit" SIGINT
wait