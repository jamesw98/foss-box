"""
This class serves as an interface. If you have a new board or different way
you want to handle some functionality, you have to implement these methods.
"""
class IFossBoxDisplay:
    @property
    def width(self) -> int:
        raise NotImplementedError

    @property
    def height(self) -> int:
        raise NotImplementedError

    def draw_rect(self, x, y, w, h, color):
        raise NotImplementedError

    def draw_text(self, text, x, y, color, scale=1):
        raise NotImplementedError

    def measure_text(self, text, scale=1):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError