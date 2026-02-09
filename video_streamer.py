import asyncio
import socket
import websockets
import struct
import time
import os

# VSSP v1.0 Constants
VSSP_MAGIC = b"VSSP"
UDP_PORT = 8766
WS_PORT = 8787
THRESHOLD = 1.0
LOG_FILE = "vssp.log"


def log(msg):
    t = time.strftime("%H:%M:%S", time.localtime())
    formatted_msg = f"[{t}] {msg}"
    print(formatted_msg)
    with open(LOG_FILE, "a") as f:
        f.write(formatted_msg + "\n")


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
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)

    async def udp_receiver(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Increase UDP buffer for macOS
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
        sock.bind(("0.0.0.0", UDP_PORT))
        sock.setblocking(False)
        log(f"VSSP UDP Listener active on {UDP_PORT}")

        loop = asyncio.get_event_loop()
        packet_count_debug = 0
        while True:
            try:
                data, addr = await loop.sock_recvfrom(sock, 2048)
                packet_count_debug += 1
                if packet_count_debug % 100 == 0:
                    log(f"Received {packet_count_debug} UDP packets from {addr}")

                if len(data) < 24:
                    continue

                magic = data[0:4]
                if magic != VSSP_MAGIC:
                    continue

                # VSSP Header: 4(magic), 4(frame_id), 1(mode), 1(eye), 1(codec), 1(flags), 2(p_id), 2(p_count), 2(p_size), 4(timestamp) = 22 bytes
                # The remaining 2 bytes in [0:24] are alignment padding.
                header = struct.unpack("<IIBBBBHHHI", data[0:22])
                _, frame_id, mode, eye, codec, flags, p_id, p_count, p_size, ts = header
                payload = data[24 : 24 + p_size]

                # Cleanup old frames cache
                now = time.time()
                if len(self.frames) > 30:
                    self.frames = {
                        k: v
                        for k, v in self.frames.items()
                        if now - v.last_update < 0.2
                    }

                key = (frame_id, eye)
                if key not in self.frames:
                    self.frames[key] = FrameBuffer(frame_id, eye, p_count, mode)

                fb = self.frames[key]
                if p_id < fb.packet_count and not fb.received_mask[p_id]:
                    fb.received_mask[p_id] = True
                    fb.data[p_id] = payload
                    fb.received_count += 1
                    fb.last_update = now

                # Check completion logic
                if fb.received_count == fb.packet_count:
                    log(
                        f"Frame {frame_id} (Eye {eye}) COMPLETE. Packets: {fb.received_count}/{fb.packet_count}. Size: {sum(len(x) for x in fb.data if x)} bytes"
                    )
                    # Assemble and push to web clients
                    full_frame = b"".join([p for p in fb.data if p])
                    await self.broadcast_frame(full_frame, mode, eye, codec)
                    fb.received_count = -99999
            except Exception:
                pass

    async def broadcast_frame(self, data, mode, eye, codec):
        log(
            f"Attempting to broadcast frame (mode={mode}, eye={eye}, codec={codec}, size={len(data)}) to {len(self.ws_clients)} clients."
        )
        if not self.ws_clients:
            return
        # Custom Web Relay Packet: [size:4][mode:1][eye:1][codec:1][payload]
        header = struct.pack("<IBBB", len(data), mode, eye, codec)
        packet = header + data

        # Concurrent broadcast
        disconnected = set()
        for client in list(self.ws_clients):
            try:
                await client.send(packet)
            except Exception:
                disconnected.add(client)
        for d in disconnected:
            self.ws_clients.discard(d)

    async def ws_handler(self, websocket, path=None):
        self.ws_clients.add(websocket)
        log(f"Browser connected to VSSP Stream. Active clients: {len(self.ws_clients)}")
        try:
            await websocket.wait_closed()
        finally:
            self.ws_clients.discard(websocket)


async def main():
    relay = VSSP_Relay()
    log("Starting VSSP v1.0 Unified Relay (UDP -> WS)")
    async with websockets.serve(relay.ws_handler, "0.0.0.0", WS_PORT):
        await relay.udp_receiver()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
