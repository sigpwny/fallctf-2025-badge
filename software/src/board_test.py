import machine
from machine import ADC, Pin, PWM, SPI, I2C, RTC
import espnow
import network

import math
import time
from time import sleep_ms
import gc


# initialize this first before we run out of memory
sta = network.WLAN(network.WLAN.IF_STA)
sta.active(True)
print('mac address:', sta.config('mac').hex())
esp = espnow.ESPNow()
esp.active(True)


from ST7735 import TFT, sysfont


class MyTFT:
    def __init__(self, scl, sda, cs, reset, rs, baudrate=10000000):
        self.spi = SPI(2, baudrate=baudrate, polarity=0, phase=0, sck=Pin(scl), mosi=Pin(sda))
        self.cs = Pin(cs, Pin.OUT)
        self.reset = Pin(reset, Pin.OUT)
        self.rs = Pin(rs, Pin.OUT)

    def do_reset(self):
        self.cs.on()
        sleep_ms(5)
        self.reset.off()
        sleep_ms(50)
        self.reset.on()
        sleep_ms(150)

    def write_cmd(self, cmd):
        self.cs.off()
        self.rs.off()
        self.spi.write(bytes([cmd]))
        self.cs.on()

    def write_data(self, data):
        self.cs.off()
        self.rs.on()
        if isinstance(data, int):
            self.spi.write(bytes([data]))
        elif isinstance(data, bytes):
            self.spi.write(data)
        else:
            raise ValueError("Data must be an int or bytes")
        self.cs.on()

    def init(self):
        self.do_reset()

        self.write_cmd(0x11)  # Exit Sleep
        sleep_ms(120)         # Delay 120ms

        # ST7735S Frame Rate
        self.write_cmd(0xB1)
        self.write_data(0x05)
        self.write_data(0x3C)
        self.write_data(0x3C)

        self.write_cmd(0xB2)
        self.write_data(0x05)
        self.write_data(0x3C)
        self.write_data(0x3C)

        self.write_cmd(0xB3)
        self.write_data(0x05)
        self.write_data(0x3C)
        self.write_data(0x3C)
        self.write_data(0x05)
        self.write_data(0x3C)
        self.write_data(0x3C)

        # End Frame Rate

        self.write_cmd(0xB4)  # Dot inversion
        self.write_data(0x03)

        # ST7735S Power Sequence
        self.write_cmd(0xC0)
        self.write_data(0x28)
        self.write_data(0x08)
        self.write_data(0x04)

        self.write_cmd(0xC1)
        self.write_data(0xC0)

        self.write_cmd(0xC2)
        self.write_data(0x0D)
        self.write_data(0x00)

        self.write_cmd(0xC3)
        self.write_data(0x8D)
        self.write_data(0x2A)

        self.write_cmd(0xC4)
        self.write_data(0x8D)
        self.write_data(0xEE)

        # End Power Sequence

        self.write_cmd(0xC5)  # VCOM
        self.write_data(0x05)

        self.write_cmd(0x36)  # MX, MY, RGB mode
        self.write_data(0xC0)

        # ST7735S Gamma Sequence
        self.write_cmd(0xE0)
        self.write_data(0x04)
        self.write_data(0x22)
        self.write_data(0x07)
        self.write_data(0x0A)
        self.write_data(0x2E)
        self.write_data(0x30)
        self.write_data(0x25)
        self.write_data(0x2A)
        self.write_data(0x28)
        self.write_data(0x26)
        self.write_data(0x2E)
        self.write_data(0x3A)
        self.write_data(0x00)
        self.write_data(0x01)
        self.write_data(0x03)
        self.write_data(0x13)

        self.write_cmd(0xE1)
        self.write_data(0x04)
        self.write_data(0x16)
        self.write_data(0x06)
        self.write_data(0x0D)
        self.write_data(0x2D)
        self.write_data(0x26)
        self.write_data(0x23)
        self.write_data(0x27)
        self.write_data(0x27)
        self.write_data(0x25)
        self.write_data(0x2D)
        self.write_data(0x3B)
        self.write_data(0x00)
        self.write_data(0x01)
        self.write_data(0x04)
        self.write_data(0x13)
        # End Gamma Sequence

        self.write_cmd(0x3A)  # 65k mode
        self.write_data(0x05)

        self.write_cmd(0x29)  # Display on

    def clear_screen(self, color):
        # Set the address window
        x0, x1, y0, y1 = 0, 127, 0, 159
        self.write_cmd(0x2A)
        self.write_data(x0 >> 8)
        self.write_data(x0)
        self.write_data(x1 >> 8)
        self.write_data(x1)
        self.write_cmd(0x2B)
        self.write_data(y0 >> 8)
        self.write_data(y0)
        self.write_data(y1 >> 8)
        self.write_data(y1)

        self.write_cmd(0x2C)  # Write to RAM
        # Fill the screen with the specified color
        color_bytes = bytes([color >> 8, color & 0xFF])
        for _ in range((x1 - x0 + 1) * (y1 - y0 + 1)):
            self.write_data(color_bytes)
        

