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

# ── Face parts ───────────────────────────────────────────

# eye center x, eye center y, eye radius, pupil radius
EYE_R = 12
PUPIL_R = 5
ROLL_R = EYE_R - PUPIL_R - 1   # how far pupil center moves from eye center = 6

def draw_eyes(angle_rad):
    # pupil position calculated using angle on a circle
    px = int(math.cos(angle_rad) * ROLL_R)
    py = int(math.sin(angle_rad) * ROLL_R)

    draw_circle(42, 28, EYE_R)           # hollow left eye (fixed)
    draw_circle(86, 28, EYE_R)           # hollow right eye (fixed)
    fill_circle(42 + px, 28 + py, PUPIL_R)   # left pupil rolling
    fill_circle(86 + px, 28 + py, PUPIL_R)   # right pupil rolling

def draw_disgust_brows():
    oled.hline(28, 10, 24, 1)
    oled.line(76, 8, 100, 13, 1)

def draw_wavy_mouth():
    oled.line(45, 52, 55, 48, 1)
    oled.line(55, 48, 65, 52, 1)
    oled.line(65, 52, 75, 48, 1)
    oled.line(75, 48, 85, 52, 1)

# ── Eye roll loop ─────────────────────────────────────────

def disgust_eyeroll_forever():
    while True:
        # do one full eye roll
        angle = 0
        while angle < 2 * math.pi:
            oled.fill(0)
            draw_eyes(angle)
            draw_disgust_brows()
            draw_wavy_mouth()
            oled.show()
            angle += 0.9             # faster roll!
            time.sleep(0.05)

        # blink after roll
        oled.fill(0)
        oled.hline(30, 28, 24, 1)    # left eye closed
        oled.hline(74, 28, 24, 1)    # right eye closed
        draw_disgust_brows()
        draw_wavy_mouth()
        oled.show()
        time.sleep(0.15)             # blink duration

        # then roll again
        time.sleep(0.3)              # tiny pause before next roll

disgust_eyeroll_forever()