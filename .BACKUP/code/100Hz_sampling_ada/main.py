"""
Test maximum speed of LSM6DSOX + LIS3MDL (Adafruit IMU 2)
Upload to Pico to test second sensor performance
"""

import time
import gc
from machine import freq

# Performance settings
freq(240000000)
gc.collect()

from board import GP6, GP7
from busio import I2C
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX as LSM6DS
from adafruit_lsm6ds import Rate
from adafruit_lis3mdl import LIS3MDL, Rate as MagRate

# Setup I2C
i2c = I2C(scl=GP7, sda=GP6, frequency=400000)

print("=== LSM6DSOX + LIS3MDL SPEED BENCHMARK ===")
print(f"CPU: {freq()} Hz")
print(f"I2C scan: {i2c.scan()}")

# Test 1: LSM6DSOX (Accelerometer + Gyroscope)
print("\n1. Testing LSM6DSOX (Accel + Gyro)...")
try:
    lsm6ds = LSM6DS(i2c)
    
    # Configure for maximum speed
    lsm6ds.accelerometer_data_rate = Rate.RATE_6_66K_HZ  # Max: 6.66 kHz
    lsm6ds.gyro_data_rate = Rate.RATE_6_66K_HZ  # Max: 6.66 kHz
    
    print(f"LSM6DSOX configured:")
    print(f"  Accel rate: {lsm6ds.accelerometer_data_rate}")
    print(f"  Gyro rate: {lsm6ds.gyro_data_rate}")
    
    # Speed test - accelerometer only
    print("Testing accelerometer speed...")
    start_time = time.ticks_ms()
    count = 0
    test_duration = 5000  # 5 seconds
    
    while time.ticks_diff(time.ticks_ms(), start_time) < test_duration:
        try:
            accel = lsm6ds.acceleration
            count += 1
        except:
            pass
    
    duration = time.ticks_diff(time.ticks_ms(), start_time)
    accel_rate = count * 1000 / duration
    accel_time_per_read = duration / count
    
    print(f"Accelerometer results:")
    print(f"  Rate: {accel_rate:.1f} Hz")
    print(f"  Time per read: {accel_time_per_read:.2f} ms")
    
    # Speed test - gyroscope only
    print("Testing gyroscope speed...")
    start_time = time.ticks_ms()
    count = 0
    
    while time.ticks_diff(time.ticks_ms(), start_time) < test_duration:
        try:
            gyro = lsm6ds.gyro
            count += 1
        except:
            pass
    
    duration = time.ticks_diff(time.ticks_ms(), start_time)
    gyro_rate = count * 1000 / duration
    gyro_time_per_read = duration / count
    
    print(f"Gyroscope results:")
    print(f"  Rate: {gyro_rate:.1f} Hz")
    print(f"  Time per read: {gyro_time_per_read:.2f} ms")
    
    # Speed test - both sensors
    print("Testing combined accel + gyro...")
    start_time = time.ticks_ms()
    count = 0
    
    while time.ticks_diff(time.ticks_ms(), start_time) < test_duration:
        try:
            accel = lsm6ds.acceleration
            gyro = lsm6ds.gyro
            count += 1
        except:
            pass
    
    duration = time.ticks_diff(time.ticks_ms(), start_time)
    combined_rate = count * 1000 / duration
    combined_time_per_read = duration / count
    
    print(f"Combined accel+gyro results:")
    print(f"  Rate: {combined_rate:.1f} Hz")
    print(f"  Time per read: {combined_time_per_read:.2f} ms")
    
except Exception as e:
    print(f"LSM6DSOX test failed: {e}")
    accel_rate = gyro_rate = combined_rate = 0

# Test 2: LIS3MDL (Magnetometer)
print(f"\n2. Testing LIS3MDL (Magnetometer)...")
try:
    lis3mdl = LIS3MDL(i2c)
    
    # Configure for maximum speed
    lis3mdl.data_rate = MagRate.RATE_1000_HZ  # Max: 1000 Hz
    
    print(f"LIS3MDL configured:")
    print(f"  Mag rate: {lis3mdl.data_rate}")
    
    # Speed test
    start_time = time.ticks_ms()
    count = 0
    test_duration = 5000
    
    while time.ticks_diff(time.ticks_ms(), start_time) < test_duration:
        try:
            mag = lis3mdl.magnetic
            count += 1
        except:
            pass
    
    duration = time.ticks_diff(time.ticks_ms(), start_time)
    mag_rate = count * 1000 / duration
    mag_time_per_read = duration / count
    
    print(f"Magnetometer results:")
    print(f"  Rate: {mag_rate:.1f} Hz")
    print(f"  Time per read: {mag_time_per_read:.2f} ms")
    
except Exception as e:
    print(f"LIS3MDL test failed: {e}")
    mag_rate = 0

