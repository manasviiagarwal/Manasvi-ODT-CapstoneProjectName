# ═══════════════════════════════════════════════════════════
# TCS3200 COLOUR SENSOR ONLY — MicroPython ESP32
# ═══════════════════════════════════════════════════════════
#
# REAL WIRING:
#   S0  → GPIO 15
#   S1  → GPIO 4
#   S2  → GPIO 5
#   S3  → GPIO 17
#   OUT → GPIO 34
#   VCC → 3.3V
#   GND → GND
#
# Notes:
# - 20% frequency scaling is used
# - Wait ~2.5s after power-up for settle / white balance
# - Best results usually come with low ambient light and close range
# ═══════════════════════════════════════════════════════════

from machine import Pin
import utime as time


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
        self._S2  = Pin(S2, Pin.OUT)
        self._S3  = Pin(S3, Pin.OUT)
        self._S0  = Pin(S0, Pin.OUT)
        self._S1  = Pin(S1, Pin.OUT)

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
        last = self._OUT.value()
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
time.sleep_ms(2500)


def classify_color(r, g, b, clear):
    MIN_SIGNAL = 80

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

    # RED: rn dominant AND gn very low (< 0.24)
    if rn > 0.44 and gn < 0.24:
        return "RED"

    # YELLOW: rn dominant but gn is higher (>= 0.24)
    if rn > gn * 1.15 and rn > 0.33 and gn >= 0.24 and bn < 0.32:
        return "YELLOW"

    # GREEN: gn >= rn (green matches or beats red)
    if gn >= rn * 0.95 and bn < gn * 1.10 and rn < 0.40:
        return "GREEN"

    # BLUE: bn dominant
    if bn > 0.40 and bn > rn * 1.12 and bn > gn * 1.12:
        return "BLUE"

    return "UNKNOWN"


print("=" * 60)
print("TCS3200 COLOUR SENSOR TEST")
print("Pins: S0=15  S1=4  S2=5  S3=17  OUT=34")
print("Hold colour target under sensor and watch the values")
print("=" * 60)

count = 0

while True:
    r, g, b, clear = sensor.read_rgbc()
    color = classify_color(r, g, b, clear)

    total = r + g + b
    if total > 0:
        rn = r / total
        gn = g / total
        bn = b / total
    else:
        rn = gn = bn = 0

    count += 1
    print("[{:04d}] R:{:7.1f} G:{:7.1f} B:{:7.1f} C:{:7.1f}  rn:{:.3f} gn:{:.3f} bn:{:.3f}  -> {}".format(
        count, r, g, b, clear, rn, gn, bn, color
    ))

    time.sleep_ms(500)