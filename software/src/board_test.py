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
sta.config(txpower=20)
print('mac address:', sta.config('mac').hex())
esp = espnow.ESPNow()
esp.active(True)
esp.add_peer(bytes.fromhex('ff' * 6))  # broadcast


from ST7735 import TFT, sysfont


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

# LED controlled by MOSFET
lcd_led = PWM(Pin(41))
lcd_led.freq(1000)  # 1 kHz
lcd_led.duty_u16(int(.2 * 65535))

btn0 = Pin(0, Pin.IN)
btn1 = Pin(13, Pin.IN)

# tft = TFT(15, 16, 17, 18, 7)
# tft.init()
# tft.clear_screen(0x1234)

spi = SPI(2, baudrate=20000000, polarity=0, phase=0, sck=Pin(15), mosi=Pin(16))
tft = TFT(spi,7,18,17)
tft.rotation(3)  # Set rotation to 1 (landscape mode)
tft.initr()
tft.rgb(True)
tft.fill(TFT.BLACK)


def main():
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

    buzzer_active = False
    btn0_prev = False
    btn1_prev = False

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

        tft.text((40, 50), f'Time: {hour:02}:{minute:02}:{second:02}.{subseconds//10000:02}', TFT.WHITE, sysfont)

        tft.text((40, 60), f'MAC: {sta.config("mac").hex()}', TFT.WHITE, sysfont)

        rmac, rmesg = esp.irecv(50)
        if rmac is not None:
            tft.text((40, 75), f'Recv {rmac.hex()}', TFT.WHITE, sysfont)
            tft.text((40, 85), f'len={len(rmesg)} t={hour:02}:{minute:02}:{second:02}', TFT.WHITE, sysfont)
            tft.text((40, 95), f'"{rmesg.decode("ascii")}"'[:19], TFT.WHITE, sysfont)

        freq = 400 + 350 * math.sin(log_counter / 100.0)
        if buzzer_active:
            buzzer.freq(int(freq))
            buzzer.duty(512)
        else:
            buzzer.freq(1)
            buzzer.duty(0)

        if btn0.value() == 0 and not btn0_prev:
            buzzer_active = not buzzer_active

        if btn1.value() == 0 and not btn1_prev:
            esp.send(bytes.fromhex('ff' * 6), 'hello', False)

        btn0_prev = btn0.value() == 0
        btn1_prev = btn1.value() == 0

        if btn0.value() == 0:
            tft.fillrect((20, 20), (5, 5), TFT.RED)
        else:
            tft.fillrect((20, 20), (5, 5), TFT.GREEN)
        if btn1.value() == 0:
            tft.fillrect((20, 10), (5, 5), TFT.RED)
        else:
            tft.fillrect((20, 10), (5, 5), TFT.GREEN)

        if log_counter > LOG_INTERVAL:
            log_counter = 0
            now = f'{year:04}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}'
            log_data = f'{now}: current={current * 1000:.1f}mA, battery={charge:.3f}V'
            print(f'Logging: "{log_data}"')

            with open('log.txt', 'a') as f:
                f.write(log_data + '\n')

        log_counter += 1

main()
