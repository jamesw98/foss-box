"""
This class serves as an interface. If you have a new board or different way
you want to handle some functionality, you have to implement these methods.
"""
class IFossBoxDisplay:
    def __init__(self):
        # 64x32 is what the code was originally made for, so if you don't specify when writing a class that inherits
        # this, it'll default to this.
        self.width = 64
        self.height = 32

    def fill_rect(self, x, y, w, h, color):
        raise NotImplementedError

    def draw_text(self, text, x, y, color, scale=1, font='bitmap8'):
        raise NotImplementedError

    def measure_text(self, text, scale=1, font='bitmap8'):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def beep(self, duration):
        raise NotImplementedError

    def beeper_on(self):
        raise NotImplementedError

    def beeper_off(self):
        raise NotImplementedError

    def weapon_left(self):
        raise NotImplementedError

    def weapon_right(self):
        raise NotImplementedError

    def bell_left(self):
        raise NotImplementedError

    def bell_right(self):
        raise NotImplementedError