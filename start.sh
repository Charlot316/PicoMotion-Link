#!/bin/bash

PROJECT_DIR="/Users/charlotfirth/Documents/pico-controller-adb"
cd "$PROJECT_DIR"

echo "=== 正在清理旧进程... ==="
lsof -ti:8000,8765 | xargs kill -9 > /dev/null 2>&1
sleep 1

# 1. 核心：建立 ADB 隧道
echo ">>> 建立 ADB 数据隧道..."
adb reverse tcp:8000 tcp:8000
adb reverse tcp:8765 tcp:8765

# 2. 禁用休眠感应器 (让头显保持清醒)
echo ">>> 正在禁用接近感应器 (防止休眠)..."
adb shell am broadcast -a com.pvr.intent.action.SETTINGS --es device_node_id proximity_sensor --ez status false > /dev/null 2>&1
adb shell settings put system screen_off_timeout 2147483647 > /dev/null 2>&1

# 3. 启动服务
python3 "$PROJECT_DIR/fast_receiver.py" &
RECEIVER_PID=$!

python3 -m http.server 8000 > /dev/null 2>&1 &
HTTP_PID=$!

sleep 1

# 4. 指挥 Pico 浏览器打开 LOCALHOST 地址
echo ">>> 正在指挥 Pico 浏览器打开: http://127.0.0.1:8000"
adb shell am start -a android.intent.action.VIEW -d "http://127.0.0.1:8000" > /dev/null 2>&1

echo "-----------------------------------------------"
echo "操作提示:"
echo "1. 点击按钮 '启动全量同步'。"
echo "2. VR 内部现在可以看到手柄模型和实时数据。"
echo "3. 按 Ctrl+C 退出时，将自动恢复休眠感应器。"
echo "==============================================="

# 捕获退出信号，恢复感应器
cleanup() {
    echo -e "\n正在恢复休眠感应器设置..."
    adb shell am broadcast -a com.pvr.intent.action.SETTINGS --es device_node_id proximity_sensor --ez status true > /dev/null 2>&1
    adb shell settings put system screen_off_timeout 60000 > /dev/null 2>&1
    kill $RECEIVER_PID $HTTP_PID
    exit
}

trap cleanup SIGINT
wait