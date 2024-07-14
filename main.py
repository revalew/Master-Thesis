# full demo with web control panel
# combines multi core and multi tasking

import utime
import json
import uasyncio as asyncio
import random
import _thread
import machine

from classes.RequestParser import RequestParser
from classes.ResponseBuilder import ResponseBuilder
from classes.WiFiConnection import WiFiConnection
from classes.IoHandler import IoHandler

# create Access Point
if not WiFiConnection.start_ap_mode(True):
    raise RuntimeError("Setting up Access Point failed")


async def handle_request(reader, writer):
    try:
        raw_request = await reader.read(2048)

        request = RequestParser(raw_request)

        response_builder = ResponseBuilder()

        # filter out api request
        if request.url_match("/api"):
            action = request.get_action()
            if action == "readData":
                # ajax request for data
                onboard_led = IoHandler.get_onboard_led()
                temp_value = IoHandler.get_temp_reading()
                response_obj = {
                    "status": 0,
                    "onboard_led": onboard_led,
                    "temp_value": temp_value,
                }
                response_builder.set_body_from_dict(response_obj)
            elif action == "setLedColour":
                # turn on requested coloured led
                # returns json object with led states
                led_colour = request.data()["colour"]

                status = "OK"
                state = 0
                if led_colour == "on":
                    state = 1
                elif led_colour == "off":
                    # leave leds off
                    pass
                else:
                    status = "Error"
                IoHandler.set_onboard_led(state)
                response_obj = {"status": status, "onboard_led": state}
                response_builder.set_body_from_dict(response_obj)
            else:
                # unknown action
                response_builder.set_status(404)

        # try to serve static file
        else:
            response_builder.serve_static_file(request.url, "/api_index.html")

        response_builder.build_response()
        writer.write(response_builder.response)
        await writer.drain()
        await writer.wait_closed()

    except OSError as e:
        print("connection error " + str(e.errno) + " " + str(e))


async def main():
    print("Setting up webserver...")
    server = asyncio.start_server(handle_request, "0.0.0.0", 80)
    asyncio.create_task(server)

    # main async loop on first core
    # just pulse the red led
    counter = 0
    while True:
        # if counter % 500 == 0:
        #     IoHandler.toggle_onboard_led()
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
