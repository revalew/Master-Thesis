"""
1. Use global variables as much as possible. Try to avoid creating local variables, specially on Core 1. Remember the problem is memory related so be conscious about how you use the memory and where memory could leak.
2. Use const() for integer variables that will not change ever
3. Use the thread lock to manipulate variables that could be manipulated on both cores
4. Use the gc (garbage collector) module to manually collect memory. Using gc.mem_free() you can check if memory is leaking. You can use gc.collect() in either of the two main loops. If for some reason you need to use it in both cores, use locks.

Example code (could be used as a template):
"""

import _thread, gc

variable = 0
core0_increment = const(1)
core1_increment = const(2)

lock = _thread.allocate_lock()


def main():  # This is the main loop running on Core 0
    global variable

    # check memory leakage
    #   print(gc.mem_free())
    print("This is core 0")
    gc.collect()

    #   ...

    lock.acquire()
    variable = variable + core0_increment
    lock.release()


#   ...


def second_thread():  # This is the main loop running on Core 1
    global variable

    while True:
        print("This is core 1")
        # Could also collect memory here
        # gc.collect()

        # ...

        lock.acquire()
        variable = variable + core1_increment
        lock.release()


_thread.start_new_thread(second_thread, ())

while True:
    main()



"""
import _thread
import time
from classes.IoHandler import IoHandler

def update_oled_thread():
    while True:
        IoHandler.oled.fill(0)
        IoHandler.oled.text("Battery:", 0, 0)

        battery_percentage, battery_voltage = IoHandler.get_ups_battery_reading()
        battery_current = IoHandler.get_ups_current_reading()

        IoHandler.oled.text(f"{battery_percentage:.1f}%", 0, 10)
        IoHandler.oled.text(f"{battery_voltage:.2f}V", 0, 20)
        IoHandler.oled.text(f"{battery_current:.2f}A", 0, 30)

        IoHandler.oled.show()
        time.sleep(2)  # Odśwież co 2 sekundy

# Uruchomienie wątku
_thread.start_new_thread(update_oled_thread, ())
"""