# Test 3: All sensors combined
print(f"\n3. Testing ALL sensors (LSM6DSOX + LIS3MDL)...")
try:
    start_time = time.ticks_ms()
    count = 0
    test_duration = 5000
    
    while time.ticks_diff(time.ticks_ms(), start_time) < test_duration:
        try:
            accel = lsm6ds.acceleration
            gyro = lsm6ds.gyro
            mag = lis3mdl.magnetic
            count += 1
        except:
            pass
    
    duration = time.ticks_diff(time.ticks_ms(), start_time)
    all_sensors_rate = count * 1000 / duration
    all_sensors_time_per_read = duration / count
    
    print(f"All sensors (accel+gyro+mag) results:")
    print(f"  Rate: {all_sensors_rate:.1f} Hz")
    print(f"  Time per read: {all_sensors_time_per_read:.2f} ms")
    
except Exception as e:
    print(f"All sensors test failed: {e}")
    all_sensors_rate = 0

# Test 4: Different data rates
print(f"\n4. Testing different data rates...")
data_rates = [
    (Rate.RATE_52_HZ, "52 Hz"),
    (Rate.RATE_104_HZ, "104 Hz"), 
    (Rate.RATE_208_HZ, "208 Hz"),
    (Rate.RATE_416_HZ, "416 Hz"),
    (Rate.RATE_833_HZ, "833 Hz"),
    (Rate.RATE_1_66K_HZ, "1.66 kHz"),
    (Rate.RATE_3_33K_HZ, "3.33 kHz"),
    (Rate.RATE_6_66K_HZ, "6.66 kHz"),
]

print("Rate setting -> Actual performance:")
for rate_setting, rate_name in data_rates:
    try:
        lsm6ds.accelerometer_data_rate = rate_setting
        lsm6ds.gyro_data_rate = rate_setting
        time.sleep_ms(100)  # Let settings settle
        
        start_time = time.ticks_ms()
        count = 0
        test_duration = 2000  # 2 second test
        
        while time.ticks_diff(time.ticks_ms(), start_time) < test_duration:
            try:
                accel = lsm6ds.acceleration
                count += 1
            except:
                pass
        
        duration = time.ticks_diff(time.ticks_ms(), start_time)
        actual_rate = count * 1000 / duration
        efficiency = (actual_rate / float(rate_name.split()[0])) * 100 if rate_name.split()[0].replace('.', '').replace('k', '000').isdigit() else 0
        
        print(f"  {rate_name:>8} -> {actual_rate:6.1f} Hz actual")
        
    except Exception as e:
        print(f"  {rate_name:>8} -> ERROR: {e}")

# Summary
print(f"\n=== ADAFRUIT IMU SUMMARY ===")
if 'accel_rate' in locals() and 'gyro_rate' in locals() and 'mag_rate' in locals():
    print(f"LSM6DSOX Accelerometer: {accel_rate:.1f} Hz max")
    print(f"LSM6DSOX Gyroscope:     {gyro_rate:.1f} Hz max")
    print(f"LIS3MDL Magnetometer:   {mag_rate:.1f} Hz max")
    if 'combined_rate' in locals():
        print(f"LSM6DSOX Combined:      {combined_rate:.1f} Hz max")
    if 'all_sensors_rate' in locals():
        print(f"All sensors combined:   {all_sensors_rate:.1f} Hz max")
    
    # Determine bottleneck
    min_rate = min(accel_rate, gyro_rate, mag_rate) if 'mag_rate' in locals() and mag_rate > 0 else min(accel_rate, gyro_rate)
    print(f"\nBottleneck: {min_rate:.1f} Hz")
    
    if min_rate >= 100:
        print("SUCCESS: Adafruit IMU can achieve 100+ Hz!")
    elif min_rate >= 50:
        print("PARTIAL: Adafruit IMU can achieve 50+ Hz")
    else:
        print("LIMITATION: Adafruit IMU below 50 Hz")
        print("RECOMMENDATION: Use only fastest sensors or optimize further")

print(f"\n=== DATA VALIDATION ===")
if 'lsm6ds' in locals() and 'lis3mdl' in locals():
    try:
        accel = lsm6ds.acceleration
        gyro = lsm6ds.gyro
        mag = lis3mdl.magnetic
        print(f"Sample data:")
        print(f"  Accel: {accel[0]:6.2f}, {accel[1]:6.2f}, {accel[2]:6.2f} m/s²")
        print(f"  Gyro:  {gyro[0]:6.2f}, {gyro[1]:6.2f}, {gyro[2]:6.2f} rad/s")
        print(f"  Mag:   {mag[0]:6.2f}, {mag[1]:6.2f}, {mag[2]:6.2f} µT")
    except Exception as e:
        print(f"Data validation failed: {e}")