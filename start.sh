#!/bin/bash

PROJECT_DIR="/Users/charlotfirth/Documents/pico-controller-adb"
cd "$PROJECT_DIR"

echo "=== 正在清理旧进程... ==="
lsof -ti:8000,8765 | xargs kill -9 > /dev/null 2>&1
sleep 1

# 1. 核心：建立 ADB 隧道
# 这会让 Pico 访问自己的 127.0.0.1 时，流量全打到 Mac 上
echo ">>> 建立 ADB 数据隧道..."
adb reverse tcp:8000 tcp:8000
adb reverse tcp:8765 tcp:8765

# 2. 启动接收器 (绑定到 127.0.0.1 确保安全)
python3 "$PROJECT_DIR/fast_receiver.py" &
RECEIVER_PID=$!

# 3. 启动网页服务器
python3 -m http.server 8000 &
HTTP_PID=$!

sleep 1

# 4. 指挥 Pico 浏览器打开 LOCALHOST 地址
# 只有访问 127.0.0.1，浏览器才会开启 VR 权限
echo ">>> 正在指挥 Pico 浏览器打开: http://127.0.0.1:8000"
adb shell am start -a android.intent.action.VIEW -d "http://127.0.0.1:8000" > /dev/null 2>&1

echo "-----------------------------------------------"
echo "操作提示:"
echo "1. Pico 应该会自动打开网页 (http://127.0.0.1:8000)。"
echo "2. 点击粉色按钮 '启动数据同步'。"
echo "3. 如果没自动打开，请手动在 Pico 输入: http://127.0.0.1:8000"
echo "==============================================="

trap "echo -e '\n正在停止...'; kill $RECEIVER_PID $HTTP_PID; exit" SIGINT
wait
