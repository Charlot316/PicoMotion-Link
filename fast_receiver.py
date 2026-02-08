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

# 存储手柄实时状态
ctrl_states = {
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
    """在终端固定位置打印双手数据"""
    # ANSI 序列：\033[H 回到顶端，\033[J 清除屏幕
    sys.stdout.write("\033[H") 
    sys.stdout.write("=== Pico 4 Ultra Motion Link (Active) ===\n")
    sys.stdout.write("提示: 按下摇杆(Joystick Click)可重置该手柄原点\n")
    sys.stdout.write("-" * 80 + "\n")
    
    for side in ["left", "right"]:
        s = ctrl_states[side]
        if s["pos"] and s["initial_pos"]:
            dx = s["pos"]["x"] - s["initial_pos"]["x"]
            dy = s["pos"]["y"] - s["initial_pos"]["y"]
            dz = s["pos"]["z"] - s["initial_pos"]["z"]
            
            # 按钮解析
            # 0:Trigger, 1:Grip, 3:Joystick, 4:Primary(A/X), 5:Secondary(B/Y)
            btns = s["btns"]
            trig = "T" if btns.get(0) else "_"
            grip = "G" if btns.get(1) else "_"
            b1 = ("X" if side=="left" else "A") if btns.get(4) else "_"
            b2 = ("Y" if side=="left" else "B") if btns.get(5) else "_"
            js_click = "Click" if btns.get(3) else "_____"
            
            # 摇杆轴
            jx, jy = s["axes"][0], s["axes"][1]
            
            line = f"{side.upper():5} | Pos:{dx:>6.2f},{dy:>6.2f},{dz:>6.2f} | Ang:{s['euler'][0]:>4.0f},{s['euler'][1]:>4.0f},{s['euler'][2]:>4.0f} | [{trig}{grip}{b1}{b2}] | JS:({jx:>5.2f},{jy:>5.2f}) {js_click}\n"
            sys.stdout.write(line)
        else:
            sys.stdout.write(f"{side.upper():5} | 等待连接...\n")
    
    sys.stdout.write("-" * 80 + "\n")
    sys.stdout.flush()

@app.route('/', methods=['POST'])
def receive():
    try:
        data = json.loads(request.data.decode())
        side = data.get("handedness")
        if side not in ctrl_states: return '', 204
        
        pos = data.get("position")
        quat = data.get("orientation")
        btns_list = data.get("buttons", [])
        axes = data.get("axes", [])
        
        # 更新状态
        ctrl_states[side]["pos"] = pos
        ctrl_states[side]["euler"] = quat_to_euler(quat)
        ctrl_states[side]["axes"] = axes
        
        # 转换按钮列表为字典
        for i, b in enumerate(btns_list):
            ctrl_states[side]["btns"][i] = b['pressed']

        # 检测摇杆点击 -> 复位
        if ctrl_states[side]["btns"].get(3): # 摇杆按下
            ctrl_states[side]["initial_pos"] = pos
            # 可以在这里加入旋转复位的逻辑（如果需要的话）
            
        # 自动初始化
        if ctrl_states[side]["initial_pos"] is None:
            ctrl_states[side]["initial_pos"] = pos

        # 转发
        unity_sender.sendto(request.data, ("127.0.0.1", UNITY_PORT))
        
        # 渲染 UI
        print_ui()
            
    except Exception:
        pass
    return '', 204

if __name__ == '__main__':
    # 先清一次屏
    sys.stdout.write("\033[2J\033[H")
    app.run(host='0.0.0.0', port=8765, threaded=True)
