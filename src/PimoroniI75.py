import Config

class PimoroniI75:
    def __init__(self, width=64, height=32):
        from interstate75 import Interstate75
        from machine import Pin
        self.i75 = Interstate75(display=Interstate75.DISPLAY_INTERSTATE75_64X32, color_order=Interstate75.COLOR_ORDER_RGB)
        self.graphics = self.i75.display
        self.graphics.set_font('bitmap8')
        self.width = width
        self.height = height

    def fill_rect(self, x, y, w, h, color):
        self.graphics.set_pen(self.graphics.create_pen(*color))
        self.graphics.rectangle(x, y, w, h)

    def draw_text(self, text, x, y, color, scale=1, font='bitmap8'):
        self.graphics.set_font(font)
        self.graphics.set_pen(self.graphics.create_pen(*color))
        self.graphics.text(text, x, y, scale=scale)
        self.graphics.set_font('bitmap8')

    def measure_text(self, text, scale=1, font='bitmap8'):
        self.graphics.set_font(font)
        width = self.graphics.measure_text(text, scale)
        self.graphics.set_font('bitmap8')
        return width

    def update(self):
        self.i75.update()

    def weapon_left(self):
        return self._button(Config.WEAPON_LEFT_PIN)

    def weapon_right(self):
        return self._button(Config.WEAPON_RIGHT_PIN)

    def bell_left(self):
        return self._button(Config.BELL_LEFT_PIN)

    def bell_right(self):
        return self._button(Config.BELL_RIGHT_PIN)

    def _button(self, pin_num):
        from machine import Pin
        return lambda: not Pin(pin_num, Pin.IN, Pin.PULL_UP).value()