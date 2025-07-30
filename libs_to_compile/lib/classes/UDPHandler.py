from asyncio import sleep

import socket
import struct

from .IoHandler import IoHandler


class UDPHandler:
    def __init__(self, host: str = "0.0.0.0", port: int = 12345) -> None:
        """
        Initializes a UDPHandler instance.

        Args:
            host (str): The host IP address to bind the UDP server to. Default is "0.0.0.0".
            port (int): The port number to bind the UDP server to. Default is 12345.

        Returns:
            None
        """
        # self.host = host
        # self.port = port

        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind((host, port))
        self.udp_sock.settimeout(0.001)  # Non-blocking

    async def handle_request(self) -> None:
        """
        Handles incoming UDP requests and sends sensor data back to the client.

        `<f18f3f` (1 float timestamp + 18 floats sensor data (9 each sensor) + 3 floats battery)

        | Symbol | Meaning | Bytes |
        |--------|-----------|-------------|
        | `<` | **Little-endian** byte order | - |
        | `f` | **1x float** (32-bit) | 4 bytes |
        | `18f` | **18x float** (32-bit each) | 72 bytes |
        | `3f` | **3x float** (32-bit each) | 12 bytes |

        Args:
            None

        Returns:
            None
        """
        while True:
            try:
                data, addr = self.udp_sock.recvfrom(64)
                # print({"data": data, "addr": addr})
                if data == b"GET":
                    # sensor_data = IoHandler.get_all_sensor_data_direct()
                    (
                        wav_a_1,
                        wav_a_2,
                        wav_a_3,
                        wav_g_1,
                        wav_g_2,
                        wav_g_3,
                        wav_m_1,
                        wav_m_2,
                        wav_m_3,
                        ada_a_1,
                        ada_a_2,
                        ada_a_3,
                        ada_g_1,
                        ada_g_2,
                        ada_g_3,
                        ada_m_1,
                        ada_m_2,
                        ada_m_3,
                        ups_voltage,
                        ups_current,
                        ups_percentage,
                    ) = IoHandler.get_all_sensor_data_direct()

                    # Pack to binary (much faster than JSON)
                    # response = struct.pack("<f18f3f", 0.0, *sensor_data)
                    response = struct.pack(
                        "<f18f3f",
                        0.0,
                        wav_a_1,
                        wav_a_2,
                        wav_a_3,
                        wav_g_1,
                        wav_g_2,
                        wav_g_3,
                        wav_m_1,
                        wav_m_2,
                        wav_m_3,
                        ada_a_1,
                        ada_a_2,
                        ada_a_3,
                        ada_g_1,
                        ada_g_2,
                        ada_g_3,
                        ada_m_1,
                        ada_m_2,
                        ada_m_3,
                        ups_voltage,
                        ups_current,
                        ups_percentage,
                    )

                    # sensor_data = IoHandler.get_all_sensor_data_cached()
                    # response = struct.pack(
                    #     "<f18f3f",
                    #     # timestamp
                    #     0.0,
                    #     # sensor1: accel(3) + gyro(3) + mag(3)
                    #     sensor_data["sensor1"]["accel"][0],
                    #     sensor_data["sensor1"]["accel"][1],
                    #     sensor_data["sensor1"]["accel"][2],
                    #     sensor_data["sensor1"]["gyro"][0],
                    #     sensor_data["sensor1"]["gyro"][1],
                    #     sensor_data["sensor1"]["gyro"][2],
                    #     sensor_data["sensor1"]["mag"][0],
                    #     sensor_data["sensor1"]["mag"][1],
                    #     sensor_data["sensor1"]["mag"][2],
                    #     # sensor2: accel(3) + gyro(3) + mag(3)
                    #     sensor_data["sensor2"]["accel"][0],
                    #     sensor_data["sensor2"]["accel"][1],
                    #     sensor_data["sensor2"]["accel"][2],
                    #     sensor_data["sensor2"]["gyro"][0],
                    #     sensor_data["sensor2"]["gyro"][1],
                    #     sensor_data["sensor2"]["gyro"][2],
                    #     sensor_data["sensor2"]["mag"][0],
                    #     sensor_data["sensor2"]["mag"][1],
                    #     sensor_data["sensor2"]["mag"][2],
                    #     # battery: voltage, current, percentage
                    #     sensor_data["battery"]["voltage"],
                    #     sensor_data["battery"]["current"],
                    #     sensor_data["battery"]["percentage"],
                    # )
                    self.udp_sock.sendto(response, addr)
            except:
                await sleep(0.001)
