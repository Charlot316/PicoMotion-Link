# PicoMotion-Link 🚀

**PicoMotion-Link** is a high-performance, ultra-low latency bridge that streams real-time 6DOF pose and controller data (Buttons/Joystick/Gyro) from **Pico 4 Ultra** to **macOS/Windows/Linux** via USB. 

It leverages the power of **WebXR** and **ADB Port Forwarding** to bypass network isolation and security restrictions, providing a seamless data stream for developers and researchers.

[中文文档](#中文说明)

---

## 🌟 Features
- **Full 6DOF Tracking**: Real-time X, Y, Z position and Euler angles for **Head (HMD)** and **Both Controllers** simultaneously.
- **Full Input Mapping**: Support for all buttons:
  - **Left**: X, Y, Trigger, Grip, Joystick Click.
  - **Right**: A, B, Trigger, Grip, Joystick Click.
- **Live Joystick Data**: Real-time (X, Y) axis values.
- **Global Reset**: Press any **Joystick Click** to instantly recalibrate the origin (0,0,0) for all devices (Head & Hands).
- **Zero-Config Network**: Uses `adb reverse` to tunnel data over USB, bypassing Wi-Fi lag and firewall issues.
- **Terminal UI**: Clean, dual-row terminal display for real-time monitoring.
- **Unity Ready**: Built-in UDP forwarding (Port 9000) for instant integration.

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
- **双持 6自由度追踪**: 同时实时获取双手柄的 X, Y, Z 位移及欧拉角。
- **全键位映射**: 完美支持所有物理按键：
  - **左手**: X, Y, 扳机, 握持, 摇杆按下。
  - **右手**: A, B, 扳机, 握持, 摇杆按下。
- **实时摇杆数据**: 高精度获取摇杆 (X, Y) 轴数值。
- **一键复位**: **按下摇杆 (Joystick Click)** 即可瞬间将对应手柄的位置重置为原点 (0,0,0)。
- **免配置网络**: 利用 `adb reverse` 建立 USB 隧道，无视 Wi-Fi 延迟和防火墙限制。
- **终端 UI**: 干净的双行终端显示，实时监控双手状态。
- **Unity 友好**: 内置 UDP 转发（端口 9000），可直接驱动 Unity 项目。

## 🛠 环境要求
- **硬件**: Pico 4 Ultra / Pico 4。
- **系统**: macOS / Windows / Linux。
- **软件依赖**: 
  - Python 3.x
  - 已安装 ADB (`brew install android-platform-tools`)。
  - 安装 Flask: `pip install flask`。

## 📄 License
Apache-2.0