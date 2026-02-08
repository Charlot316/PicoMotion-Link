# PicoMotion-Link 🚀

**PicoMotion-Link** is a lightweight, ultra-low latency bridge that streams real-time 6DOF pose and controller data (Buttons/Joystick/Gyro) from **Pico 4 Ultra** to **macOS** via USB. 

It leverages the power of **WebXR** and **ADB Port Forwarding** to bypass network isolation and security restrictions, providing a seamless data stream for developers and researchers.

[中文文档](#中文说明)

---

## 🌟 Features
- **6DOF Tracking**: Real-time X, Y, Z position and Euler angles (Pitch/Yaw/Roll).
- **Full Input Mapping**: Support for all buttons (Trigger, Grip, A/B/X/Y) and Joysticks.
- **Zero-Config Network**: Uses `adb reverse` to tunnel data over USB, bypassing Wi-Fi lag and firewall issues.
- **Auto-Calibration**: Automatic initial position anchoring on startup.
- **Unity Ready**: Built-in UDP forwarding (Port 9000) for instant integration with Unity projects.

## 🛠 Prerequisites
- **Hardware**: Pico 4 Ultra / Pico 4.
- **System**: macOS.
- **Software**: 
  - Python 3.x
  - ADB (Android Debug Bridge) installed (`brew install android-platform-tools`).
  - `Flask` library (`pip install flask`).

## 🚀 Quick Start
1. **Connect**: Connect your Pico 4 Ultra to your Mac via USB and enable USB Debugging.
2. **Run**:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
3. **VR Mode**: Look into your Pico headset. The browser will automatically open `http://127.0.0.1:8000`. Click **"Start Sync"** to enter VR mode.
4. **Stream**: Watch your terminal for real-time data flow!

---

<a name="中文说明"></a>
## 🌟 功能特性
- **6自由度追踪**: 实时获取 X, Y, Z 位移及欧拉角（俯仰/偏航/翻滚）。
- **全键位映射**: 支持所有按键（扳机、握持、A/B/X/Y）以及摇杆数据。
- **免配置网络**: 利用 `adb reverse` 建立 USB 隧道，无视 Wi-Fi 延迟和防火墙限制。
- **自动校准**: 启动时自动锚定初始位置。
- **Unity 友好**: 内置 UDP 转发（端口 9000），可直接驱动 Unity 场景中的物体。

## 🛠 环境要求
- **硬件**: Pico 4 Ultra / Pico 4。
- **系统**: macOS。
- **软件依赖**: 
  - Python 3.x
  - 已安装 ADB (`brew install android-platform-tools`)。
  - 安装 Flask: `pip install flask`。

## 🚀 快速开始
1. **连接**: 使用 USB 线连接 Pico 4 Ultra 与 Mac，并开启 USB 调试。
2. **启动**:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
3. **进入VR**: 戴上头显，浏览器会自动打开 `http://127.0.0.1:8000`。点击 **"开始全量同步"**。
4. **接收数据**: 你的 Mac 终端将开始实时刷新手柄数据。

---

## 🏗 Project Structure
- `start.sh`: One-click automation script.
- `fast_receiver.py`: High-speed Flask-based data receiver.
- `index.html`: WebXR data collector for Pico Browser.
- `monitor.py`: Optional ADB-based raw event listener.

## 📄 License
MIT