# Initialize ADC on GPIO 10
adc_pin = Pin(10)
adc = ADC(adc_pin)

# adc.atten(ADC.ATTN_11DB)
adc.atten(ADC.ATTN_0DB)
ADC_ATTEN_VMAX = .75

ISENSE_GAIN = 50
ISENSE_RESISTOR = 0.1  # Ohm

buzzer = PWM(Pin(9))
buzzer.freq(1000)        # 1 kHz tone
buzzer.duty_u16(0)   # 50% duty cycle (range: 0–65535)

Pin(3, Pin.OUT).off() # ground the other pin of the buzzer

button = Pin(13, Pin.IN)

# LED controlled by MOSFET
lcd_led = PWM(Pin(41))
lcd_led.freq(1000)  # 1 kHz
lcd_led.duty_u16(int(.2 * 65535))

# tft = TFT(15, 16, 17, 18, 7)
# tft.init()
# tft.clear_screen(0x1234)

spi = SPI(2, baudrate=20000000, polarity=0, phase=0, sck=Pin(15), mosi=Pin(16))
tft = TFT(spi,7,18,17)
tft.rotation(3)  # Set rotation to 1 (landscape mode)
tft.initr()
tft.rgb(True)
tft.fill(TFT.BLACK)

def testlines(color):
    tft.fill(TFT.BLACK)
    for x in range(0, tft.size()[0], 6):
        tft.line((0,0),(x, tft.size()[1] - 1), color)
    for y in range(0, tft.size()[1], 6):
        tft.line((0,0),(tft.size()[0] - 1, y), color)

    tft.fill(TFT.BLACK)
    for x in range(0, tft.size()[0], 6):
        tft.line((tft.size()[0] - 1, 0), (x, tft.size()[1] - 1), color)
    for y in range(0, tft.size()[1], 6):
        tft.line((tft.size()[0] - 1, 0), (0, y), color)

    tft.fill(TFT.BLACK)
    for x in range(0, tft.size()[0], 6):
        tft.line((0, tft.size()[1] - 1), (x, 0), color)
    for y in range(0, tft.size()[1], 6):
        tft.line((0, tft.size()[1] - 1), (tft.size()[0] - 1,y), color)

    tft.fill(TFT.BLACK)
    for x in range(0, tft.size()[0], 6):
        tft.line((tft.size()[0] - 1, tft.size()[1] - 1), (x, 0), color)
    for y in range(0, tft.size()[1], 6):
        tft.line((tft.size()[0] - 1, tft.size()[1] - 1), (0, y), color)

def testfastlines(color1, color2):
    tft.fill(TFT.BLACK)
    for y in range(0, tft.size()[1], 5):
        tft.hline((0,y), tft.size()[0], color1)
    for x in range(0, tft.size()[0], 5):
        tft.vline((x,0), tft.size()[1], color2)

