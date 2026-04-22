from machine import Pin, PWM, I2C
import sh1106
import math
import utime as time

#MOTOR PINS
IN1 = Pin(27, Pin.OUT)
IN2 = Pin(26, Pin.OUT)
#ENA = PWM(Pin(14), freq=1000)

IN3 = Pin(25, Pin.OUT)
IN4 = Pin(33, Pin.OUT)
#ENB = PWM(Pin(32), freq=1000)

IR = Pin(18, Pin.IN)



# OLED
WIDTH, HEIGHT = 128, 64
i2c  = I2C(0, scl=Pin(22), sda=Pin(21), freq=100_000)
oled = sh1106.SH1106_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, rotate=180)
try:
    oled.sleep(False)
except Exception:
    pass

# TCS3200
class TCS3200:
    RED   = (0, 0)
    BLUE  = (0, 1)
    CLEAR = (1, 0)
    GREEN = (1, 1)

    POWER_DOWN      = (0, 0)
    TWO_PERCENT     = (0, 1)
    TWENTY_PERCENT  = (1, 0)
    HUNDRED_PERCENT = (1, 1)

    def __init__(self, OUT=34, S2=5, S3=17, S0=15, S1=4):
        self._OUT = Pin(OUT, Pin.IN)
        self._S2  = Pin(S2,  Pin.OUT)
        self._S3  = Pin(S3,  Pin.OUT)
        self._S0  = Pin(S0,  Pin.OUT)
        self._S1  = Pin(S1,  Pin.OUT)

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

    def _count_pulses(self, ms=120):
        count = 0
        last  = self._OUT.value()
        end_t = time.ticks_add(time.ticks_ms(), ms)
        while time.ticks_diff(end_t, time.ticks_ms()) > 0:
            v = self._OUT.value()
            if v == 1 and last == 0:
                count += 1
            last = v
        return count * (1000 // ms)

    def read_channel(self, filt):
        self.filter = filt
        time.sleep_ms(20)
        return self._count_pulses(120)

    def read_rgbc(self):
        r = self.read_channel(self.RED)
        g = self.read_channel(self.GREEN)
        b = self.read_channel(self.BLUE)
        c = self.read_channel(self.CLEAR)
        return r, g, b, c

sensor = TCS3200(OUT=34, S2=5, S3=17, S0=15, S1=4)
sensor.freq_divider = TCS3200.TWENTY_PERCENT
time.sleep_ms(1500)


def classify_color(r, g, b, clear):
    MIN_SIGNAL = 300   # raised from 80 — ignores weak/ambient readings

    if r < MIN_SIGNAL and g < MIN_SIGNAL and b < MIN_SIGNAL:
        return "UNKNOWN"

    total = r + g + b
    if total <= 0:
        return "UNKNOWN"

    rn = r / total
    gn = g / total
    bn = b / total
    spread = max(r, g, b) - min(r, g, b)

    # Overexposed / white
    if clear > 7000 and spread < 1800:
        return "UNKNOWN"

    # RED: rn dominant AND gn very low
    if rn > 0.44 and gn < 0.24:
        return "RED"

    # YELLOW: strong signal + rn clearly beats gn + meaningful spread
    if rn > gn * 1.25 and rn > 0.36 and gn >= 0.24 and bn < 0.32 and spread > 300 and r > 600:
        return "YELLOW"

    # GREEN: gn close to rn
    if gn >= rn * 0.88 and bn < gn * 1.12 and rn < 0.43:
        return "GREEN"

    # BLUE: bn dominant
    if bn > 0.40 and bn > rn * 1.12 and bn > gn * 1.12:
        return "BLUE"

    return "UNKNOWN"

#MOTOR MOTION
def stop():
    IN1.value(0)
    IN2.value(0)
    IN3.value(0)
    IN4.value(0)
  
def turn_right():
    IN1.value(1)
    IN2.value(0)
    IN3.value(0)
    IN4.value(0)
    time.sleep_ms(60)
    stop()

def turn_left():
    IN1.value(0)
    IN2.value(0)
    IN3.value(1)
    IN4.value(0)
    time.sleep_ms(60)
    stop()

# OLED CODES
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
        y += 1; err += 2 * y + 1
        if 2 * (err - x) + 1 > 0:
            x -= 1; err += 1 - 2 * x

def draw_arc(cx, cy, r, start_deg, end_deg):
    steps = 40
    for i in range(steps + 1):
        angle = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        oled.pixel(int(cx + r * math.cos(angle)),
                   int(cy + r * math.sin(angle)), 1)

def eyes_open():
    fill_circle(42, 28, 12)
    fill_circle(86, 28, 12)

def eyes_closed():
    oled.hline(30, 28, 24, 1)
    oled.hline(74, 28, 24, 1)

EYE_R   = 12
PUPIL_R = 5
ROLL_R  = EYE_R - PUPIL_R - 1

def draw_emotion_frame(emotion, blinking, disgust_angle=0.0):
    oled.fill(0)
    if emotion == "DISGUST":
        draw_circle(42, 28, EYE_R)
        draw_circle(86, 28, EYE_R)
        if blinking:
            oled.hline(30, 28, 24, 1)
            oled.hline(74, 28, 24, 1)
        else:
            px = int(math.cos(disgust_angle) * ROLL_R)
            py = int(math.sin(disgust_angle) * ROLL_R)
            fill_circle(42 + px, 28 + py, PUPIL_R)
            fill_circle(86 + px, 28 + py, PUPIL_R)
        oled.hline(28, 10, 24, 1)
        oled.line(76, 8, 100, 13, 1)
        oled.line(45, 52, 55, 48, 1)
        oled.line(55, 48, 65, 52, 1)
        oled.line(65, 52, 75, 48, 1)
        oled.line(75, 48, 85, 52, 1)
    else:
        if blinking:
            eyes_closed()
        else:
            eyes_open()
        if emotion == "HAPPY":
            draw_arc(64, 42, 10, 20, 160)
        elif emotion == "SAD":
            draw_arc(64, 52, 10, 200, 340)
        elif emotion == "ANGRY":
            oled.line(28, 10, 52, 18, 1)
            oled.line(76, 18, 100, 10, 1)
            draw_arc(64, 52, 10, 200, 340)
        else:
            oled.hline(45, 50, 38, 1)
    oled.show()

# EMOTION MAPPING
EMOTION_MAP = {
    "RED":    "ANGRY",
    "GREEN":  "DISGUST",
    "BLUE":   "SAD",
    "YELLOW": "HAPPY",
}


current_emotion  = "NORMAL"
STARTUP_SKIP     = 2
CONFIRM_COUNT    = 2
reads_done       = 0
color_buffer     = []
last_color_ms    = time.ticks_ms()
COLOR_INTERVAL   = 600
last_blink_ms    = time.ticks_ms()
BLINK_INTERVAL   = 3000
BLINK_DURATION   = 150
blinking         = False
blink_end_ms     = 0
disgust_angle    = 0.0
DISGUST_STEP     = 0.9
last_disgust_ms  = time.ticks_ms()
DISGUST_FRAME_MS = 50

# MAIN LOOP
print("Emotion robot started. Warming up colour sensor...")

while True:
    now = time.ticks_ms()

    # 1. Line following
    if IR.value() == 1:
        turn_left()
        print("noobkack")
    else:
        turn_right()
        print("black")

    # 2. Colour reading
    if time.ticks_diff(now, last_color_ms) >= COLOR_INTERVAL:
        r, g, b, clear = sensor.read_rgbc()
        detected = classify_color(r, g, b, clear)
        last_color_ms = time.ticks_ms()
        reads_done += 1
        print("Read {}: R:{:.0f} G:{:.0f} B:{:.0f} -> {}".format(
              reads_done, r, g, b, detected))

        if reads_done <= STARTUP_SKIP:
            print("Startup skip [{}/{}]: {} (ignored)".format(
                  reads_done, STARTUP_SKIP, detected))
        else:
            color_buffer.append(detected)
            if len(color_buffer) > CONFIRM_COUNT:
                color_buffer.pop(0)
            if (len(color_buffer) == CONFIRM_COUNT and
                    all(c == color_buffer[0] for c in color_buffer)):
                if detected == "UNKNOWN":
                    if current_emotion != "NORMAL":
                        current_emotion = "NORMAL"
                        disgust_angle   = 0.0
                        print("Emotion → NORMAL")
                else:
                    new_emotion = EMOTION_MAP.get(detected, "NORMAL")
                    if new_emotion != current_emotion:
                        current_emotion = new_emotion
                        disgust_angle   = 0.0
                        print("Emotion → {} (from {})".format(
                              current_emotion, detected))
                color_buffer.clear()

    # 3. Blink timer
    if not blinking and time.ticks_diff(now, last_blink_ms) >= BLINK_INTERVAL:
        blinking     = True
        blink_end_ms = time.ticks_add(now, BLINK_DURATION)
    if blinking and time.ticks_diff(now, blink_end_ms) >= 0:
        blinking      = False
        last_blink_ms = now

    # 4. Disgust eye-roll
    if current_emotion == "DISGUST":
        if time.ticks_diff(now, last_disgust_ms) >= DISGUST_FRAME_MS:
            disgust_angle   = (disgust_angle + DISGUST_STEP) % (2 * math.pi)
            last_disgust_ms = now

    # 5. Render OLED
    try:
        draw_emotion_frame(current_emotion, blinking, disgust_angle)
    except Exception as e:
        print("OLED error:", e)
        oled.fill(0)
        oled.show()

    time.sleep_ms(50)
