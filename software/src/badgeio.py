"""
TEMP placeholder for badge io components
"""

from ST7735 import TFT
from machine import SPI, Pin, PWM


class PullupButton:
    def __init__(self, pin):
        self.button = Pin(pin, Pin.IN, Pin.PULL_UP)
        """
        Maintain a buffer of the last two states
        buffer[0] is the current state
        buffer[1] is the previous state
        """
        self.buffer = [False, False]

    @property
    def value(self):
        """
        Gets current state of button. Pullup means 1 when not pressed and 0 when it is, so we invert it.
        """
        return not self.button.value()

    @property
    def pressed(self):
        """
        Detects a rising press, I.E. the button was not pressed before, but is now
        """
        return self.buffer[0] and not self.buffer[1]

    @property
    def released(self):
        """
        Detects a falling press, I.E. the button was pressed before, but is not now
        """
        return not self.buffer[0] and self.buffer[1]

    def tick(self):
        self.buffer[1] = self.buffer[0]
        self.buffer[0] = self.value


class Joystick:
    def __init__(self):
        pass

    def x(self):
        return 0

    def y(self):
        return 1


spi = SPI(1, baudrate=20000000, polarity=0, phase=0, sck=Pin(15), mosi=Pin(16))
display = TFT(spi, aDC=7, aReset=18, aCS=17)
display.initr()
display.rgb(True)
# LED controlled by MOSFET
lcd_led = PWM(Pin(41))
lcd_led.freq(1000)  # 1 kHz
lcd_led.duty_u16(int(.5 * 65535))
a_btn = PullupButton(0)
b_btn = PullupButton(13)
joystick = Joystick()


def tick_buttons():
    a_btn.tick()
    b_btn.tick()
