from asyncio import sleep
import socket
import struct
import time
from .IoHandler import IoHandler


class UDPHandler:
    def __init__(self, host: str = "0.0.0.0", port: int = 12345) -> None:
        """Initializes a UDPHandler instance."""
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind((host, port))
        self.udp_sock.settimeout(0.001)

        self.client_addr = None
        self.control_lock = False  # Prevent timer/control interference

    def send_batch_to_client(self, batch_data):
        """Callback for high-speed sampler to send data"""
        if not self.client_addr or self.control_lock:
            return False

        try:
            self.udp_sock.sendto(batch_data, self.client_addr)
            return True
        except:
            return False

    async def handle_request(self) -> None:
        """
        Handles incoming UDP requests and sends sensor data back to the client.

        `<f18f3f` (1 float timestamp + 18 floats sensor data (9 each sensor) + 3 floats battery). Other formats are kinda self-explanatory - B for boolean, H for hex, I for int, etc.

        | Symbol | Meaning | Bytes |
        |--------|-----------|-------------|
        | `<` | **Little-endian** byte order | - |
        | `f` | **1x float** (32-bit) | 4 bytes |
        | `18f` | **18x float** (32-bit each) | 72 bytes |
        | `3f` | **3x float** (32-bit each) | 12 bytes |
        """
        while True:
            try:
                data, addr = self.udp_sock.recvfrom(64)

                # Set sampling rate commands
                if data == b"SET_RATE_25":
                    success = IoHandler.set_sampling_rate(25)
                    response = struct.pack("<B", 1 if success else 0)
                    self.udp_sock.sendto(response, addr)

                elif data == b"SET_RATE_50":
                    success = IoHandler.set_sampling_rate(50)
                    response = struct.pack("<B", 1 if success else 0)
                    self.udp_sock.sendto(response, addr)

                elif data == b"SET_RATE_100":
                    success = IoHandler.set_sampling_rate(100)
                    response = struct.pack("<B", 1 if success else 0)
                    self.udp_sock.sendto(response, addr)

                elif data == b"SET_RATE_200":
                    success = IoHandler.set_sampling_rate(200)
                    response = struct.pack("<B", 1 if success else 0)
                    self.udp_sock.sendto(response, addr)

                # Start high-speed sampling
                elif data == b"START":
                    self.control_lock = True  # Block timer callbacks

                    # Force stop any existing sampling first
                    IoHandler.stop_high_speed_sampling()
                    time.sleep_ms(100)  # Wait for timer to fully stop

                    # Clear any pending data in socket buffer
                    try:
                        while True:
                            self.udp_sock.recv(4096, socket.MSG_DONTWAIT)
                    except:
                        pass

                    # Initialize system if needed
                    if not IoHandler.high_speed_sampler:
                        IoHandler.initialize_high_speed_system()

                    self.client_addr = addr
                    success = IoHandler.start_high_speed_sampling(
                        self.send_batch_to_client
                    )

                    # print(f"start_sampling success = {success}")

                    # Send control response immediately
                    if success:
                        ack = struct.pack("<H", 0xACE)
                    else:
                        ack = struct.pack("<H", 0xFFFF)

                    self.udp_sock.sendto(ack, addr)

                    # Small delay before allowing data packets
                    time.sleep_ms(50)
                    self.control_lock = False  # Allow timer callbacks

                # Stop sampling
                elif data == b"STOP":
                    self.control_lock = True  # Block timer callbacks

                    IoHandler.stop_high_speed_sampling()
                    self.client_addr = None

                    time.sleep_ms(50)  # Wait for final packets

                    stats = IoHandler.get_sampling_stats()
                    response = struct.pack(
                        "<III",
                        stats.get("samples", 0),
                        stats.get("packets", 0),
                        stats.get("errors", 0),
                    )
                    self.udp_sock.sendto(response, addr)

                    self.control_lock = False

                # Get status
                elif data == b"STATUS":
                    stats = IoHandler.get_sampling_stats()
                    status = struct.pack(
                        "<BIIII",
                        1 if stats.get("active", False) else 0,
                        stats.get("rate", 0),
                        stats.get("samples", 0),
                        stats.get("packets", 0),
                        stats.get("errors", 0),
                    )
                    self.udp_sock.sendto(status, addr)

                # Single reading (for testing/compatibility)
                elif data == b"GET":
                    sensor_data = IoHandler.get_all_sensor_data_direct()

                    response = struct.pack(
                        "<f18f3f",
                        0.0,  # timestamp placeholder
                        # 21 floats total
                        sensor_data[0],
                        sensor_data[1],
                        sensor_data[2],
                        sensor_data[3],
                        sensor_data[4],
                        sensor_data[5],
                        sensor_data[6],
                        sensor_data[7],
                        sensor_data[8],
                        sensor_data[9],
                        sensor_data[10],
                        sensor_data[11],
                        sensor_data[12],
                        sensor_data[13],
                        sensor_data[14],
                        sensor_data[15],
                        sensor_data[16],
                        sensor_data[17],
                        sensor_data[18],
                        sensor_data[19],
                        sensor_data[20],
                    )
                    self.udp_sock.sendto(response, addr)

            except:
                await sleep(0.001)
