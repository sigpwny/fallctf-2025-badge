import ST7735
import framebuf
from sysfont import sysfont
from machine import Pin, SPI, PWM

class Display(framebuf.FrameBuffer):
  def __init__(
    self,
    spi_id=1,
    sck_pin=15,
    mosi_pin=16,
    dc_pin=7,
    reset_pin=18,
    cs_pin=17,
    backlight_pin=41,
    baudrate=20000000,
    rotation=3,
    rgb=True,
    tab='g',  # 'r' = red, 'b' = blue, 'g' = green
    width=160,
    height=128
  ):
    self.width = width
    self.height = height
    self.buffer = bytearray(self.width * self.height * 2)  # RGB565 = 2 bytes per pixel

    # Initialize FrameBuffer in RGB565 format
    super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)

    # SPI setup
    self.spi = SPI(spi_id, baudrate=baudrate, polarity=0, phase=0, sck=Pin(sck_pin), mosi=Pin(mosi_pin))

    # Init ST7735 driver with correct tab type
    if tab == 'r':
      self.tft = ST7735.TFT(self.spi, aDC=dc_pin, aReset=reset_pin, aCS=cs_pin, variant="red")
      self.tft.initr()
    elif tab == 'b':
      self.tft = ST7735.TFT(self.spi, aDC=dc_pin, aReset=reset_pin, aCS=cs_pin, variant="black")
      self.tft.initb()
    elif tab == 'g':
      self.tft = ST7735.TFT(self.spi, aDC=dc_pin, aReset=reset_pin, aCS=cs_pin, variant="green")
      self.tft.initg()
    else:
      raise ValueError("Invalid tab color. Use 'r', 'b', or 'g'.")

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
    duty = int(1023 * (1 - duty))
    self.backlight.duty(duty)
  
  def draw_circle(self, x, y, r, color):
    self.ellipse(x, y, r, r, color)

  def fill_circle(self, x, y, r, color):
    self.ellipse(x, y, r, r, color, True)

  def show(self):
    """Push framebuffer to the display."""
    self.tft.image(0, 0, self.width - 1, self.height - 1, self.buffer)

  def get_tft(self):
    return self.tft