import board
import displayio
import framebufferio
import rgbmatrix
import digitalio
import time
import terminalio
from adafruit_display_text import bitmap_label
from IFossBoxDisplay import IFossBoxDisplay

try:
    import bitmaptools as _bitmaptools
except ImportError:
    _bitmaptools = None


class MatrixPortalS3(IFossBoxDisplay):
    # HUB75 matrix pins - pre-wired on Matrix Portal S3, do not change
    _RGB_PINS = [
        board.MTX_R1, board.MTX_G1, board.MTX_B1,
        board.MTX_R2, board.MTX_G2, board.MTX_B2,
    ]
    _ADDR_PINS = [board.MTX_ADDRA, board.MTX_ADDRB, board.MTX_ADDRC, board.MTX_ADDRD]
    _CLK_PIN = board.MTX_CLK
    _LAT_PIN = board.MTX_LAT
    _OE_PIN = board.MTX_OE

    # User GPIO - change these to match your wiring
    WEAPON_LEFT_PIN = board.A0
    WEAPON_RIGHT_PIN = board.A1
    BELL_LEFT_PIN = board.A2
    BELL_RIGHT_PIN = board.A3
    BUZZER_PIN = board.TX   # active-low external buzzer on TX pin

    # Font file paths - copy these to /fonts/ on the board.
    # Download from:
    # https://github.com/olikraus/u8g2/tree/master/tools/font/bdf
    FONT_MAIN  = "/fonts/5x8.bdf"  # used for bitmap8 (scores, clock)
    FONT_SMALL = "/fonts/4x6.bdf"  # used for bitmap6 (BT ID)

    def __init__(self, width=64, height=32):
        super().__init__()
        displayio.release_displays()

        self._matrix = rgbmatrix.RGBMatrix(
            width=width,
            height=height,
            bit_depth=4,
            rgb_pins=self._RGB_PINS,
            addr_pins=self._ADDR_PINS,
            clock_pin=self._CLK_PIN,
            latch_pin=self._LAT_PIN,
            output_enable_pin=self._OE_PIN,
        )
        self._display = framebufferio.FramebufferDisplay(self._matrix, auto_refresh=False)
        self.width = width
        self.height = height

        # Palette-backed bitmap for fill_rect (up to 63 distinct colors + black)
        self._palette = displayio.Palette(64)
        self._palette[0] = 0x000000
        self._color_map = {(0, 0, 0): 0}
        self._next_color = 1

        self._bitmap = displayio.Bitmap(width, height, 64)
        self._bg_tile = displayio.TileGrid(self._bitmap, pixel_shader=self._palette)

        self._group = displayio.Group()
        self._group.append(self._bg_tile)
        self._display.root_group = self._group

        # Load fonts; fall back to terminalio.FONT if a file is missing
        self._font_main  = self._load_font(self.FONT_MAIN)
        self._font_small = self._load_font(self.FONT_SMALL)

        # Measure metrics once per font: (x_off, y_off, char_w, h)
        self._metrics_main  = self._font_metrics(self._font_main)
        self._metrics_small = self._font_metrics(self._font_small)

        # Active text labels keyed by (x, y); labels render above the bitmap
        self._labels = {}
        # When fill_rect removes a label, skip the next update() so we never
        # push a blank frame between clear and redraw.
        self._defer_refresh = False

        # Active-low buzzer
        self._beeper = digitalio.DigitalInOut(self.BUZZER_PIN)
        self._beeper.direction = digitalio.Direction.OUTPUT
        self._beeper.value = True

    # -- internal helpers --

    @staticmethod
    def _load_font(path):
        try:
            from adafruit_bitmap_font import bitmap_font
            return bitmap_font.load_font(path)
        except (ImportError, OSError, ValueError):
            return terminalio.FONT

    @staticmethod
    def _font_metrics(font):
        lbl = bitmap_label.Label(font, text="M")
        bb = lbl.bounding_box
        return (bb[0], bb[1], bb[2], bb[3])  # (x_off, y_off, char_w, h)

    def _color_idx(self, color):
        r, g, b = color
        key = (r, g, b)
        if key not in self._color_map:
            idx = self._next_color
            self._palette[idx] = (r << 16) | (g << 8) | b
            self._color_map[key] = idx
            self._next_color = self._next_color % 63 + 1
        return self._color_map[key]

    # -- IFossBoxDisplay --

    def fill_rect(self, x, y, w, h, color):
        idx = self._color_idx(color)
        if _bitmaptools is not None:
            _bitmaptools.fill_region(self._bitmap, x, y, min(x + w, self.width), min(y + h, self.height), idx)
        else:
            for row in range(y, min(y + h, self.height)):
                for col in range(x, min(x + w, self.width)):
                    self._bitmap[col, row] = idx
        # Remove labels whose anchor position falls inside the cleared area so
        # stale text doesn't render on top of the freshly-cleared background.
        to_remove = [
            k for k in self._labels
            if x <= k[0] < x + w and y <= k[1] < y + h
        ]
        for k in to_remove:
            self._group.remove(self._labels.pop(k))
        if to_remove:
            self._defer_refresh = True

    def draw_text(self, text, x, y, color, scale=1, font='bitmap8'):
        r, g, b = color
        color_val = (r << 16) | (g << 8) | b
        font_obj = self._font_small if font == 'bitmap6' else self._font_main
        metrics  = self._metrics_small if font == 'bitmap6' else self._metrics_main
        x_off, y_off, _, h = metrics
        key = (x, y)
        if key in self._labels:
            lbl = self._labels[key]
            if lbl.text != text:
                lbl.text = text
            lbl.color = color_val
        else:
            lbl = bitmap_label.Label(font_obj, text=text, color=color_val, scale=scale)
            lbl.x = x - x_off
            # Shift so visible top lands at y; clamp to keep bottom on screen.
            lbl.y = min(y, self.height - h) - y_off
            self._labels[key] = lbl
            self._group.append(lbl)

    def measure_text(self, text, scale=1, font='bitmap8'):
        _, _, char_w, _ = self._metrics_small if font == 'bitmap6' else self._metrics_main
        return char_w * len(text) * scale

    def update(self):
        if self._defer_refresh:
            self._defer_refresh = False
            return
        self._display.refresh()

    def beep(self, duration):
        self.beeper_on()
        time.sleep(duration)
        self.beeper_off()

    def beeper_on(self):
        self._beeper.value = False

    def beeper_off(self):
        self._beeper.value = True

    def weapon_left(self):
        return self._button(self.WEAPON_LEFT_PIN)

    def weapon_right(self):
        return self._button(self.WEAPON_RIGHT_PIN)

    def bell_left(self):
        return self._button(self.BELL_LEFT_PIN)

    def bell_right(self):
        return self._button(self.BELL_RIGHT_PIN)

    def _button(self, pin):
        btn = digitalio.DigitalInOut(pin)
        btn.direction = digitalio.Direction.INPUT
        btn.pull = digitalio.Pull.UP
        return lambda: not btn.value
