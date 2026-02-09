import socket
import struct
import asyncio
import websockets
import time
from collections import deque

# VSSP v1.0 Constants
VSSP_MAGIC = b"VSSP"
MAX_PAYLOAD = 1200
UDP_PORT = 8789
WS_PORT = 8790
THRESHOLD = 0.9


class FrameBuffer:
    def __init__(self, frame_id, eye, packet_count, mode):
        self.frame_id = frame_id
        self.eye = eye
        self.packet_count = packet_count
        self.mode = mode
        self.received_mask = [False] * packet_count
        self.data = [None] * packet_count
        self.received_count = 0
        self.last_update = time.time()


class VSSP_Relay:
    def __init__(self):
        self.frames = {}  # Key: (frame_id, eye)
        self.ws_clients = set()
        self.latest_frame_id = -1

    async def udp_receiver(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", UDP_PORT))
        sock.setblocking(False)
        print(f"[VSSP] UDP Server listening on {UDP_PORT}")

        loop = asyncio.get_event_loop()
        while True:
            data, addr = await loop.sock_recvfrom(sock, 2048)
            if len(data) < 24:
                continue

            # Parse Header (24 bytes, little-endian)
            magic = data[0:4]
            if magic != VSSP_MAGIC:
                continue

            header = struct.unpack("<IIBBBBHHHH I", data[0:24])
            # Header indices: 0:magic, 1:frame_id, 2:mode, 3:eye, 4:codec, 5:flags,
            # 6:packet_id, 7:packet_count, 8:payload_size, 9:timestamp_ms
            _, frame_id, mode, eye, codec, flags, p_id, p_count, p_size, ts = header
            payload = data[24 : 24 + p_size]

            # Cleanup old frames
            now = time.time()
            if len(self.frames) > 20:
                self.frames = {
                    k: v for k, v in self.frames.items() if now - v.last_update < 0.1
                }

            key = (frame_id, eye)
            if key not in self.frames:
                self.frames[key] = FrameBuffer(frame_id, eye, p_count, mode)

            fb = self.frames[key]
            if not fb.received_mask[p_id]:
                fb.received_mask[p_id] = True
                fb.data[p_id] = payload
                fb.received_count += 1
                fb.last_update = now

            # Check completion (THRESHOLD = 0.9)
            if fb.received_count >= fb.packet_count * THRESHOLD:
                # Assemble frame
                full_frame = b"".join([p if p else b"" for p in fb.data])
                await self.broadcast_frame(full_frame, mode, eye)
                # Mark as handled to avoid double send
                fb.received_count = -99999

    async def broadcast_frame(self, data, mode, eye):
        if not self.ws_clients:
            return

        # Web Relay Format (per spec 11.1)
        # offset 0: size(4), 4: mode(1), 5: eye(1), 6: data(N)
        header = struct.pack("<IBB", len(data), mode, eye)
        packet = header + data

        tasks = [asyncio.create_task(client.send(packet)) for client in self.ws_clients]
        if tasks:
            await asyncio.wait(tasks)

    async def ws_handler(self, websocket, path):
        self.ws_clients.add(websocket)
        print(f"[VSSP] Web Client Connected. Total: {len(self.ws_clients)}")
        try:
            await websocket.wait_closed()
        finally:
            self.ws_clients.remove(websocket)


async def main():
    relay = VSSP_Relay()
    await asyncio.gather(
        relay.udp_receiver(), websockets.serve(relay.ws_handler, "0.0.0.0", WS_PORT)
    )


if __name__ == "__main__":
    asyncio.run(main())
