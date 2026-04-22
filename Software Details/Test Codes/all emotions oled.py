from machine import Pin, I2C
import sh1106
import math
import time

# ── Setup ────────────────────────────────────────────────

WIDTH = 128
HEIGHT = 64
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
oled = sh1106.SH1106_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, rotate=180)
try:
    oled.sleep(False)
except:
    pass

# ── Drawing helpers ──────────────────────────────────────

def fill_circle(cx, cy, r, col=1):
    for dy in range(-r, r+1):
        dx = int((r*r - dy*dy) ** 0.5)
        oled.hline(cx - dx, cy + dy, 2*dx + 1, col)

def draw_circle(cx, cy, r):
    x, y, err = r, 0, 0
    while x >= y:
        oled.pixel(cx+x, cy+y, 1); oled.pixel(cx-x, cy+y, 1)
        oled.pixel(cx+x, cy-y, 1); oled.pixel(cx-x, cy-y, 1)
        oled.pixel(cx+y, cy+x, 1); oled.pixel(cx-y, cy+x, 1)
        oled.pixel(cx+y, cy-x, 1); oled.pixel(cx-y, cy-x, 1)
        y += 1
        err += 2*y + 1
        if 2*(err - x) + 1 > 0:
            x -= 1
            err += 1 - 2*x

def draw_arc(cx, cy, r, start_deg, end_deg):
    steps = 40
    for i in range(steps + 1):
        angle = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        x = int(cx + r * math.cos(angle))
        y = int(cy + r * math.sin(angle))
        oled.pixel(x, y, 1)

def eyes_open():
    fill_circle(42, 28, 12, 1)
    fill_circle(86, 28, 12, 1)

def eyes_closed():
    oled.hline(30, 28, 24, 1)
    oled.hline(74, 28, 24, 1)

def blink(draw_extras):
    """one blink — eyes open, blink, eyes open again"""
    oled.fill(0); eyes_open(); draw_extras(); oled.show()
    time.sleep(1.5)
    oled.fill(0); eyes_closed(); draw_extras(); oled.show()
    time.sleep(0.15)
    oled.fill(0); eyes_open(); draw_extras(); oled.show()
    time.sleep(1.5)

# ── Happy ────────────────────────────────────────────────

def happy():
    end_time = time.time() + 5
    while time.time() < end_time:
        def extras():
            draw_arc(64, 42, 10, 20, 160)
        blink(extras)

# ── Normal ───────────────────────────────────────────────

def normal():
    end_time = time.time() + 5
    while time.time() < end_time:
        def extras():
            oled.hline(45, 50, 38, 1)
        blink(extras)

# ── Sad ──────────────────────────────────────────────────

def sad():
    end_time = time.time() + 5
    while time.time() < end_time:
        def extras():
            draw_arc(64, 52, 10, 200, 340)
        blink(extras)

# ── Angry ────────────────────────────────────────────────

def angry():
    end_time = time.time() + 5
    while time.time() < end_time:
        def extras():
            oled.line(28, 10, 52, 18, 1)
            oled.line(76, 18, 100, 10, 1)
            draw_arc(64, 52, 10, 200, 340)
        blink(extras)

# ── Disgust ──────────────────────────────────────────────

EYE_R = 12
PUPIL_R = 5
ROLL_R = EYE_R - PUPIL_R - 1

def disgust():
    end_time = time.time() + 5
    while time.time() < end_time:
        # one eye roll
        angle = 0
        while angle < 2 * math.pi:
            oled.fill(0)
            px = int(math.cos(angle) * ROLL_R)
            py = int(math.sin(angle) * ROLL_R)
            draw_circle(42, 28, EYE_R)
            draw_circle(86, 28, EYE_R)
            fill_circle(42 + px, 28 + py, PUPIL_R)
            fill_circle(86 + px, 28 + py, PUPIL_R)
            oled.hline(28, 10, 24, 1)
            oled.line(76, 8, 100, 13, 1)
            oled.line(45, 52, 55, 48, 1)
            oled.line(55, 48, 65, 52, 1)
            oled.line(65, 52, 75, 48, 1)
            oled.line(75, 48, 85, 52, 1)
            oled.show()
            angle += 0.9
            time.sleep(0.05)
            if time.time() >= end_time:
                break

        # blink after roll
        oled.fill(0)
        oled.hline(30, 28, 24, 1)    # left eye closed
        oled.hline(74, 28, 24, 1)    # right eye closed
        oled.hline(28, 10, 24, 1)
        oled.line(76, 8, 100, 13, 1)
        oled.line(45, 52, 55, 48, 1)
        oled.line(55, 48, 65, 52, 1)
        oled.line(65, 52, 75, 48, 1)
        oled.line(75, 48, 85, 52, 1)
        oled.show()
        time.sleep(0.15)             # blink duration

# ── Main loop ────────────────────────────────────────────

while True:
    happy()
    normal()
    sad()
    angry()
    disgust()