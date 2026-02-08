import socket
import json
import sys

# 配置
UDP_IP = "0.0.0.0"
UDP_PORT = 8765
UNITY_PORT = 9000

initial_positions = {"left": None, "right": None}
udp_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_receiver.bind((UDP_IP, UDP_PORT))

# 预留给 Unity 的转发
unity_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def calculate_offset(current, initial):
    return {
        "x": round(current["x"] - initial["x"], 4),
        "y": round(current["y"] - initial["y"], 4),
        "z": round(current["z"] - initial["z"], 4)
    }

print(f"=== Pico 4 Ultra UDP 接收端 ===")
print(f"正在监听 UDP 端口: {UDP_PORT}")

try:
    while True:
        data, addr = udp_receiver.recvfrom(4096)
        try:
            payload = json.loads(data.decode())
            if payload.get("type") == "controller":
                side = payload.get("handedness")
                pos = payload.get("position")
                
                if initial_positions[side] is None:
                    initial_positions[side] = pos
                    print(f"\n[{side.upper()}] 已校准初始位置: {pos}")
                
                rel_pos = calculate_offset(pos, initial_positions[side])
                
                # 实时显示
                if side == "left":
                    sys.stdout.write(f"\r左手位移: X={rel_pos['x']:>7.4f}, Y={rel_pos['y']:>7.4f}, Z={rel_pos['z']:>7.4f} ")
                    sys.stdout.flush()

                # 转发给 Unity
                unity_sender.sendto(data, ("127.0.0.1", UNITY_PORT))
        except Exception as e:
            pass
except KeyboardInterrupt:
    print("\n停止服务")
