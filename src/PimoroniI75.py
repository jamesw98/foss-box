import time
from IFossBoxDisplay import IFossBoxDisplay

class PimoroniI75(IFossBoxDisplay):
    def __init__(self, pins, width=64, height=32):
        super().__init__()
        from interstate75 import Interstate75
        from machine import Pin
        self.i75 = Interstate75(display=Interstate75.DISPLAY_INTERSTATE75_64X32, color_order=Interstate75.COLOR_ORDER_RGB)
        self.graphics = self.i75.display
        self.graphics.set_font('bitmap8')
        self.width = width
        self.height = height

        self.weapon_left_pin = pins["weapon_left"]
        self.weapon_right_pin = pins["weapon_right"]
        self.bell_left_pin = pins["bell_left"]
        self.bell_right_pin = pins["bell_right"]
        self.buzzer_pin = pins["buzzer"]

        self.beeper = Pin(self.buzzer_pin, Pin.OUT, value=1)

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

    def beep(self, duration):
        self.beeper_on()
        time.sleep(duration)
        self.beeper_off()

    def beeper_on(self):
        self.beeper.value(0)

    def beeper_off(self):
        self.beeper.value(1)

    def weapon_left(self):
        return self._button(self.weapon_left_pin)

    def weapon_right(self):
        return self._button(self.weapon_right_pin)

    def bell_left(self):
        return self._button(self.bell_left_pin)

    def bell_right(self):
        return self._button(self.bell_right_pin)

    def _button(self, pin_num):
        from machine import Pin
        return lambda: not Pin(pin_num, Pin.IN, Pin.PULL_UP).value()