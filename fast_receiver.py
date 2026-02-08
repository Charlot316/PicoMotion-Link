from flask import Flask, request
import socket
import json
import sys
import logging
import math

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

UNITY_PORT = 9000
unity_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
initial_positions = {"left": None, "right": None}

def quat_to_euler(q):
    """将四元数转换为欧拉角 (degrees)"""
    x, y, z, w = q['x'], q['y'], q['z'], q['w']
    # pitch (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    pitch = math.atan2(sinr_cosp, cosr_cosp)
    # yaw (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    yaw = math.asin(sinp) if abs(sinp) <= 1 else math.copysign(math.pi/2, sinp)
    # roll (z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    roll = math.atan2(siny_cosp, cosy_cosp)
    
    return [math.degrees(pitch), math.degrees(yaw), math.degrees(roll)]

@app.route('/', methods=['POST'])
def receive():
    global initial_positions
    try:
        data_raw = request.data.decode()
        data = json.loads(data_raw)
        side = data.get("handedness")
        pos = data.get("position")
        quat = data.get("orientation")
        btns = data.get("buttons", [])
        axes = data.get("axes", [])
        
        if side not in initial_positions: return '', 204
        if initial_positions[side] is None:
            initial_positions[side] = pos
            print(f"\n[{side.upper()}] 初始位置已锚定")

        # 转发全量原始数据给 Unity
        unity_sender.sendto(request.data, ("127.0.0.1", UNITY_PORT))
        
        # 计算位移和角度
        dx = pos['x'] - initial_positions[side]['x']
        dy = pos['y'] - initial_positions[side]['y']
        dz = pos['z'] - initial_positions[side]['z']
        euler = quat_to_euler(quat)
        
        # 识别常用按键 (Pico 4 标准映射)
        # 0: Trigger, 1: Grip, 4: A/X, 5: B/Y, 3: Joystick Click
        trigger = btns[0]['pressed'] if len(btns) > 0 else False
        button_a = btns[4]['pressed'] if len(btns) > 4 else False
        
        # 实时打印：位移 | 角度 | 关键按键
        sys.stdout.write(f"\r{side:5}: Pos({dx:>5.2f},{dy:>5.2f},{dz:>5.2f}) | Ang({euler[0]:>4.0f},{euler[1]:>4.0f},{euler[2]:>4.0f}) | Trigger: {'ON ' if trigger else 'OFF'} | A: {'ON ' if button_a else 'OFF'} ")
        sys.stdout.flush()
            
    except Exception as e:
        pass
    return '', 204

if __name__ == '__main__':
    print("=== Pico 4 Ultra 全量数据接收器 ===")
    app.run(host='0.0.0.0', port=8765, threaded=True)