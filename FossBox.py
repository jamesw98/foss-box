import Utils
import time

class FossBox:
    DOUBLE_LOCKOUT_MS = 40
    ILLUMINATED_TIME = 3
    SCORE_SIDE_PADDING = 5
    SCORE_TOP_PADDING = 3
    CLOCK_ENABLED = False
    SCORE_ENABLED = True
    CLOCK_SECONDS = 180

    BLACK = (0, 0, 0)
    LEFT_COLOR = (255, 0 , 0)
    RIGHT_COLOR = (0, 255, 0)
    SCORE_COLOR = (0, 0, 255)
    TIMER_COLOR = (255, 255, 255)
    GROUND_COLOR = (255, 100, 0)

    def __init__(self, disp: IFossBoxDisplay, weapon_left, weapon_right, bell_left, bell_right):
        self.disp = disp
        self.weapon_left = weapon_left
        self.weapon_right = weapon_right
        self.bell_left = bell_left
        self.bell_right = bell_right

        self.width = self.disp.width
        self.height = self.disp.height
        self.half = self.w // 2
        self.forth = self.w // 4
        self.eighth = self.w // 8

        self.left_score = 0
        self.right_score = 0
        self.clock_seconds = self.CLOCK_SECONDS
        self.clock = Utils.format_clock(self.clock_seconds)
        self.last_tick = Utils.ticks_ms()

    def check(self):
        return self.weapon_left() and not self.bell_right(), self.weapon_right() and not self.bell_left(), self.bell_left(), self.bell_right()

    def clear_lights(self):
        self.disp.fill_rect(0, 0, self.W, self.forth, self.BLACK)
        self.disp.update()

    def clear_clock(self):
        tw = self.disp.measure_text(self.clock, 1)
        x = (self.width - tw) // 2
        self.disp.fill_rect(x, self.forth, tw, self.eigth, self.BLACK)
        self.disp.update()

    def clear_score(self, score, side):
        text = str(score)
        w = self.disp.measure_text(text, 1)
        x = self.SCORE_SIDE_PADDING if side == 'left' else self.width - w - self.SCORE_SIDE_PADDING
        self.disp.fill_rect(x, self.forth + self.SCORE_TOP_PADDING, w, self.eighth, self.BLACK)
        self.disp.update()

    def run(self):
        while True:
            left_valid, right_valid, left_bell, right_bell = self.check()
            double = left_valid and right_valid
            any_valid = left_valid or right_valid
            any_bell = left_bell or right_bell

            if any_bell:
                if left_bell:
                    self.disp.fill_rect(0, 0, 3, self.forth, self.GROUND_COLOR)
                if right_bell:
                    self.disp.fill_rect(self.width - 3, 0, 3, self.forth, self.GROUND_COLOR)
            self.disp.update()
            self.clear_lights()

            if any_valid and not double:
                waiting_for = 'left' if right_valid else 'right'
                start = Utils.ticks_ms()
                while True:
                    left, right, _, _ = self.check()
                    if (waiting_for == 'left' and left) or (waiting_for == 'right' and right):
                        double = true
                        break

                    if Utils.ticks_diff(Utils.ticks_ms(), start) >= self.DOUBLE_LOCKOUT_MS:
                        break

            if any_valid:
                if left_valid or double:
                    self.disp.fill_rect(0, 0, self.half, self.forth, self.LEFT_COLOR)
                    self.left_score += 1
                if right_valid or double:
                    self.disp.fill_rect(self.half, 0, self.forth, self.RIGHT_COLOR)
                    self.right_score += 1

                self.disp.update()
                time.sleep(self.ILLUMINATED_TIME)
                self.last_tick = Utils.ticks_ms()
                self.clear_lights()
                self.clear_score(self.left_score, 'left')
                self.clear_score(self.right_score, 'right')

            if self.CLOCK_ENABLED and Utils.ticks_diff(Utils.ticks_ms(), self.last_tick) >= 1000 and self.clock_seconds > 0:
                self.clear_clock()
                self.clock_seconds -= 1
                self.last_tick = Utils.ticks_add(self.last_tick, 1000)
                self.clock = Utils.format_clock(self.clock_seconds)
                clock_x = (self.W - self.d.measure_text(self.clock, 1)) // 2
                self.d.draw_text(self.clock, clock_x, self.W_FORTH, self.TIMER_COLOR)

            if self.SCORE_ENABLED:
                left_num = str(self.left_score)
                right_num = str(self.right_score)
                right_x = self.W - self.disp.measure_text(right_num, 1) - self.SCORE_SIDE_PADDING
                self.disp.draw_text(left_num, self.SCORE_SIDE_PADDING, self.forth + self.SCORE_TOP_PADDING, self.SCORE_COLOR)
                self.disp.draw_text(right_num, right_x, self.forth + self.SCORE_TOP_PADDING, self.SCORE_COLOR)

            self.disp.update()
