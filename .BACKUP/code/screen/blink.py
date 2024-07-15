
# tim = Timer()
# def tick(timer):
#     global led
#     led.toggle()
# tim.init(freq=2.5, mode=Timer.PERIODIC, callback=tick)
def main():
    try:
        from machine import Pin, Timer
        import neopixel
        from utime import sleep

        led = Pin(16, Pin.OUT) # 16 is the built-in single neopixel
        pixel = neopixel.NeoPixel(led, 1)

        print("LED starts flashing...")
        # while True:
        for i in range(5):
            sleep(1) # sleep 1sec
            pixel[0] = (255, 0, 0)
            pixel.write()
            sleep(1) # sleep 1sec
            pixel[0] = (0, 255, 0)
            pixel.write()
            sleep(1) # sleep 1sec
            pixel[0] = (0, 0, 255)
            pixel.write()

    except Exception as e:
        print(e)
        pixel[0] = (0, 0, 0)
        pixel.write()

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected.")
        pixel[0] = (0, 0, 0)
        pixel.write()

    finally:
        pixel[0] = (0, 0, 0)
        pixel.write()

if __name__ == "__main__":
    main()