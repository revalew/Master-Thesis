# full demo with web control panel
# combines multi core and multi tasking

import uasyncio as asyncio  # type: ignore

import machine # type: ignore
import gc

from classes import WiFiConnection, RequestHandler

gc.enable()
gc.collect()

# create Access Point ('192.168.4.1', '255.255.255.0', '192.168.4.1', '0.0.0.0')
if not WiFiConnection.start_ap_mode():
    raise RuntimeError("Setting up Access Point failed")

# for prop in WiFiConnection().fullConfig:
#     print(f"{prop}\n")

async def main() -> None:
    handler = RequestHandler()
    asyncio.create_task(asyncio.start_server(handler.handle_request, "0.0.0.0", 80))  # type: ignore
    gc.collect()

    counter = 0
    while True:
        # if counter % 1000 == 0:
        if counter == 1000:
            gc.collect()
            print(f"Allocated RAM: {gc.mem_alloc()}\nFree RAM: {gc.mem_free()}\n")  # type: ignore
            counter = 0
        counter += 1
        await asyncio.sleep(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())  # Run the main asynchronous function

    except Exception as e:
        print(e)
        machine.reset()

    finally:
        asyncio.new_event_loop()  # Create a new event loop if needed
