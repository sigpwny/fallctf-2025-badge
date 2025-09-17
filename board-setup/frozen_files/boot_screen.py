from view import FontTextView, BitMapView
from layout import ComplexLayout, Style
from logger import log
import time

TYPE_CHECKING = False
if TYPE_CHECKING:
    from display import Display


def boot_screen(display, font_path="assets/monospaceKrypton_24.mfnt"):
    # type: (Display, str) -> None
    # TODO fix colors
    # by `magick pwny8.svg -resize 64x64 -strip -monochrome -depth 1 -define bmp:format=bmp3 mono:- > assets/logo.raw`
    with open("assets/logo.raw", "rb") as f:
        logo_data = f.read()
    ComplexLayout(
        display,
        (
            FontTextView(
                display=display,
                font_path=font_path,
                color=display.display.tft.GREEN,
                data="2025\nSIGPWNY\nFALLCTF",
                # rot=45,
            ),
            Style(posType=0b00, x=5, y=40),
        ),
        (
            BitMapView(
                display,
                bytearray(logo_data),
                width=64,
                height=64,
                fg_color=display.display.tft.GREEN,
            ),
            Style(posType=0b10, x=-10),
        ),
    ).render()
    # time.sleep(sleep)
