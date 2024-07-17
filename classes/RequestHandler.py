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
                action = request.get_action()
                gc.collect()
                if action == "AdaReadIMU":
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
                        IoHandler.get_accel_ada_reading()
                    )
                    gc.collect()
                    gyro["X"], gyro["Y"], gyro["Z"] = IoHandler.get_gyro_ada_reading()
                    gc.collect()
                    magnetic["X"], magnetic["Y"], magnetic["Z"] = (
                        IoHandler.get_magnetic_ada_reading()
                    )
                    gc.collect()
                    response_obj = {
                        "status": "OK",
                        "acceleration": acceleration,
                        "gyro": gyro,
                        "magnetic": magnetic,
                    }
                    response_builder.set_body_from_dict(response_obj)
                elif action == "WavReadIMU":
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
                        IoHandler.get_accel_wav_reading()
                    )
                    gc.collect()
                    gyro["X"], gyro["Y"], gyro["Z"] = IoHandler.get_gyro_wav_reading()
                    gc.collect()
                    magnetic["X"], magnetic["Y"], magnetic["Z"] = (
                        IoHandler.get_magnetic_wav_reading()
                    )
                    gc.collect()
                    response_obj = {
                        "status": "OK",
                        "acceleration": acceleration,
                        "gyro": gyro,
                        "magnetic": magnetic,
                    }
                    response_builder.set_body_from_dict(response_obj)
                elif action == "getBatteryInfo":
                    battery_percentage, battery_voltage = (
                        IoHandler.get_ups_battery_reading()
                    )
                    gc.collect()
                    battery_current = IoHandler.get_ups_current_reading()
                    gc.collect()
                    response_obj = {
                        "status": "OK",
                        "battery_voltage": battery_voltage,
                        "battery_current": battery_current,
                        "battery_percentage": battery_percentage,
                    }
                    response_builder.set_body_from_dict(response_obj)
                # elif action == "getPressureInfo":
                #     pressure = IoHandler.get_pressure_wav_reading()
                #     gc.collect()
                #     temperature = IoHandler.get_temp_wav_reading()
                #     gc.collect()
                #     response_obj = {
                #         "status": "OK",
                #         "pressure": pressure,
                #         "temperature": temperature,
                #     }
                #     response_builder.set_body_from_dict(response_obj)
                else:
                    # unknown action
                    response_builder.set_status(404)

            # try to serve static file
            else:
                response_builder.serve_static_file(request.url, "./src/index.html")

            response_builder.build_response()
            writer.write(response_builder.response)
            await writer.drain()
            await writer.wait_closed()
            gc.collect()

        except OSError as e:
            print("connection error " + str(e.errno) + " " + str(e))
