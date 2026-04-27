#!/bin/bash

# 项目目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# APK 包名（Unity Build Settings → Player → Package Name），可用环境变量覆盖
APK_PACKAGE="${VSSP_APK_PACKAGE:-com.vssp.motionlink}"

# 解析模式
MODE="apk"
case "${1:-}" in
    ""|apk|--apk) MODE="apk" ;;
    web|--web)    MODE="web" ;;
    -h|--help)
        cat <<EOF
用法: $0 [--apk | --web]

  --apk  (默认)  自动启动 Pico 上的 VSSP Sender APK，只做 pose 同步（不需要戴头盔）
  --web          打开 Pico 浏览器进入 WebXR 模式（支持视频回显）

环境变量:
  VSSP_APK_PACKAGE  覆盖 APK 包名 (当前默认: $APK_PACKAGE)
EOF
        exit 0
        ;;
    *) echo "未知模式: $1（可用 --apk / --web）"; exit 1 ;;
esac

echo "🚀 VSSP 启动中 (模式: $MODE)"
echo "📂 项目目录: $PROJECT_DIR"

# --- Pico 防休眠 ---
echo "⚙️  配置 PICO 防休眠..."
adb shell settings put system screen_off_timeout 2147483647 > /dev/null 2>&1
adb shell settings put global stay_on_while_plugged_in 3 > /dev/null 2>&1
adb shell svc power stayon true > /dev/null 2>&1
echo "✅ PICO 已设置为永不休眠。"

cd "$PROJECT_DIR"

# --- 清理旧进程 ---
echo "=== 清理旧进程..."
pkill -f "fast_receiver.py" || true
pkill -f "video_streamer.py" || true
pkill -f "http.server 8000" || true
sleep 1

# --- pose 数据隧道（两种模式都需要）---
echo ">>> 建立 ADB 数据隧道 (8765 pose)..."
adb reverse tcp:8765 tcp:8765 > /dev/null

# --- pose 接收器（两种模式都需要）---
echo ">>> 启动 fast_receiver..."
python3 "$PROJECT_DIR/fast_receiver.py" &
RECEIVER_PID=$!

if [ "$MODE" = "web" ]; then
    # ========== WEB 模式 ==========
    adb reverse tcp:8787 tcp:8787 > /dev/null
    adb reverse tcp:8786 tcp:8786 > /dev/null
    adb reverse tcp:8000 tcp:8000 > /dev/null

    echo ">>> 启动 video_streamer + HTTP..."
    python3 "$PROJECT_DIR/video_streamer.py" &
    VIDEO_PID=$!
    python3 -m http.server 8000 > /dev/null 2>&1 &
    HTTP_PID=$!

    sleep 1

    echo ">>> 打开 Pico 浏览器..."
    adb shell am start -a android.intent.action.VIEW -d "http://127.0.0.1:8000" > /dev/null 2>&1

    trap "echo -e '\n停止服务...'; kill $RECEIVER_PID $VIDEO_PID $HTTP_PID 2>/dev/null; exit" SIGINT

    echo "-----------------------------------------------"
    echo "操作提示: 头盔里点击屏幕任意位置进入 VR；Ctrl+C 退出。"
    echo "-----------------------------------------------"
else
    # ========== APK 模式 ==========
    sleep 1

    # 检查 APK 是否已安装
    if ! adb shell pm list packages 2>/dev/null | tr -d '\r' | grep -qx "package:$APK_PACKAGE"; then
        echo "❌ APK 未安装: $APK_PACKAGE"
        echo "   请先在 Unity 里构建 VSSP Sender APK 并安装到 Pico，"
        echo "   或用环境变量指定正确包名："
        echo "     VSSP_APK_PACKAGE=com.your.company ./start.sh"
        kill $RECEIVER_PID 2>/dev/null
        exit 1
    fi

    echo ">>> 启动 Pico APK: $APK_PACKAGE"
    adb shell monkey -p "$APK_PACKAGE" -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1

    trap "echo -e '\n停止服务...'; adb shell am force-stop $APK_PACKAGE > /dev/null 2>&1; kill $RECEIVER_PID 2>/dev/null; exit" SIGINT

    echo "-----------------------------------------------"
    echo "APK 已拉起，pose 数据同步中。Ctrl+C 退出（并关闭 APK）。"
    echo "-----------------------------------------------"
fi

wait
