# full demo with web control panel
# combines multi core and multi tasking

import uasyncio as asyncio

# import _thread
import machine
import gc

from classes.WiFiConnection import WiFiConnection
from classes.RequestHandler import RequestHandler

gc.enable()
gc.collect()

# create Access Point ('192.168.4.1', '255.255.255.0', '192.168.4.1', '0.0.0.0')
if not WiFiConnection.start_ap_mode():
    raise RuntimeError("Setting up Access Point failed")


async def main() -> None:
    # print("Setting up webserver...")
    # handler = RequestHandler()
    # asyncio.create_task(asyncio.start_server(handler.handle_request, "0.0.0.0", 80))
    asyncio.create_task(
        asyncio.start_server(RequestHandler().handle_request, "0.0.0.0", 80)
    )
    # print("WebServer started!\n\n")

    # main async loop on first core
    # counter = 0
    while True:
        # if counter % 1000 == 0:
        #     gc.collect()
        #     # print(gc.mem_free())
        # counter += 1
        await asyncio.sleep(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())  # Run the main asynchronous function

    except Exception as e:
        print(e)
        machine.reset()

    finally:
        asyncio.new_event_loop()  # Create a new event loop if needed
