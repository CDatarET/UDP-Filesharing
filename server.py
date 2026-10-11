import socket
import os
import json
import struct

HOST = "0.0.0.0"
PORT = 5000
BUFFER_SIZE = 4096
SAVE_DIR = "received_files"

os.makedirs(SAVE_DIR, exist_ok=True)

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

print(f"UDP server listening on port {PORT}...")

while True:
    data, address = server.recvfrom(BUFFER_SIZE)

    if data.startswith(b"START"):
        try:
            info = json.loads(data[5:].decode())
            filename = os.path.basename(info["filename"])
            filesize = info["filesize"]

            path = os.path.join(SAVE_DIR, filename)
            f = open(path, "wb")

            received = 0
            expected_seq = 0

            server.sendto(b"READY", address)
            print(f"Receiving {filename} from {address}")

            while received < filesize:
                packet, address = server.recvfrom(BUFFER_SIZE)

                if len(packet) < 4:
                    continue

                seq = struct.unpack("!I", packet[:4])[0]
                chunk = packet[4:]

                if seq == expected_seq:
                    f.write(chunk)
                    received += len(chunk)
                    expected_seq += 1

                server.sendto(
                    struct.pack("!I", expected_seq), address
                )

            f.close()
            server.sendto(b"DONE", address)
            print(f"Saved file: {path}")

        except (ValueError, KeyError, OSError) as e:
            print("Transfer error:", e)