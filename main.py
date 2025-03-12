# full demo with web control panel
# combines multi core and multi tasking

# import uasyncio as asyncio # type: ignore
import asyncio

import machine # type: ignore
import gc

from classes import WiFiConnection, RequestHandler, IoHandler

gc.enable()
gc.collect()

# create Access Point ('192.168.4.1', '255.255.255.0', '192.168.4.1', '0.0.0.0')
if not WiFiConnection.start_ap_mode():
    raise RuntimeError("Setting up Access Point failed")

# for prop in WiFiConnection().fullConfig:
#     print(f"{prop}\n")


async def main() -> None:
    """
    Main function of the program.

    Initializes the asynchronous web server and OLED update task.

    This function runs an infinite loop that calls the garbage collector
    every 1000 iterations to free up unused memory.

    Args:
        None

    Returns:
        None
    """
    # Start web server
    handler = RequestHandler()
    asyncio.create_task(asyncio.start_server(handler.handle_request, "0.0.0.0", 80))  # type: ignore

    # Start OLED update
    asyncio.create_task(IoHandler.update_oled())

    gc.collect()

    counter = 0
    while True:
        # if counter % 1000 == 0:
        if counter == 1000:
            gc.collect()
            # print(f"Allocated RAM: {gc.mem_alloc()}\nFree RAM: {gc.mem_free()}\n")  # type: ignore
            counter = 0
        counter += 1
        await asyncio.sleep(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())  # Run the main asynchronous function

    except KeyboardInterrupt:
        print("Program interrupted by user.")
        IoHandler.oled.fill(0)  # Clear the display
        IoHandler.oled.text("Stopped", 35, 30)
        IoHandler.oled.show()
        IoHandler.oled.poweroff()
        machine.reset()
    
    except Exception as e:
        print(f"Error: {e}")
        IoHandler.oled.fill(0)  # Clear the display
        IoHandler.oled.text("Error", 45, 30)
        IoHandler.oled.show()
        # asyncio.sleep(2)  # Leave the error message on the screen before restarting
        machine.reset()

    finally:
        asyncio.new_event_loop()  # Create a new event loop if needed
