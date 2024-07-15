from classes.RequestParser import RequestParser
from classes.ResponseBuilder import ResponseBuilder
from classes.IoHandler import IoHandler


class RequestHandler:
    def __init__(self):
        # get everything into a starting state
        pass

    # Asynchronous function to handle client requests
    async def handle_request(self, reader, writer):
        try:
            raw_request = await reader.read(1024)

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
                    onboard_led = 0
                    if led_colour == "on":
                        onboard_led = 1
                    elif led_colour == "off":
                        # leave leds off
                        pass
                    else:
                        status = "Error"
                    IoHandler.set_onboard_led(onboard_led)
                    response_obj = {"status": status, "onboard_led": onboard_led}
                    response_builder.set_body_from_dict(response_obj)
                else:
                    # unknown action
                    response_builder.set_status(404)

            # try to serve static file
            else:
                response_builder.serve_static_file(request.url, "/index.html")

            response_builder.build_response()
            writer.write(response_builder.response)
            await writer.drain()
            await writer.wait_closed()

        except OSError as e:
            print("connection error " + str(e.errno) + " " + str(e))
