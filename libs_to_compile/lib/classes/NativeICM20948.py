import micropython
import time

# from machine import I2C, Pin

# ICM20948 constants
ICM20948_WHO_AM_I = 0x00
ICM20948_PWR_MGMT_1 = 0x06
ICM20948_ACCEL_XOUT_H = 0x2D
ICM20948_GYRO_XOUT_H = 0x33
ICM20948_REG_BANK_SEL = 0x7F
ICM20948_ACCEL_SMPLRT_DIV_1 = 0x10
ICM20948_ACCEL_SMPLRT_DIV_2 = 0x11
ICM20948_ACCEL_CONFIG_1 = 0x14
ICM20948_GYRO_SMPLRT_DIV = 0x00
ICM20948_GYRO_CONFIG_1 = 0x01

# Magnetometer constants (AK09916)
ICM20948_I2C_MST_STATUS = 0x17
ICM20948_EXT_SLV_SENS_DATA_00 = 0x3B
ICM20948_USER_CTRL = 0x03
ICM20948_I2C_MST_CTRL = 0x01
ICM20948_I2C_SLV0_ADDR = 0x03
ICM20948_I2C_SLV0_REG = 0x04
ICM20948_I2C_SLV0_CTRL = 0x05
ICM20948_I2C_SLV4_ADDR = 0x13
ICM20948_I2C_SLV4_REG = 0x14
ICM20948_I2C_SLV4_CTRL = 0x15
ICM20948_I2C_SLV4_DO = 0x16
ICM20948_I2C_SLV4_DI = 0x17

AK09916_CNTL2 = 0x31
AK09916_WIA2 = 0x01


