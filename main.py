"""
Main program file

Here we:
    - set up the WiFi connection (Access Point or Station mode)
    - start the web server,
    - start the OLED update task (to display the IMU data live IF the screen is on),
    - start the UDP server.
"""

# import uasyncio as asyncio # type: ignore
import asyncio

import machine  # type: ignore
import gc

from classes import WiFiConnection, RequestHandler, IoHandler, UDPHandler


gc.enable()
gc.collect()

# create Access Point ('192.168.4.1', '255.255.255.0', '192.168.4.1', '0.0.0.0')
if not WiFiConnection.start_ap_mode():
    raise RuntimeError("Setting up Access Point failed")

# if not WiFiConnection.start_station_mode():
#     raise RuntimeError("Setting up Station mode failed")

# for prop in WiFiConnection().fullConfig:  # type: ignore
#     print(f"{prop}\n")


async def main() -> None:
    """
    Main function of the program.

    Initializes the asynchronous web server and OLED update task and UDP server.

    Args:
        None

    Returns:
        None
    """
    # Start HTTP server (keep existing, just in case?)
    handler = RequestHandler()
    asyncio.create_task(
        asyncio.start_server(handler.handle_request, host="0.0.0.0", port=80, backlog=1)
    )

    # Configure sensor INTERNAL sample rates BEFORE starting async tasks
    print_config = False
    # IoHandler.set_sample_rate(sample_rate=10, print_config=print_config) # 10 Hz
    # IoHandler.set_sample_rate(sample_rate=20, print_config=print_config) # 20 Hz
    # IoHandler.set_sample_rate(sample_rate=50, print_config=print_config)  # 50 Hz
    IoHandler.set_sample_rate(sample_rate=100, print_config=print_config) # 100 Hz
    # IoHandler.set_sample_rate(sample_rate=200, print_config=print_config) # 200 Hz
    # IoHandler.set_sample_rate(sample_rate=400, print_config=print_config) # 400 Hz
    # IoHandler.set_sample_rate(sample_rate=800, print_config=print_config) # 800 Hz
    # IoHandler.set_sample_rate(sample_rate=1000, print_config=print_config) # 1000 Hz

    # Start OLED update
    asyncio.create_task(IoHandler.update_oled())

    # UDP handler task
    udp_handler = UDPHandler()
    asyncio.create_task(udp_handler.handle_request())

    # counter = 0
    # while True:
    #     # if counter % 1000 == 0:
    #     if counter == 1000:
    #         gc.collect()
    #         # print(f"Allocated RAM: {gc.mem_alloc()}\nFree RAM: {gc.mem_free()}\n")  # type: ignore
    #         counter = 0

    #     counter += 1
    #     await asyncio.sleep(0.01)

    while True:
        gc.collect()
        await asyncio.sleep(99999)


if __name__ == "__main__":
    try:
        asyncio.run(main())  # Run the main asynchronous function

    except KeyboardInterrupt:
        from time import sleep

        print("Program interrupted by user.")

        IoHandler.oled.fill(0)  # Clear the display
        IoHandler.oled.text("KeyboardInterrupt", 0, 0)
        IoHandler.oled.text("Stopped", 35, 30)
        IoHandler.oled.show()
        sleep(2)
        IoHandler.oled.poweroff()

        machine.reset()

    except Exception as e:
        from time import sleep

        print(f"Error: {e}")

        IoHandler.oled.fill(0)  # Clear the display
        IoHandler.oled.text("Exception", 0, 0)
        IoHandler.oled.text("Error", 45, 30)
        IoHandler.oled.show()
        sleep(2)
        IoHandler.oled.poweroff()

        machine.reset()

    finally:
        asyncio.new_event_loop()  # Create a new event loop if needed
