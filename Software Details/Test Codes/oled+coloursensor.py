# ═══════════════════════════════════════════════════════════
# TCS3200 + SH1106 OLED — Emotion Face by Colour
# Green→Disgust  Blue→Sad  Red→Angry  Yellow→Happy
# MicroPython ESP32
# ═══════════════════════════════════════════════════════════
#
# WIRING:
#   TCS3200: S0=14  S1=32  S2=16  S3=17  OUT=34
#   OLED:    SCL=22  SDA=21  VCC=3.3V  GND=GND
# ═══════════════════════════════════════════════════════════

from machine import Pin, Timer, I2C
import sh1106
import math
import utime as time

# ═══════════════════════════════════════════════════════════
# OLED SETUP
# ═══════════════════════════════════════════════════════════

WIDTH  = 128
HEIGHT = 64
i2c  = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
oled = sh1106.SH1106_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, rotate=180)
try:
    oled.sleep(False)
except:
    pass


# ═══════════════════════════════════════════════════════════
# TCS3200 DRIVER
# ═══════════════════════════════════════════════════════════

class TCS3200:
    ON  = True
    OFF = False

    RED            = (0, 0)
    BLUE           = (0, 1)
    GREEN          = (1, 1)
    TWENTY_PERCENT = (1, 0)

    def __init__(self, OUT=34, S2=16, S3=17, S0=14, S1=32):
        self._OUT = Pin(OUT, Pin.IN)
        self._S2  = Pin(S2,  Pin.OUT)
        self._S3  = Pin(S3,  Pin.OUT)
        self._S0  = Pin(S0,  Pin.OUT)
        self._S1  = Pin(S1,  Pin.OUT)

        self._tim        = Timer(0)
        self._timeout    = 5000
        self._cycles     = 50
        self._cycle      = 0
        self._start_tick = 0
        self._end_tick   = 0
        self._meas       = False

    @property
    def filter(self):
        return (self._S2.value(), self._S3.value())

    @filter.setter
    def filter(self, setting):
        self._S2.value(setting[0])
        self._S3.value(setting[1])

    @property
    def freq_divider(self):
        return (self._S0.value(), self._S1.value())

    @freq_divider.setter
    def freq_divider(self, fd):
        self._S0.value(fd[0])
        self._S1.value(fd[1])

    @property
    def meas(self):
        return self._meas

    @meas.setter
    def meas(self, start):
        if start:
            self._meas       = True
            self._cycle      = 0
            self._start_tick = 0
            self._end_tick   = 0
            self._OUT.irq(trigger=Pin.IRQ_RISING, handler=self._cbf)
            self._tim.init(period=self._timeout, mode=Timer.ONE_SHOT,
                           callback=self._timeout_cb)
        else:
            self._meas = False
            self._OUT.irq(trigger=Pin.IRQ_RISING, handler=None)
            self._tim.deinit()

    @property
    def measured_freq(self):
        duration = self._end_tick - self._start_tick
        return 1_000_000 * self._cycles / duration

    def read_rgb(self):
        filters = (self.RED, self.GREEN, self.BLUE)
        freqs   = []
        for f in filters:
            self.meas   = self.OFF
            self.filter = f
            time.sleep_ms(10)
            self._end_tick = 0
            self._cycle    = 0
            self.meas      = self.ON
            t0 = time.ticks_ms()
            while self._end_tick == 0:
                if time.ticks_diff(time.ticks_ms(), t0) > 3000:
                    return (0.0, 0.0, 0.0)
                time.sleep_ms(5)
            freqs.append(self.measured_freq)
        return tuple(freqs)

    def _cbf(self, src):
        t = time.ticks_us()
        if self._cycle == 0:
            self._start_tick = t
        if self._cycle >= self._cycles:
            self._end_tick = t
            self.meas = self.OFF
            return
        self._cycle += 1

    def _timeout_cb(self, src):
        self._OUT.irq(trigger=Pin.IRQ_RISING, handler=None)
        raise Exception("TCS3200 timeout!")


# ═══════════════════════════════════════════════════════════
# SENSOR INIT
# ═══════════════════════════════════════════════════════════

sensor = TCS3200(OUT=34, S2=16, S3=17, S0=14, S1=32)
sensor.freq_divider = TCS3200.TWENTY_PERCENT


# ═══════════════════════════════════════════════════════════
# COLOUR CLASSIFICATION
# ═══════════════════════════════════════════════════════════

def classify_color(r, g, b):
    MIN_SIGNAL = 40

    if r < MIN_SIGNAL and g < MIN_SIGNAL and b < MIN_SIGNAL:
        return "UNKNOWN"

    dominant = max(r, g, b)

    if r == dominant and g > b * 1.03 and r < g * 2.2:
        return "YELLOW"

    if r == dominant and r > g * 1.4 and r > b * 1.4:
        return "RED"

    if g == min(r, g, b) and (b - g) > 90 and b > r * 1.15:
        return "BLUE"

    if g == min(r, g, b) and g > MIN_SIGNAL:
        return "GREEN"

    if max(r, g, b) / min(r, g, b) < 1.35:
        return "UNKNOWN"

    return "UNKNOWN"


