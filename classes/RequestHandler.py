from classes.RequestParser import RequestParser
from classes.ResponseBuilder import ResponseBuilder
from classes.IoHandler import IoHandler

import gc


class RequestHandler:
    def __init__(self) -> None:
        # get everything into a starting state
        gc.enable()
        gc.collect()
        pass

    # Asynchronous function to handle client requests
    @classmethod
    async def handle_request(cls, reader, writer) -> None:
        try:
            raw_request = await reader.read(1024)
            gc.collect()

            request = RequestParser(raw_request)

            response_builder = ResponseBuilder()

            # filter out api request
            if request.url_match("/api"):
                gc.collect()
                action = request.get_action()
                if action == "readData":
                    # ajax request for data
                    onboard_led = IoHandler.get_onboard_led()
                    temp_value = IoHandler.get_temp_reading()
                    response_obj = {
                        "status": "OK",
                        "onboard_led": onboard_led,
                        "temp_value": temp_value,
                    }
                    response_builder.set_body_from_dict(response_obj)
                elif action == "readIMU":
                    # ajax request for data
                    acceleration = {
                        "X": 0.0,
                        "Y": 0.0,
                        "Z": 0.0,
                    }
                    gyro = {
                        "X": 0.0,
                        "Y": 0.0,
                        "Z": 0.0,
                    }
                    magnetic = {
                        "X": 0.0,
                        "Y": 0.0,
                        "Z": 0.0,
                    }
                    acceleration["X"], acceleration["Y"], acceleration["Z"] = (
                        IoHandler.get_accel_reading()
                    )
                    gyro["X"], gyro["Y"], gyro["Z"] = IoHandler.get_gyro_reading()
                    magnetic["X"], magnetic["Y"], magnetic["Z"] = (
                        IoHandler.get_magnetic_reading()
                    )
                    response_obj = {
                        "status": "OK",
                        "acceleration": acceleration,
                        "gyro": gyro,
                        "magnetic": magnetic,
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
                response_builder.serve_static_file(request.url, "./index.html")

            response_builder.build_response()
            writer.write(response_builder.response)
            await writer.drain()
            await writer.wait_closed()
            gc.collect()

        except OSError as e:
            print("connection error " + str(e.errno) + " " + str(e))
