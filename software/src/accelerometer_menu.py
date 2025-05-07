from menu import Menu
from badgeio import display
from machine import I2C, Pin
from sysfont import sysfont

ADDR = 0x0F

CHIP_ID = 0x00
XOUT1 = 0x02
YOUT1 = 0x04
ZOUT1 = 0x06
RANGESEL = 0x0F
POWMODE = 0x11
SWRST = 0x14


class AccelerometerMenu(Menu):
    def __init__(self) -> None:
        i2c = I2C(0, scl=Pin(21), sda=Pin(33), freq=100000)
        scanned = i2c.scan()
        if ADDR not in scanned:
            print("Accelerometer device not found on I2C bus.")
            return
        self.i2c = i2c

    def on_focus(self):
        display.fill()

        # reset
        self.i2c.writeto_mem(ADDR, SWRST, bytes([0xb6]))
        # check chip id
        chip_id = self.i2c.readfrom_mem(ADDR, CHIP_ID, 1)
        print(f'Chip ID: {chip_id[0]:08b}')
        # check mode
        mode = self.i2c.readfrom_mem(ADDR, POWMODE, 1)
        print(f'Mode: {mode[0]:08b}')
        # set range and
        self.i2c.writeto_mem(ADDR, RANGESEL, bytes([0x8]))
        accel_range = self.i2c.readfrom_mem(ADDR, RANGESEL, 1)
        print(f'Range: {accel_range[0]:08b}')

    def tick(self):
        self.raw_x = self.i2c.readfrom_mem(ADDR, XOUT1, 2)
        self.raw_y = self.i2c.readfrom_mem(ADDR, YOUT1, 2)
        self.raw_z = self.i2c.readfrom_mem(ADDR, ZOUT1, 2)
        # acceleration is 12 bits
        self.accel_x = ((self.raw_x[0] & 0xF0) >> 4) | (self.raw_x[1] << 4)
        self.accel_y = ((self.raw_y[0] & 0xF0) >> 4) | (self.raw_y[1] << 4)
        self.accel_z = ((self.raw_z[0] & 0xF0) >> 4) | (self.raw_z[1] << 4)
        # correct signs
        self.accel_x = (self.accel_x ^ 0x800) - 0x800
        self.accel_y = (self.accel_y ^ 0x800) - 0x800
        self.accel_z = (self.accel_z ^ 0x800) - 0x800
        # get new
        self.new_x = self.raw_x[0] & 0x1
        self.new_y = self.raw_y[0] & 0x1
        self.new_z = self.raw_z[0] & 0x1

    def draw(self):
        display.text(
            (5, 5), (f'X: {self.accel_x} ({self.new_x})     '), display.WHITE, sysfont)
        display.text(
            (5, 5 + sysfont["Height"]), (f'   ({self.accel_x:012b})'), display.WHITE, sysfont)
        display.text(
            (5, 5 + sysfont["Height"] * 2), (f'Y: {self.accel_y} ({self.new_y})     '), display.WHITE, sysfont)
        display.text(
            (5, 5 + sysfont["Height"] * 3), (f'   ({self.accel_y:012b})'), display.WHITE, sysfont)
        display.text(
            (5, 5 + sysfont["Height"] * 4), (f'Z: {self.accel_z} ({self.new_z})     '), display.WHITE, sysfont)
        display.text(
            (5, 5 + sysfont["Height"] * 5), (f'   ({self.accel_z:012b})'), display.WHITE, sysfont)