# ═══════════════════════════════════════════════════════════
# OLED DRAWING HELPERS
# ═══════════════════════════════════════════════════════════

EYE_R   = 12
PUPIL_R = 5
ROLL_R  = EYE_R - PUPIL_R - 1

def fill_circle(cx, cy, r, col=1):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        oled.hline(cx - dx, cy + dy, 2 * dx + 1, col)

def draw_circle(cx, cy, r):
    x, y, err = r, 0, 0
    while x >= y:
        oled.pixel(cx+x, cy+y, 1); oled.pixel(cx-x, cy+y, 1)
        oled.pixel(cx+x, cy-y, 1); oled.pixel(cx-x, cy-y, 1)
        oled.pixel(cx+y, cy+x, 1); oled.pixel(cx-y, cy+x, 1)
        oled.pixel(cx+y, cy-x, 1); oled.pixel(cx-y, cy-x, 1)
        y += 1
        err += 2 * y + 1
        if 2 * (err - x) + 1 > 0:
            x -= 1
            err += 1 - 2 * x

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
    oled.fill(0); eyes_open();   draw_extras(); oled.show(); time.sleep_ms(1500)
    oled.fill(0); eyes_closed(); draw_extras(); oled.show(); time.sleep_ms(150)
    oled.fill(0); eyes_open();   draw_extras(); oled.show(); time.sleep_ms(1500)


# ═══════════════════════════════════════════════════════════
# FACE ANIMATIONS
# ═══════════════════════════════════════════════════════════

def face_happy():
    def extras():
        draw_arc(64, 42, 10, 20, 160)
    blink(extras)

def face_sad():
    def extras():
        draw_arc(64, 52, 10, 200, 340)
    blink(extras)

def face_angry():
    def extras():
        oled.line(28, 10, 52, 18, 1)
        oled.line(76, 18, 100, 10, 1)
        draw_arc(64, 52, 10, 200, 340)
    blink(extras)

def face_disgust():
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
        time.sleep_ms(50)
    oled.fill(0)
    oled.hline(30, 28, 24, 1)
    oled.hline(74, 28, 24, 1)
    oled.show()
    time.sleep_ms(150)

def face_normal():
    """Default neutral face shown while scanning/confirming"""
    oled.fill(0)
    eyes_open()
    # flat mouth
    oled.hline(54, 48, 20, 1)
    oled.show()


# ═══════════════════════════════════════════════════════════
# COLOUR → FACE MAP
# ═══════════════════════════════════════════════════════════

FACE_MAP = {
    "RED":    face_angry,
    "BLUE":   face_sad,
    "GREEN":  face_disgust,
    "YELLOW": face_happy,
}


# ═══════════════════════════════════════════════════════════
# CONFIRMATION SETTINGS
# ═══════════════════════════════════════════════════════════

CONFIRM_TIME_MS = 3000   # colour must be seen for 3 seconds to confirm
                         # increase to 5000 if still too jumpy


# ═══════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════

print("=" * 52)
print("  TCS3200 + OLED  |  RED=Angry  BLUE=Sad")
print("                  |  GREEN=Disgust  YELLOW=Happy")
print("=" * 52)

candidate_color  = "UNKNOWN"   # colour currently being timed
candidate_start  = 0           # when we first saw it
confirmed_color  = "UNKNOWN"   # last confirmed colour
read_count       = 0

# show neutral face at startup
face_normal()

while True:
    try:
        r, g, b = sensor.read_rgb()
        color   = classify_color(r, g, b)
        read_count += 1

        print(f"[{read_count:04d}]  R:{r:7.1f}  G:{g:7.1f}  B:{b:7.1f}   → {color}")

        if color != candidate_color:
            # colour changed — reset the timer
            candidate_color = color
            candidate_start = time.ticks_ms()
            print(f"         Candidate reset → {color}")

        else:
            # same colour — check if held long enough
            elapsed = time.ticks_diff(time.ticks_ms(), candidate_start)

            if elapsed >= CONFIRM_TIME_MS and color != confirmed_color:
                # confirmed! only trigger if it's a real colour
                if color in FACE_MAP:
                    print(f"         *** CONFIRMED: {color} ***")
                    confirmed_color = color
                    FACE_MAP[color]()
                else:
                    # UNKNOWN held for 3s → go back to neutral
                    confirmed_color = "UNKNOWN"
                    face_normal()

            elif color not in FACE_MAP:
                # still unknown/scanning — keep showing neutral face
                face_normal()

    except Exception as e:
        print(f"Error: {e}")
        time.sleep_ms(1000)