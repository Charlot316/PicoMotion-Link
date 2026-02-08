import asyncio
import socket
import websockets
import threading
import os
import struct
import time

# 配置
TCP_PORT = 8786
WS_PORT = 8787
LOG_FILE = "video_streamer.log"

# 全局存储最新帧
latest_frame = None
frame_lock = threading.Lock()


def log(msg):
    t = time.strftime("%H:%M:%S", time.localtime())
    formatted_msg = f"[{t}] {msg}"
    print(formatted_msg)
    with open(LOG_FILE, "a") as f:
        f.write(formatted_msg + "\n")


def recv_all(sock, n):
    data = b""
    while len(data) < n:
        try:
            packet = sock.recv(n - len(data))
            if not packet:
                log(f"Recv failed: socket closed during recv_all (got {len(data)}/{n})")
                return None
            data += packet
        except Exception as e:
            log(f"Recv exception: {e}")
            return None
    return data


def tcp_receive_thread():
    global latest_frame
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_sock.bind(("0.0.0.0", TCP_PORT))
    except Exception as e:
        log(f"CRITICAL: Could not bind to port {TCP_PORT}: {e}")
        return

    server_sock.listen(5)
    log(f"TCP HD Video Server listening on {TCP_PORT}")

    while True:
        try:
            client_sock, addr = server_sock.accept()
            log(f"UNITY CONNECTED: {addr}")

            # 使用 TCP 流式读取
            # 协议: [0x42] [Length: 4 bytes big-endian] [Image Data]

            client_sock.settimeout(None)  # 禁用超时，避免 Unity 暂停时断连

            while True:
                # 1. 读这帧的总头：1 (magic) + 4 (len) = 5 bytes
                # 这样可以减少系统调用次数
                head_blob = recv_all(client_sock, 5)
                if not head_blob:
                    break

                magic = head_blob[0]
                if magic != 0x42:
                    log(
                        f"Protocol Error: Invalid Magic Byte {hex(magic)}. Reseting connection."
                    )
                    break

                img_len = struct.unpack(">I", head_blob[1:5])[0]

                # 2. 校验
                if img_len > 20_000_000:  # 20MB
                    log(f"Oversized frame: {img_len}")
                    break

                # 3. 读体
                img_data = recv_all(client_sock, img_len)
                if not img_data:
                    break

                # 4. 更新
                with frame_lock:
                    latest_frame = img_data
        except Exception as e:
            log(f"Stream Error: {e}")
        finally:
            client_sock.close()


async def video_server(websocket):
    log(f"WS Browser connected: {websocket.remote_address}")
    last_sent_frame = None
    try:
        while True:
            current_frame = None
            with frame_lock:
                current_frame = latest_frame
            if current_frame and current_frame != last_sent_frame:
                await websocket.send(current_frame)
                last_sent_frame = current_frame
            await asyncio.sleep(0.01)
    except websockets.exceptions.ConnectionClosed:
        log("WS Browser disconnected")


async def main():
    threading.Thread(target=tcp_receive_thread, daemon=True).start()
    log(f"WebSocket interface for PICO browser ready on ws://localhost:{WS_PORT}")
    async with websockets.serve(video_server, "0.0.0.0", WS_PORT):
        await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
