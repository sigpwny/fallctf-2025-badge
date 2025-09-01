import asyncio
from logger import log

import ST7735
import framebuf
from machine import Pin, SPI, PWM
from boolpalette import BoolPalette

class ST7735Display(framebuf.FrameBuffer):
    def __init__(
            self,
            _buffer=None,
            spi_id=2,
            sck_pin=15,
            mosi_pin=16,
            dc_pin=7,
            reset_pin=18,
            cs_pin=17,
            backlight_pin=41,
            baudrate=40_000_000,
            rotation=3,
            rgb=True,
            width=160,
            height=128
    ):
        self.width = width
        self.height = height
        if _buffer:
            assert len(_buffer) == self.width * self.height * 2
            self.buffer = _buffer
        else:
            self.buffer = bytearray(self.width * self.height * 2)  # RGB565 = 2 bytes per pixel

        # Initialize FrameBuffer in RGB565 format
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)

        self.palette = BoolPalette(framebuf.RGB565)

        # SPI setup
        self.spi = SPI(spi_id, baudrate=baudrate, polarity=0, phase=0, sck=Pin(sck_pin), mosi=Pin(mosi_pin))

        self.tft = ST7735.TFT(self.spi, aDC=dc_pin, aReset=reset_pin, aCS=cs_pin, variant="green")
        self.tft.initg()

        self.tft.rgb(rgb)
        self.tft.rotation(rotation)

        # Backlight control
        self.backlight = PWM(Pin(backlight_pin))
        self.backlight.freq(1000)
        self.set_backlight(1)

        self.clear()
        self.show()

    def clear(self, color=0x0000):
        self.fill(color)

    def set_backlight(self, duty):
        """Set backlight brightness: 0 (off) to 1 (max)."""
        self.backlight.duty_u16(int(duty * 65535))

    def draw_circle(self, x, y, r, color):
        self.ellipse(x, y, r, r, color)

    def fill_circle(self, x, y, r, color):
        self.ellipse(x, y, r, r, color, True)

    def show(self):
        """Push framebuffer to the display."""
        self.tft.image(0, 0, self.width - 1, self.height - 1, self.buffer)

    def get_tft(self):
        return self.tft


class Display:
    def __init__(self, _buffer=None):
        self.display = ST7735Display(_buffer=_buffer)
        self.width = self.display.width
        self.height = self.display.height
        self.line_height = 10  # Approximate line height for text

        self.display.set_backlight(0.2)

    def clear(self):
        self.display.clear()

    def draw_text(self, x, y, text):
        self.display.text(text, x, y, 0xffff)

    def show(self):
        self.display.show()

    async def run(self):
        pass
