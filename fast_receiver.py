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

# 存储所有设备状态
states = {
    "head": {"pos": None, "initial_pos": None, "euler": [0,0,0]},
    "left": {"pos": None, "initial_pos": None, "euler": [0,0,0], "btns": {}, "axes": [0,0]},
    "right": {"pos": None, "initial_pos": None, "euler": [0,0,0], "btns": {}, "axes": [0,0]}
}

def quat_to_euler(q):
    x, y, z, w = q['x'], q['y'], q['z'], q['w']
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    pitch = math.atan2(sinr_cosp, cosr_cosp)
    sinp = 2 * (w * y - z * x)
    yaw = math.asin(sinp) if abs(sinp) <= 1 else math.copysign(math.pi/2, sinp)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    roll = math.atan2(siny_cosp, cosy_cosp)
    return [math.degrees(pitch), math.degrees(yaw), math.degrees(roll)]

def print_ui():
    sys.stdout.write("\033[H") 
    sys.stdout.write("=== Pico 4 Ultra Motion Link (Full 6DOF) ===\n")
    sys.stdout.write("提示: 按下任一摇杆可重置 [全设备] 初始原点\n")
    sys.stdout.write("-" * 90 + "\n")
    
    for key in ["head", "left", "right"]:
        s = states[key]
        if s["pos"] and s["initial_pos"]:
            dx = s["pos"]["x"] - s["initial_pos"]["x"]
            dy = s["pos"]["y"] - s["initial_pos"]["y"]
            dz = s["pos"]["z"] - s["initial_pos"]["z"]
            
            if key == "head":
                line = f"{key.upper():5} | Pos:{dx:>6.2f},{dy:>6.2f},{dz:>6.2f} | Ang:{s['euler'][0]:>4.0f},{s['euler'][1]:>4.0f},{s['euler'][2]:>4.0f} | [HMD Tracking]\n"
            else:
                btns = s["btns"]
                trig = "T" if btns.get(0) else "_"
                grip = "G" if btns.get(1) else "_"
                b1 = ("X" if key=="left" else "A") if btns.get(4) else "_"
                b2 = ("Y" if key=="left" else "B") if btns.get(5) else "_"
                js_x, js_y = s["axes"][0], s["axes"][1]
                line = f"{key.upper():5} | Pos:{dx:>6.2f},{dy:>6.2f},{dz:>6.2f} | Ang:{s['euler'][0]:>4.0f},{s['euler'][1]:>4.0f},{s['euler'][2]:>4.0f} | [{trig}{grip}{b1}{b2}] | JS:({js_x:>5.2f},{js_y:>5.2f})\n"
            sys.stdout.write(line)
        else:
            sys.stdout.write(f"{key.upper():5} | 等待数据...\n")
    
    sys.stdout.write("-" * 90 + "\n")
    sys.stdout.flush()

@app.route('/', methods=['POST'])
def receive():
    try:
        data = json.loads(request.data.decode())
        dtype = data.get("type")
        
        if dtype == "head":
            key = "head"
        else:
            key = data.get("handedness")
            
        if key not in states: return '', 204
        
        pos = data.get("position")
        states[key]["pos"] = pos
        states[key]["euler"] = quat_to_euler(data.get("orientation"))
        
        if dtype == "controller":
            # 更新按键和轴
            btns_list = data.get("buttons", [])
            for i, b in enumerate(btns_list):
                states[key]["btns"][i] = b['pressed']
            states[key]["axes"] = data.get("axes", [0,0])

            # 如果点击摇杆，重置所有设备原点
            if states[key]["btns"].get(3):
                for k in states:
                    if states[k]["pos"]: states[k]["initial_pos"] = states[k]["pos"]

        # 首次初始化
        if states[key]["initial_pos"] is None:
            states[key]["initial_pos"] = pos

        # 转发 Unity
        unity_sender.sendto(request.data, ("127.0.0.1", UNITY_PORT))
        print_ui()
            
    except Exception:
        pass
    return '', 204

if __name__ == '__main__':
    sys.stdout.write("\033[2J\033[H")
    app.run(host='0.0.0.0', port=8765, threaded=True)