"""
This class serves as an interface. If you have a new board or different way
you want to handle some functionality, you have to implement these methods.
"""
class IFossBoxDisplay:
    @property
    def width(self):
        raise NotImplementedError

    @property
    def height(self):
        raise NotImplementedError

    def fill_rect(self, x, y, w, h, color):
        raise NotImplementedError

    def draw_text(self, text, x, y, color, scale=1):
        raise NotImplementedError

    def measure_text(self, text, scale=1):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def weapon_left(self, pin):
        raise NotImplementedError

    def weapon_right(self, pin):
        raise NotImplementedError

    def bell_left(self, pin):
        raise NotImplementedError

    def bell_right(self, pin):
        raise NotImplementedError