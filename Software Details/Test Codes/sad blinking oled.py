from machine import Pin, I2C
import sh1106
import framebuf
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

def draw_arc(cx, cy, r, start_deg, end_deg):
    steps = 40
    for i in range(steps + 1):
        angle = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        x = int(cx + r * math.cos(angle))
        y = int(cy + r * math.sin(angle))
        oled.pixel(x, y, 1)

# ── Face parts ───────────────────────────────────────────

def eyes_open():
    fill_circle(42, 28, 12, 1)    # left eye
    fill_circle(86, 28, 12, 1)    # right eye

def eyes_closed():
    oled.hline(30, 28, 24, 1)     # left eye closed (flat line)
    oled.hline(74, 28, 24, 1)     # right eye closed (flat line)

def draw_sad():
    draw_arc(64, 52, 10, 200, 340) # sad

# ── Main blink loop ──────────────────────────────────────

def blink_forever():
    while True:
        # eyes open
        oled.fill(0)
        eyes_open()
        draw_sad()
        oled.show()
        time.sleep(2)             # open for 2 seconds

        # eyes closed (blink)
        oled.fill(0)
        eyes_closed()
        draw_sad()
        oled.show()
        time.sleep(0.15)          # blink lasts 0.15 seconds

blink_forever()