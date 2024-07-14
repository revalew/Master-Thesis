import socket  # Library for socket programming
import time  # Library for time-related functions

import network  # importing network
import gc

import uasyncio as asyncio

from machine import Pin, ADC  # Importing specific classes from the machine module

# Initializing onboard LED and temperature sensor
onboard_led = Pin("LED", Pin.OUT, value=0)  # GPIO pin for onboard LED
temperature_sensor = ADC(4)  # GPIO 4 is connected to the temperature sensor

gc.collect()


def setup_ap():
    ssid = "Kisiel MasterThesis RPiPico"  # Set access point name
    password = "myMasterThesis"  # Set your access point password

    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)

    ap.active(True)  # activating
    ap.config(pm=0xA11140)  # Disable power-save mode

    while ap.active() == False:
        pass

    print("Successfully started AP")
    print(ap.ifconfig())


def web_page():
    html = """
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                h1 {
                    margin-top: 30px;
                    text-align: center;
                }

                p {
                    text-align: center;
                }

                a {
                    text-decoration: none;
                    color: royalblue;
                }
            </style>
        </head>
        <body>
            <h1>Welcome to the HEXAPOD Project Webpage!</h1>
            <p>Come visit our GitHub at: <a href="https://github.com/revalew/HEXAPOD" target="_blank">HEXAPOD</a>!</p>
        </body>
    </html>"""
    return html


# Asynchronous function to handle client requests
async def handle_client(reader, writer):
    print("Client connected")  # Print message when client is connected
    request_line = await reader.readline()  # Read the HTTP request line
    print("Request:", request_line)  # Print the received request
    # Skip HTTP request headers
    while await reader.readline() != b"\r\n":
        pass

    response = web_page()

    writer.write(
        "HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n"
    )  # Write HTTP response header
    writer.write(response)  # Write HTML response

    await writer.drain()  # Drain the writer buffer
    await writer.wait_closed()  # Wait until writer is closed
    print("Client disconnected")  # Print message when client is disconnected


async def main():
    try:
        setup_ap()  # Start the Access Point

        asyncio.create_task(
            asyncio.start_server(handle_client, "0.0.0.0", 80)
        )  # Start the web server

        while True:  # Loop indefinitely
            await asyncio.sleep(0)  # Sleep for a short period

    except Exception as e:
        print(e)

    except KeyboardInterrupt:
        print("KeyboardInterrupt detected, closing the program")

    finally:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())

    finally:
        asyncio.new_event_loop()
