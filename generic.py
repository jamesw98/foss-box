# generic.py — platform-agnostic fencing scoring machine (POC)
#
# The core (DisplayDriver + ScoringMachine) has NO hardware imports.
# To port to a new board, write a ~15-line adapter at the bottom that
# implements DisplayDriver and wraps your buttons as plain callables.
#
# Colors are plain (r, g, b) tuples throughout — no platform pen objects.
# Buttons are any callable that returns True when pressed.

import time


# ---------------------------------------------------------------------------
# Time shim — smooths over MicroPython vs CircuitPython differences
# ---------------------------------------------------------------------------

def _ticks_ms():
    try:
        return time.ticks_ms()           # MicroPython
    except AttributeError:
        return int(time.monotonic() * 1000)  # CircuitPython

def _ticks_diff(new, old):
    try:
        return time.ticks_diff(new, old)  # MicroPython (handles wraparound)
    except AttributeError:
        return new - old

def _ticks_add(t, delta):
    try:
        return time.ticks_add(t, delta)   # MicroPython
    except AttributeError:
        return t + delta


# ---------------------------------------------------------------------------
# Display interface — implement these 4 methods + 2 properties for your board
# ---------------------------------------------------------------------------

class DisplayDriver:
    """
    Minimal display contract. Subclass and implement all methods.

    Colors are always plain (r, g, b) tuples — convert inside your adapter.
    """

    @property
    def width(self) -> int:
        raise NotImplementedError

    @property
    def height(self) -> int:
        raise NotImplementedError

    def fill_rect(self, x, y, w, h, color):
        """Fill a rectangle with color=(r,g,b)."""
        raise NotImplementedError

    def draw_text(self, text, x, y, color, scale=1):
        """Draw text at (x, y) with color=(r,g,b)."""
        raise NotImplementedError

    def measure_text(self, text, scale=1) -> int:
        """Return the pixel width of text at the given scale."""
        raise NotImplementedError

    def update(self):
        """Push the frame buffer to the physical display."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Scoring machine — only depends on DisplayDriver + time shim above
# ---------------------------------------------------------------------------

class ScoringMachine:
    DOUBLE_LOCKOUT  = 40    # ms — window to detect a double touch
    ILLUMINATED_TIME = 3    # seconds lights stay on after a touch
    SCORE_PADDING   = 5     # px from display edge to score digits
    CLOCK_ENABLED   = False
    SCORE_ENABLED   = True
    CLOCK_SECONDS   = 180

    # Colors as plain (r, g, b) tuples
    BLACK       = (0,   0,   0)
    LEFT_COLOR  = (255, 0,   0)
    RIGHT_COLOR = (0,   255, 0)
    SCORE_COLOR = (89,  6,   200)
    TIMER_COLOR = (255, 255, 255)

    def __init__(self, display: DisplayDriver,
                 weapon_left, weapon_right, bell_left, bell_right):
        """
        display      — DisplayDriver instance
        weapon_left  — callable, returns True when the left weapon tip is depressed
        weapon_right — callable, returns True when the right weapon tip is depressed
        bell_left    — callable, returns True when the left bell is pressed
        bell_right   — callable, returns True when the right bell is pressed
        """
        self.d = display
        self.weapon_left  = weapon_left
        self.weapon_right = weapon_right
        self.bell_left    = bell_left
        self.bell_right   = bell_right

        self.W       = display.width
        self.W_HALF  = self.W // 2
        self.W_FORTH = self.W // 4
        self.W_EIGHTH = self.W // 8

        self.left_score    = 0
        self.right_score   = 0
        self.clock_seconds = self.CLOCK_SECONDS
        self.clock         = self._fmt_clock(self.clock_seconds)
        self.last_tick     = _ticks_ms()

    @staticmethod
    def _fmt_clock(s):
        return "{:d}:{:02d}".format(s // 60, s % 60)

    def _check(self):
        # A weapon fires only when the opposing bell is not active (pull-up: unpressed = True)
        left  = self.weapon_left()  and not self.bell_right()
        right = self.weapon_right() and not self.bell_left()
        return left, right

    def _clear_lights(self):
        self.d.fill_rect(0, 0, self.W, self.W_FORTH, self.BLACK)
        self.d.update()

    def _clear_clock(self):
        tw = self.d.measure_text(self.clock, 1)
        x  = (self.W - tw) // 2
        self.d.fill_rect(x, self.W_FORTH, tw, self.W_EIGHTH, self.BLACK)
        self.d.update()

    def _clear_score(self, score, side):
        text = str(score)
        w = self.d.measure_text(text, 1)
        x = self.SCORE_PADDING if side == 'left' else self.W - w - self.SCORE_PADDING
        self.d.fill_rect(x, self.W_FORTH, w, self.W_EIGHTH, self.BLACK)
        self.d.update()

    def run(self):
        while True:
            left_pressed, right_pressed = self._check()
            double     = left_pressed and right_pressed
            any_pressed = left_pressed or right_pressed

            # Wait out the double-lockout window before committing to a single touch
            if any_pressed and not double:
                waiting_for = 'left' if right_pressed else 'right'
                start = _ticks_ms()
                while True:
                    lp, rp = self._check()
                    if (lp if waiting_for == 'left' else rp):
                        double = True
                        break
                    if _ticks_diff(_ticks_ms(), start) >= self.DOUBLE_LOCKOUT:
                        break

            if any_pressed:
                if left_pressed or double:
                    self.d.fill_rect(0, 0, self.W_HALF, self.W_FORTH, self.LEFT_COLOR)
                    self.left_score += 1

                if right_pressed or double:
                    self.d.fill_rect(self.W_HALF, 0, self.W_HALF, self.W_FORTH, self.RIGHT_COLOR)
                    self.right_score += 1

                self.d.update()
                time.sleep(self.ILLUMINATED_TIME)
                self.last_tick = _ticks_ms()
                self._clear_lights()
                self._clear_score(self.left_score,  'left')
                self._clear_score(self.right_score, 'right')

            if (self.CLOCK_ENABLED
                    and _ticks_diff(_ticks_ms(), self.last_tick) >= 1000
                    and self.clock_seconds > 0):
                self._clear_clock()
                self.clock_seconds -= 1
                self.last_tick = _ticks_add(self.last_tick, 1000)
                self.clock = self._fmt_clock(self.clock_seconds)

            left_num  = str(self.left_score)
            right_num = str(self.right_score)
            right_x   = self.W - self.d.measure_text(right_num, 1) - self.SCORE_PADDING
            clock_x   = (self.W - self.d.measure_text(self.clock, 1)) // 2

            if self.CLOCK_ENABLED:
                self.d.draw_text(self.clock, clock_x, self.W_FORTH, self.TIMER_COLOR)

            if self.SCORE_ENABLED:
                self.d.draw_text(left_num,  self.SCORE_PADDING, self.W_FORTH, self.SCORE_COLOR)
                self.d.draw_text(right_num, right_x,            self.W_FORTH, self.SCORE_COLOR)

            self.d.update()


# ---------------------------------------------------------------------------
# Adapters — one per board family.  Each imports its own libs internally so
# the core above stays import-free.  Copy/modify these for new hardware.
# ---------------------------------------------------------------------------

class PimoroniI75Display(DisplayDriver):
    """Pimoroni Interstate 75 W (MicroPython / PicoGraphics)."""

    def __init__(self, width=64, height=32):
        from interstate75 import Interstate75
        self._i75 = Interstate75(
            display=Interstate75.DISPLAY_INTERSTATE75_64X32,
            color_order=Interstate75.COLOR_ORDER_RGB,
        )
        self._g = self._i75.display
        self._g.set_font('bitmap8')
        self._w, self._h = width, height

    @property
    def width(self):  return self._w
    @property
    def height(self): return self._h

    def fill_rect(self, x, y, w, h, color):
        self._g.set_pen(self._g.create_pen(*color))
        self._g.rectangle(x, y, w, h)

    def draw_text(self, text, x, y, color, scale=1):
        self._g.set_pen(self._g.create_pen(*color))
        self._g.text(text, x, y, scale=scale)

    def measure_text(self, text, scale=1):
        return self._g.measure_text(text, scale)

    def update(self):
        self._i75.update()


class AdafruitMatrixDisplay(DisplayDriver):
    """
    Adafruit RGB Matrix panel (CircuitPython).

    Uses framebufferio + displayio.  Pin names below match MatrixPortal M4 /
    RP2040 Matrix; adjust for your board.  This is a POC — text rendering
    re-creates Label objects each frame; cache them for production use.
    """

    def __init__(self, width=64, height=32):
        import board, rgbmatrix, framebufferio, displayio, terminalio
        from adafruit_display_text import label as _lbl

        self._lbl   = _lbl
        self._font  = terminalio.FONT
        self._w, self._h = width, height
        self._pending_color = 0xFFFFFF

        displayio.release_displays()
        matrix = rgbmatrix.RGBMatrix(
            width=width, height=height, bit_depth=2,
            rgb_pins=[board.R0, board.G0, board.B0, board.R1, board.G1, board.B1],
            addr_pins=[board.ROW_A, board.ROW_B, board.ROW_C, board.ROW_D],
            clock_pin=board.CLK, latch_pin=board.LAT, output_enable_pin=board.OE,
        )
        self._display = framebufferio.FramebufferDisplay(matrix, auto_refresh=False)

        self._palette    = displayio.Palette(16)
        self._palette[0] = 0x000000
        self._bitmap     = displayio.Bitmap(width, height, 16)
        self._color_map  = {}
        self._next_idx   = 1

        tile = displayio.TileGrid(self._bitmap, pixel_shader=self._palette)
        self._text_group = displayio.Group()
        root = displayio.Group()
        root.append(tile)
        root.append(self._text_group)
        self._display.root_group = root

    @property
    def width(self):  return self._w
    @property
    def height(self): return self._h

    def _idx(self, color):
        packed = (color[0] << 16) | (color[1] << 8) | color[2]
        if packed not in self._color_map:
            self._palette[self._next_idx] = packed
            self._color_map[packed] = self._next_idx
            self._next_idx += 1
        return self._color_map[packed]

    def fill_rect(self, x, y, w, h, color):
        idx = self._idx(color) if any(color) else 0
        for py in range(y, y + h):
            for px in range(x, x + w):
                if 0 <= px < self._w and 0 <= py < self._h:
                    self._bitmap[px, py] = idx

    def draw_text(self, text, x, y, color, scale=1):
        packed = (color[0] << 16) | (color[1] << 8) | color[2]
        lbl = self._lbl.Label(self._font, text=text, color=packed, scale=scale)
        lbl.x, lbl.y = x, y
        self._text_group.append(lbl)

    def measure_text(self, text, scale=1):
        return len(text) * 6 * scale  # terminalio.FONT is ~6 px/char

    def update(self):
        self._display.refresh()
        while len(self._text_group):
            self._text_group.pop()


def _mp_button(pin_num):
    """Return a callable for a pull-up button on a MicroPython board."""
    from machine import Pin
    p = Pin(pin_num, Pin.IN, Pin.PULL_UP)
    return lambda: not p.value()


def _cp_button(pin):
    """Return a callable for a pull-up button on a CircuitPython board."""
    import digitalio
    btn = digitalio.DigitalInOut(pin)
    btn.direction = digitalio.Direction.INPUT
    btn.pull = digitalio.Pull.UP
    return lambda: not btn.value


# ---------------------------------------------------------------------------
# Entry point — pick one block, comment out the other
# ---------------------------------------------------------------------------

# Pimoroni Interstate 75 W (MicroPython)
display      = PimoroniI75Display(width=64, height=32)
weapon_left  = _mp_button(21)
weapon_right = _mp_button(19)
bell_left    = _mp_button(27)
bell_right   = _mp_button(26)

# Adafruit RGB Matrix (CircuitPython) — uncomment to use
# import board
# display      = AdafruitMatrixDisplay(width=64, height=32)
# weapon_left  = _cp_button(board.D9)
# weapon_right = _cp_button(board.D10)
# bell_left    = _cp_button(board.D11)
# bell_right   = _cp_button(board.D12)

ScoringMachine(display, weapon_left, weapon_right, bell_left, bell_right).run()
