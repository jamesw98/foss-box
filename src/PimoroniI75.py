class PimoroniI75:
    def __init__(self, width=64, height=32):
        from interstate75 import Interstate75
        self.i75 = Interstate75(display=Interstate75.DISPLAY_INTERSTATE75_64X32, color_order=Interstate75.COLOR_ORDER_RGB)
        self.graphics = self.i75.display
        self.graphics.set_font('bitmap8')
        self.width = width
        self.height = height

    def fill_rect(self, x, y, w, h, color):
        self.graphics.set_pen(self.graphics.create_pen(*color))
        self.graphics.rectangle(x, y, w, h)

    def draw_text(self, text, x, y, color, scale=1):
        self.graphics.set_pen(self.graphics.create_pen(*color))
        self.graphics.text(text, x, y, scale=scale)

    def measure_text(self, text, scale=1):
        return self.graphics.measure_text(text, scale)

    def update(self):
        self.i75.update()