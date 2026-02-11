from flask import Flask, request
import socket
import json
import sys
import logging
import math
import threading
import time

app = Flask(__name__)
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

UNITY_PORT = 9000
unity_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 存储设备状态
states = {
    "head": {
        "pos": None,
        "initial_pos": None,
        "euler": [0, 0, 0],
        "quat": [0, 0, 0, 1],
    },
    "left": {
        "pos": None,
        "initial_pos": None,
        "euler": [0, 0, 0],
        "quat": [0, 0, 0, 1],
        "btns": {},
        "axes": [0, 0],
    },
    "right": {
        "pos": None,
        "initial_pos": None,
        "euler": [0, 0, 0],
        "quat": [0, 0, 0, 1],
        "btns": {},
        "axes": [0, 0],
    },
}


def quat_to_euler(q):
    # q 可以是字典也可以是列表/元组
    if isinstance(q, dict):
        x, y, z, w = q["x"], q["y"], q["z"], q["w"]
    else:
        x, y, z, w = q
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    pitch = math.atan2(sinr_cosp, cosr_cosp)
    sinp = 2 * (w * y - z * x)
    yaw = math.asin(sinp) if abs(sinp) <= 1 else math.copysign(math.pi / 2, sinp)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    roll = math.atan2(siny_cosp, cosy_cosp)
    return [math.degrees(pitch), math.degrees(yaw), math.degrees(roll)]


def ui_thread():
    while True:
        sys.stdout.write("\033[H\033[J")
        sys.stdout.write(
            "============================================================================================================\n"
        )
        sys.stdout.write("   Pico 4 Ultra Motion Link (Full 6DOF Sync)\n")
        sys.stdout.write("   提示: 按下任一摇杆可重置 [全设备] 初始原点\n")
        sys.stdout.write(
            "============================================================================================================\n"
        )
        for key in ["head", "left", "right"]:
            s = states[key]
            if s["pos"] and s["initial_pos"]:
                dx, dy, dz = (
                    s["pos"]["x"] - s["initial_pos"]["x"],
                    s["pos"]["y"] - s["initial_pos"]["y"],
                    s["pos"]["z"] - s["initial_pos"]["z"],
                )

                # 格式化四元数显示
                q = s["quat"]
                quat_str = f"Q:({q[0]:>5.2f},{q[1]:>5.2f},{q[2]:>5.2f},{q[3]:>5.2f})"
                ang_str = f"A:({s['euler'][0]:>4.0f},{s['euler'][1]:>4.0f},{s['euler'][2]:>4.0f})"

                if key == "head":
                    line = f"{key.upper():5} | Pos: {dx:>6.2f}, {dy:>6.2f}, {dz:>6.2f} | {ang_str} | {quat_str} | [HMD]"
                else:
                    btns = s["btns"]
                    t, g = ("T" if btns.get(0) else "_"), ("G" if btns.get(1) else "_")
                    b1 = ("X" if key == "left" else "A") if btns.get(4) else "_"
                    b2 = ("Y" if key == "left" else "B") if btns.get(5) else "_"
                    line = f"{key.upper():5} | Pos: {dx:>6.2f}, {dy:>6.2f}, {dz:>6.2f} | {ang_str} | {quat_str} | JS:({s['axes'][0]:>5.2f}, {s['axes'][1]:>5.2f})"
                sys.stdout.write(line + "\n")
            else:
                sys.stdout.write(f"{key.upper():5} | 等待数据中...\n")
        sys.stdout.write(
            "============================================================================================================\n"
        )
        sys.stdout.flush()
        time.sleep(0.04)  # 稍微降低 UI 刷新频率以减少 CPU 占用


@app.route("/", methods=["POST"])
def receive():
    try:
        # 1. 解析原始数据
        raw_data = request.get_data()
        if not raw_data:
            return "", 240

        data = json.loads(raw_data.decode())
        dtype = data.get("type")
        key = "head" if dtype == "head" else data.get("handedness")

        if key not in states:
            return "", 204

        # 2. 提取并转换坐标系 (WebXR RH -> Unity LH)
        # WebXR: X+, Y+, Z- (forward is Z-)
        # Unity: X+, Y+, Z+ (forward is Z+)
        pos = data.get("position", {"x": 0, "y": 0, "z": 0})
        ori = data.get("orientation", {"x": 0, "y": 0, "z": 0, "w": 1})

        # 位置转换: Z 轴取反
        unity_pos = {
            "x": float(pos.get("x", 0)),
            "y": float(pos.get("y", 0)),
            "z": -float(pos.get("z", 0)),
        }

        # 四元数转换: Mirror across XY plane (Z inversion)
        # WebXR Quaternion (x,y,z,w) -> Unity (-x,-y,z,w)
        unity_ori = {
            "x": -float(ori.get("x", 0)),
            "y": -float(ori.get("y", 0)),
            "z": float(ori.get("z", 0)),
            "w": float(ori.get("w", 1)),
        }

        # 3. 更新服务器内部状态 (用于 console 显示)
        states[key]["pos"] = unity_pos
        states[key]["quat"] = [
            unity_ori["x"],
            unity_ori["y"],
            unity_ori["z"],
            unity_ori["w"],
        ]
        states[key]["euler"] = quat_to_euler(unity_ori)

        # 4. 构造发送给 Unity 的最终数据包 (确保是扁平的、直接的四元数)
        clean_data = {
            "type": dtype,
            "handedness": data.get("handedness", ""),
            "position": unity_pos,
            "orientation": unity_ori,
        }

        if dtype == "controller":
            clean_data["buttons"] = data.get("buttons", [])
            clean_data["axes"] = data.get("axes", [0, 0])

            # 更新 CLI 需要显示的状态
            for i, b in enumerate(clean_data["buttons"]):
                states[key]["btns"][i] = b["pressed"]
            states[key]["axes"] = clean_data["axes"]

            # 处理重置逻辑 (一般是按下菜单键/摇杆)
            # 检查按钮 3 (通常是 Joystick Click) 是否被按下
            if any(
                b.get("pressed") for i, b in enumerate(clean_data["buttons"]) if i == 3
            ):
                for k in states:
                    if states[k]["pos"]:
                        states[k]["initial_pos"] = states[k]["pos"]

        # 处理初始位置记录
        if states[key]["initial_pos"] is None:
            states[key]["initial_pos"] = states[key]["pos"]

        # 5. 发送处理后的 JSON 给 Unity
        message = json.dumps(clean_data).encode()
        unity_sender.sendto(message, ("127.0.0.1", UNITY_PORT))

    except Exception:
        # 忽略解析错误
        pass
    return "", 204


if __name__ == "__main__":
    threading.Thread(target=ui_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=8765, threaded=True)
