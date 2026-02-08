import subprocess
import re
import sys

def get_pico_event_paths():
    """通过 adb 获取 Pico 手柄的事件设备路径"""
    try:
        output = subprocess.check_output(["adb", "shell", "getevent", "-lp"], text=True)
        devices = {}
        current_device = None
        
        for line in output.splitlines():
            # 匹配设备路径
            dev_match = re.match(r"add device \d+: (.*)", line)
            if dev_match:
                current_device = dev_match.group(1)
            
            # 匹配名称 (Pico 4 Ultra 通常包含 Pico Controller)
            if current_device and "name:" in line and "Pico" in line:
                name = line.split('"')[1]
                # 简单区分左右 (根据实际情况可能需要调整匹配字符)
                side = "Left" if "Left" in name or "L" in name else "Right"
                devices[side] = current_device
        
        return devices
    except Exception as e:
        print(f"获取设备失败: {e}")
        return {}

def monitor_event(device_path, side):
    """实时监控并解析 getevent 输出"""
    print(f"开始监控 {side} 手柄: {device_path}")
    
    # -lt: l 是显示标签名称, t 是增加时间戳
    cmd = ["adb", "shell", "getevent", "-lt", device_path]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    try:
        for line in process.stdout:
            # 格式解析: [时间戳] 类型 代码 值
            # 例子: [ 12345.678] EV_KEY       BTN_A                DOWN
            match = re.search(r"(\w+)\s+(\w+)\s+(\w+)", line)
            if match:
                ev_type, ev_code, ev_value = match.groups()
                
                # 处理按键事件
                if ev_type == "EV_KEY":
                    state = "Pressed" if ev_value == "DOWN" else "Released"
                    print(f"[{side}] Button: {ev_code} -> {state}")
                
                # 处理摇杆和模拟量 (ABS)
                elif ev_type == "EV_ABS":
                    # ABS_X/Y 为摇杆, ABS_GAS 为扳机, ABS_BRAKE 为抓握
                    print(f"[{side}] Axis: {ev_code} -> Value: {ev_value}")
                    
    except KeyboardInterrupt:
        process.terminate()
        print("
监控停止")

if __name__ == "__main__":
    pico_devices = get_pico_event_paths()
    
    if not pico_devices:
        print("未发现 Pico 手柄。请确保：")
        print("1. Pico 已连接且开启了 ADB 调试")
        print("2. 运行了 'adb devices' 确认可见")
        sys.exit(1)

    print("发现手柄设备:")
    for side, path in pico_devices.items():
        print(f" - {side}: {path}")

    # 默认监控发现的第一个设备，或者可以修改为多线程监控两个
    first_side = list(pico_devices.keys())[0]
    monitor_event(pico_devices[first_side], first_side)
