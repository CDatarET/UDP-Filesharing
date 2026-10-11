import socket
import os
import json
import struct

PORT = 5000
CHUNK_SIZE = 4000
TIMEOUT = 2
MAX_RETRIES = 10

server_ip = input("Enter server IP address: ")
file_path = input("Enter file path: ")

if not os.path.isfile(file_path):
    print("File not found!")
    raise SystemExit(1)

filename = os.path.basename(file_path)
filesize = os.path.getsize(file_path)

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.settimeout(TIMEOUT)
server = (server_ip, PORT)


def send_reliably(packet, expected_ack):
    for attempt in range(MAX_RETRIES):
        client.sendto(packet, server)

        try:
            while True:
                reply, address = client.recvfrom(4096)

                if address != server:
                    continue

                if reply == expected_ack:
                    return

        except socket.timeout:
            print(f"Retrying packet... ({attempt + 1})")

    raise TimeoutError("Server did not acknowledge packet")


try:
    metadata = json.dumps({
        "filename": filename,
        "filesize": filesize
    }).encode()

    client.sendto(b"START" + metadata, server)

    reply, _ = client.recvfrom(4096)
    if reply != b"READY":
        raise RuntimeError("Server did not accept the file")

    print(f"Sending {filename} ({filesize} bytes)...")

    seq = 0

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break

            packet = struct.pack("!I", seq) + chunk
            send_reliably(packet, struct.pack("!I", seq + 1))
            seq += 1

            print(f"Sent {min(seq * CHUNK_SIZE, filesize)}"
                  f"/{filesize} bytes", end="\r")

    reply, _ = client.recvfrom(4096)

    if reply == b"DONE":
        print(f"\nFile '{filename}' sent successfully!")
    else:
        print("\nUnexpected server response:", reply)

except (socket.timeout, TimeoutError, OSError, RuntimeError) as e:
    print("\nTransfer failed:", e)

finally:
    client.close()