class NativeICM20948:
    def __init__(self, i2c_bus, address=0x68, accel_div=0, gyro_div=0):
        self.i2c = i2c_bus
        self.addr = address
        self.setup_sensor(accel_div=accel_div, gyro_div=gyro_div)
        self.setup_magnetometer()

    def setup_sensor(self, accel_div=0, gyro_div=0):
        who_am_i = self.read_register(0, ICM20948_WHO_AM_I)
        if who_am_i != 0xEA:
            raise RuntimeError(f"ICM20948 not found, got 0x{who_am_i:02x}")

        # Wake up sensor
        self.write_register(0, ICM20948_PWR_MGMT_1, 0x01)
        time.sleep_ms(10)

        self.set_internal_rates(accel_div=accel_div, gyro_div=gyro_div)

    def set_internal_rates(self, accel_div=0, gyro_div=0):
        """Set internal sampling rates via divisors

        Accelerometer: 1125/(1+div) Hz, max 1125 Hz (div=0)
        Gyroscope: 1100/(1+div) Hz, max 1100 Hz (div=0)

        Args:
            accel_div: 0-4095, 0=max speed (1125 Hz)
            gyro_div: 0-255, 0=max speed (1100 Hz)
        """
        # Accelerometer divisor (16-bit, big endian)
        self.write_register(2, ICM20948_ACCEL_SMPLRT_DIV_1, (accel_div >> 8) & 0xFF)
        self.write_register(2, ICM20948_ACCEL_SMPLRT_DIV_2, accel_div & 0xFF)
        self.write_register(2, ICM20948_ACCEL_CONFIG_1, 0x14)  # ±8g, no DLPF

        # Gyroscope divisor (8-bit)
        self.write_register(2, ICM20948_GYRO_SMPLRT_DIV, gyro_div & 0xFF)
        self.write_register(2, ICM20948_GYRO_CONFIG_1, 0x0E)  # ±500dps, no DLPF

        # Calculate actual rates for logging
        accel_rate = 1125 / (1 + accel_div)
        gyro_rate = 1100 / (1 + gyro_div)
        # print(
        #     f"ICM20948 configured: Accel {accel_rate:.1f} Hz, Gyro {gyro_rate:.1f} Hz"
        # )

    def setup_magnetometer(self):
        # Enable I2C master
        self.write_register(0, ICM20948_USER_CTRL, 0x20)
        time.sleep_ms(10)

        # Configure I2C master
        self.write_register(3, ICM20948_I2C_MST_CTRL, 0x17)
        time.sleep_ms(10)

        # Configure magnetometer for continuous mode
        self.write_mag_register(AK09916_CNTL2, 0x08)  # 100Hz continuous
        time.sleep_ms(10)

        # Setup slave 0 for reading mag data
        self.write_register(3, ICM20948_I2C_SLV0_ADDR, 0x8C)  # AK09916 read
        self.write_register(3, ICM20948_I2C_SLV0_REG, 0x11)  # HXL register
        self.write_register(3, ICM20948_I2C_SLV0_CTRL, 0x89)  # Enable, 9 bytes

    def write_register(self, bank, reg, value):
        self.i2c.writeto_mem(self.addr, ICM20948_REG_BANK_SEL, bytes([bank << 4]))
        self.i2c.writeto_mem(self.addr, reg, bytes([value]))

    def read_register(self, bank, reg, length=1):
        self.i2c.writeto_mem(self.addr, ICM20948_REG_BANK_SEL, bytes([bank << 4]))
        data = self.i2c.readfrom_mem(self.addr, reg, length)
        return data[0] if length == 1 else data

    def write_mag_register(self, reg, value):
        self.write_register(3, ICM20948_I2C_SLV4_ADDR, 0x0C)
        self.write_register(3, ICM20948_I2C_SLV4_REG, reg)
        self.write_register(3, ICM20948_I2C_SLV4_DO, value)
        self.write_register(3, ICM20948_I2C_SLV4_CTRL, 0x80)
        time.sleep_ms(10)

    @micropython.native
    def read_acceleration_fast(self) -> tuple[float, float, float] | None:
        try:
            raw_data = self.i2c.readfrom_mem(self.addr, ICM20948_ACCEL_XOUT_H, 6)

            x_raw = (raw_data[0] << 8) | raw_data[1]
            y_raw = (raw_data[2] << 8) | raw_data[3]
            z_raw = (raw_data[4] << 8) | raw_data[5]

            if x_raw > 32767:
                x_raw -= 65536
            if y_raw > 32767:
                y_raw -= 65536
            if z_raw > 32767:
                z_raw -= 65536

            scale = 8.0 / 4096.0 * 9.80665
            return (x_raw * scale, y_raw * scale, z_raw * scale)
        except:
            return None

    @micropython.native
    def read_gyro_fast(self) -> tuple[float, float, float] | None:
        try:
            raw_data = self.i2c.readfrom_mem(self.addr, ICM20948_GYRO_XOUT_H, 6)

            x_raw = (raw_data[0] << 8) | raw_data[1]
            y_raw = (raw_data[2] << 8) | raw_data[3]
            z_raw = (raw_data[4] << 8) | raw_data[5]

            if x_raw > 32767:
                x_raw -= 65536
            if y_raw > 32767:
                y_raw -= 65536
            if z_raw > 32767:
                z_raw -= 65536

            scale = 500.0 / 65.5 * 0.017453293
            return (x_raw * scale, y_raw * scale, z_raw * scale)
        except:
            return None

    @micropython.native
    def read_magnetic_fast(self) -> tuple[float, float, float] | None:
        try:
            raw_data = self.read_register(0, ICM20948_EXT_SLV_SENS_DATA_00, 9)

            x_raw = (raw_data[1] << 8) | raw_data[0]
            y_raw = (raw_data[3] << 8) | raw_data[2]
            z_raw = (raw_data[5] << 8) | raw_data[4]

            if x_raw > 32767:
                x_raw -= 65536
            if y_raw > 32767:
                y_raw -= 65536
            if z_raw > 32767:
                z_raw -= 65536

            scale = 0.15
            return (x_raw * scale, y_raw * scale, z_raw * scale)
        except:
            return None

    @property
    def acceleration(self):
        return self.read_acceleration_fast()

    @property
    def gyro(self):
        return self.read_gyro_fast()

    @property
    def magnetic(self):
        return self.read_magnetic_fast()

    @micropython.native
    def read_all_fast(self) -> tuple[
        tuple[float, float, float] | None,
        tuple[float, float, float] | None,
        tuple[float, float, float] | None,
    ]:
        accel = self.read_acceleration_fast()
        gyro = self.read_gyro_fast()
        mag = self.read_magnetic_fast()
        return accel, gyro, mag