def testdrawrects(color):
    tft.fill(TFT.BLACK);
    for x in range(0,tft.size()[0],6):
        tft.rect((tft.size()[0]//2 - x//2, tft.size()[1]//2 - x/2), (x, x), color)

def testfillrects(color1, color2):
    tft.fill(TFT.BLACK);
    for x in range(tft.size()[0],0,-6):
        tft.fillrect((tft.size()[0]//2 - x//2, tft.size()[1]//2 - x/2), (x, x), color1)
        tft.rect((tft.size()[0]//2 - x//2, tft.size()[1]//2 - x/2), (x, x), color2)


def testfillcircles(radius, color):
    for x in range(radius, tft.size()[0], radius * 2):
        for y in range(radius, tft.size()[1], radius * 2):
            tft.fillcircle((x, y), radius, color)

def testdrawcircles(radius, color):
    for x in range(0, tft.size()[0] + radius, radius * 2):
        for y in range(0, tft.size()[1] + radius, radius * 2):
            tft.circle((x, y), radius, color)

def testtriangles():
    tft.fill(TFT.BLACK);
    color = 0xF800
    w = tft.size()[0] // 2
    x = tft.size()[1] - 1
    y = 0
    z = tft.size()[0]
    for t in range(0, 15):
        tft.line((w, y), (y, x), color)
        tft.line((y, x), (z, x), color)
        tft.line((z, x), (w, y), color)
        x -= 4
        y += 4
        z -= 4
        color += 100

def testroundrects():
    tft.fill(TFT.BLACK);
    color = 100
    for t in range(5):
        x = 0
        y = 0
        w = tft.size()[0] - 2
        h = tft.size()[1] - 2
        for i in range(17):
            tft.rect((x, y), (w, h), color)
            x += 2
            y += 3
            w -= 4
            h -= 6
            color += 1100
        color += 100

def test_main():
    tft.fillrect((0, 0), (130, 165), TFT.WHITE)
    tft.fillcircle((64, 80), 50, TFT.GREEN)
    while True: time.sleep(1)

    testdrawrects(TFT.GREEN)
    time.sleep_ms(500)

    testfillrects(TFT.YELLOW, TFT.PURPLE)
    time.sleep_ms(500)

    testlines(TFT.YELLOW)
    time.sleep_ms(500)

    testfastlines(TFT.RED, TFT.BLUE)
    time.sleep_ms(500)

    tft.fill(TFT.BLACK)
    testfillcircles(10, TFT.BLUE)
    testdrawcircles(10, TFT.WHITE)
    time.sleep_ms(500)

    testroundrects()
    time.sleep_ms(500)

    testtriangles()
    time.sleep_ms(500)


def test_accelerometer():
    # freq = 80000000
    freq = 80000000
    if machine.freq() != freq:
        machine.freq(freq)
    # https://atta.szlcsc.com/upload/public/pdf/source/20210108/C966924_A4D777CCA047E4BCE52C7136D49F7338.pdf

    # connect on I2C SCL pin 21, SDA pin 33
    i2c = I2C(0, scl=Pin(21), sda=Pin(33), freq=100000)
    scanned = i2c.scan()
    addr = 0x0f
    if addr not in scanned:
        print("Accelerometer device not found on I2C bus.")
        return

    # reset by writing 0xb6 to 0x14
    i2c.writeto_mem(addr, 0x14, b'\xb6')

    # read address 0 (CHIP_ID) to test if the device is connected
    # chip_id = i2c.readfrom_mem(addr, 0, 1)
    i2c.writeto(addr, bytes([0]))
    chip_id = i2c.readfrom(addr, 1)
    print(f'Chip ID: {chip_id[0]:08b}')

    mode = i2c.readfrom_mem(addr, 0x11, 1)
    print(f'Mode: {mode[0]:08b}')

    # for i in range(0, 0xFF):
    #     data = i2c.readfrom_mem(addr, i, 1)
    #     print(f'Address {i:02x}: {data[0]:08b}')

    # rangesel: +-2g
    i2c.writeto_mem(addr, 0x0f, bytes([0b0011]))
    # bwsel: 62.5Hz
    i2c.writeto_mem(addr, 0x10, bytes([0b01011]))

    tft.fillrect((0, 0), (130, 165), TFT.BLACK)

    def u12_to_s12(value):
        if value & 0x800:
            return value - 0x1000
        return value


    joystick_adc1 = ADC(Pin(4))
    joystick_adc1.atten(ADC.ATTN_11DB)
    joystick_adc2 = ADC(Pin(5))
    joystick_adc2.atten(ADC.ATTN_11DB)

    charge_adc = ADC(Pin(8))
    charge_adc.atten(ADC.ATTN_11DB)

    rtc = RTC()
    LOG_INTERVAL = 100
    log_counter = 0

    # while True:
    #     host, msg = esp.recv()
    #     if msg:             # msg == None if timeout in recv()
    #         print('got message from', host.hex(), 'msg:', msg)
    #         if msg == b'end':
    #             break


    gc.collect()

    while True:

        n = 10
        total = 0
        sumofsquares = 0
        for _ in range(n):
            raw = adc.read_uv()
            total += raw
            sumofsquares += raw * raw
        voltage = total / n / 1e6
        current = voltage / ISENSE_RESISTOR / ISENSE_GAIN  # Convert voltage to current

        x_raw = i2c.readfrom_mem(addr, 0x02, 1)[0] >> 4 | i2c.readfrom_mem(addr, 0x03, 1)[0] << 4
        y_raw = i2c.readfrom_mem(addr, 0x04, 1)[0] >> 4 | i2c.readfrom_mem(addr, 0x05, 1)[0] << 4
        z_raw = i2c.readfrom_mem(addr, 0x06, 1)[0] >> 4 | i2c.readfrom_mem(addr, 0x07, 1)[0] << 4
        max_val = 0x7FF
        x, y, z = u12_to_s12(x_raw) / max_val, u12_to_s12(y_raw) / max_val, u12_to_s12(z_raw) / max_val
        x = (x + 1)/2
        y = (y + 1)/2
        z = (z + 1)/2
        # print(f'X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}')
        tft.fillrect((0, 0), (4, int(160 * x)), TFT.RED)
        tft.fillrect((0, int(160 * x)), (4, 160), TFT.BLACK)
        tft.fillrect((4, 0), (4, int(160 * y)), TFT.GREEN)
        tft.fillrect((4, int(160 * y)), (4, 160), TFT.BLACK)
        tft.fillrect((8, 0), (4, int(160 * z)), TFT.BLUE)
        tft.fillrect((8, int(160 * z)), (4, 160), TFT.BLACK)

        # write the current as text to the screen
        tft.text((40, 10), f'I: {current * 1000:5.1f}mA', TFT.WHITE, sysfont) 

        joystick1 = joystick_adc1.read_uv() / 1e6
        joystick2 = joystick_adc2.read_uv() / 1e6
        tft.text((40, 20), f'Joystick:', TFT.WHITE, sysfont)
        tft.text((40, 30), f'{joystick1:5.3f}V, {joystick2:5.3f}V', TFT.WHITE, sysfont)

        charge = 2 * charge_adc.read_uv() / 1e6 # multiply by 2 for voltage divider
        tft.text((40, 40), f'Charge: {charge:-5.3f}V', TFT.WHITE, sysfont)

        year, month, day, weekday, hour, minute, second, subseconds = rtc.datetime()

        tft.text((40, 50), f'Time: {hour:02}:{minute:02}:{second:02}', TFT.WHITE, sysfont)

        tft.text((40, 60), f'MAC: {sta.config("mac").hex()}', TFT.WHITE, sysfont)

        rmac, rmesg = esp.recv(100)
        if rmac is not None:
            tft.text((40, 75), f'Recv {rmac.hex()}', TFT.WHITE, sysfont)
            tft.text((40, 85), f'len={len(rmesg)} t={hour:02}:{minute:02}:{second:02}', TFT.WHITE, sysfont)
            tft.text((40, 95), f'"{rmesg.decode("ascii")}"'[:19], TFT.WHITE, sysfont)

        if log_counter > LOG_INTERVAL:
            log_counter = 0
            now = f'{year:04}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}'
            log_data = f'{now}: current={current * 1000:.1f}mA, battery={charge:.3f}V'
            print(f'Logging: "{log_data}"')

            with open('log.txt', 'a') as f:
                f.write(log_data + '\n')

        log_counter += 1

test_accelerometer()
Pin(41, Pin.OUT).off()
test_main()
