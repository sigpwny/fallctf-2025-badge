from view import FontTextView, BitMapView
from layout import ColumnLayout
from logger import log
import time

TYPE_CHECKING = False
if TYPE_CHECKING:
    from display import Display


def boot_screen(display, font_path="assets/monospaceKrypton_24.mfnt", sleep=0.5):
    # type: (Display, str, int) -> None
    # TODO fix colors
    # by `magick pwny8.svg -resize 64x64 -strip -monochrome -depth 1 -define bmp:format=bmp3 mono:- > assets/logo.raw`
    with open("assets/logo.raw", "rb") as f:
        logo_data = f.read()
    v = ColumnLayout(
        display,
        FontTextView(
            display=display,
            font_path=font_path,
            color=display.display.tft.GREEN,
            # rot=45,
        ),
        BitMapView(
            display,
            bytearray(logo_data),
            width=64,
            height=64,
            fg_color=display.display.tft.GREEN,
        ),
        col_width=90,
        # draw_outline=True,
    )
    v[0].update(5, 40, "2025\nSIGPWNY\nFALLCTF")
    v.render()
    time.sleep(sleep)
