import uasyncio as asyncio
import machine

import ap

# import tft


def main():
    try:
        asyncio.run(ap.main())  # Run the main asynchronous function
    finally:
        asyncio.new_event_loop()  # Create a new event loop if needed


if __name__ == "__main__":
    try:
        main()

    except Exception as e:
        print(e)
        machine.reset()
