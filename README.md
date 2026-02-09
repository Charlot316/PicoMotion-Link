# VSSP (VR Stereo Streaming Protocol) v1.0 🚀

**VSSP** 是一个专为 **Pico 4 Ultra** 设计的高性能、超低延迟 3D 视频串流及追踪同步方案。它实现了从物理设备到 WebXR 端的全链路闭环，支持 6DOF 位移、手柄按键、以及原生双视口 3D 视频流。

[中文文档](#中文说明)

---

## 🌟 Features
- **Independent Eye Rendering**: Dual-viewport stream (Eye 1 / Eye 2) with NO horizontal compression. Now optimized to **1:1 Square Aspect Ratio** to match VR view and save 43% bandwidth.
- **Ultra-Low Latency**: Optimized UDP transport for video and async WebXR pose sync.
- **Full 6DOF & Input Mapping**: 
  - **Head & Hands**: Real-time position and orientation.
  - **Buttons**: A/B/X/Y, Triggers, Grips, Joysticks.
- **AutoHand Integration**: Native support for **AutoHand** physics interaction system.
- **Head-Gaze Directional Movement**: Left-joystick movement is automatically aligned to where you are looking.
- **Zero-Config Network**: Tunneling via `adb reverse` over USB for maximum stability.

## 🚀 Quick Start
1. **Unity Setup**: Import scripts from the `UnityExample/` folder into your project. Add `PicoVideoStreamer`, `HandDesktopControllerLink`, and `PicoMotionLinkReceiver` to your scene.
2. **Connect**: Link your Pico 4 Ultra via USB (Enable USB Debugging).
3. **Run Server**:
   ```bash
   chmod +x start.sh && ./start.sh
   # On Windows: run start_windows.bat
   ```
4. **Enter VR**: The browser on Pico will open `https://127.0.0.1:8000`. Click **"Start VR"** to begin.

---

<a name="中文说明"></a>
## 🌟 功能特性
- **原生双目独立渲染**: 非传统的 SBS 合图模式。左右眼独立采样发送，现已优化为 **1:1 正方形比例** 以适配 VR 视口并节省约 43% 带宽。
- **极致低延迟**: 视频流基于 UDP，追踪数据基于异步 WebSocket。
- **全方位交互**: 
  - **追踪**: 头部视角、双持手柄位置及姿态。
  - **摇杆/按键**: 映射 Unity 物理轴向，支持视角导向移动逻辑。
- **AutoHand 联动**: 提供对 **AutoHand** 物理交互系统的原生脚本支持（见示例脚本）。
- **一键部署**: 自动配置 ADB 端口转发，无视 Wi-Fi 环境波动。

## 🛠 开发环境
- **硬件**: Pico 4 Ultra / Pico 4。
- **Python**: 3.10+ (Dependencies: `websockets`, `cryptography` for HTTPS).
- **Unity**: 2021.3+ (Integrated via VSSP Provider scripts).

## 📄 License
Apache-2.0