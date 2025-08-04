"""
Main program file

"""

import asyncio
import machine
import gc
from machine import freq

# Performance optimization
# (If you can't optimize the code - throw more compute at it?)
freq(240000000)
gc.threshold(32768)

from classes import WiFiConnection, RequestHandler, IoHandler, UDPHandler

gc.enable()
gc.collect()

if not WiFiConnection.start_ap_mode():
    raise RuntimeError("Setting up Access Point failed")


async def main() -> None:
    """
    Main function with unified high-speed sampling
    """
    handler = RequestHandler()
    asyncio.create_task(
        asyncio.start_server(handler.handle_request, host="0.0.0.0", port=80, backlog=1)
    )

    asyncio.create_task(IoHandler.update_oled())

    udp_handler = UDPHandler()
    asyncio.create_task(udp_handler.handle_request())

    # print("=== SYSTEM READY ===")
    # print("Default: Output 50 Hz")
    # print("Internal rates:")
    # print("  Waveshare (accel/gyro):")
    # print(f"    ICM20948 @ {IoHandler.ACCEL_WAV_HZ} / {IoHandler.GYRO_WAV_HZ} Hz")
    # print("  Adafruit (accel_gyro/mag):")
    # print(f"    LSM6DSOX @ {IoHandler.ACCEL_ADA_HZ} Hz")
    # print(f"    LIS3MDL @ {IoHandler.MAG_ADA_HZ} Hz")


    while True:
        gc.collect()
        await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("Program interrupted by user.")

        IoHandler.oled.fill(0)
        IoHandler.oled.text("KeyboardInterrupt", 0, 0)
        IoHandler.oled.text("Stopped", 35, 30)
        IoHandler.oled.show()

        import time

        time.sleep(2)
        IoHandler.oled.poweroff()
        machine.reset()

    except Exception as e:
        print(f"Error: {e}")

        IoHandler.oled.fill(0)
        IoHandler.oled.text("Exception", 0, 0)
        IoHandler.oled.text("Error", 45, 30)
        IoHandler.oled.show()

        import time

        time.sleep(2)
        IoHandler.oled.poweroff()
        machine.reset()

    finally:
        asyncio.new_event_loop()
