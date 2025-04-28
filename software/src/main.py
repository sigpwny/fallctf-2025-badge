from machine import Pin, I2C, ADC, RTC, PWM
from time import sleep, localtime
import ssd1306
import math


class Badge:
    def __init__(self):
        self.rtc = RTC()
        self.rtc.datetime((2020, 1, 1, 0, 0, 0, 0, 0))

        # using default address 0x3C
        i2c = I2C(0, sda=Pin(11), scl=Pin(12))
        self.display = ssd1306.SSD1306_I2C(128, 64, i2c)

        self.display.fill(0)
        for i in range(0, 128, 5):
            self.display.rect(0, 0, i, 64, 1, True)
            self.display.show() 

        self.display.fill(0)
        self.display.text('Hello, World!', 0, 0)
        self.display.show()

        self.battery_pin = ADC(Pin(13))
        self.battery_pin.atten(ADC.ATTN_11DB)

        self.buzzer = PWM(Pin(10))
        self.buzzer_active = False

        self.btn0 = Pin(0, Pin.IN)
        self.prev_btn0 = False

    def update_battery_voltage(self):
        self.display.text("Time: %02d:%02d:%02d" % self.rtc.datetime()[4:7], 0, 0)

        VOLTAGE_DIVIDER = 2
        MAX_ADC_VALUE = 2**13
        MAX_VOLTAGE = 2.6 # officially 2.45V, but 2.6V is a calibrated value
        battery_voltage = self.battery_pin.read() * MAX_VOLTAGE * VOLTAGE_DIVIDER / MAX_ADC_VALUE

        self.display.text('Battery voltage:', 0, 10)
        self.display.text("%.3f V" % battery_voltage, 0, 20)

    def update_buzzer(self, ticks):
        freq = 400 + 350 * math.sin(ticks / 100.0)
        if self.buzzer_active:
            self.buzzer.freq(int(freq))
            self.buzzer.duty(512)
            self.display.text("Buzzer: %d" % freq, 0, 40)
        else:
            self.buzzer.freq(1)
            self.buzzer.duty(0)
            self.display.text("Buzzer: OFF", 0, 40)

        btn0 = self.btn0.value()
        if btn0 == 0 and self.prev_btn0:
            self.buzzer_active = not self.buzzer_active
        self.prev_btn0 = btn0

    def tick(self, ticks):
        self.display.fill(0)
        self.update_battery_voltage()
        self.update_buzzer(ticks)
        self.display.show()


def main():
    print('boot.')
    badge = Badge()

    tick = 0
    while True:
        tick += 1
        badge.tick(tick)
        sleep(0.01)


if __name__ == '__main__':
    main()
