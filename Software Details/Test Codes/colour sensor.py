

# ═══════════════════════════════════════════════════════════
# TCS3200 COLOUR SENSOR — STANDALONE TEST
# MicroPython ESP32
# ═══════════════════════════════════════════════════════════
#
# WIRING:
#   S0  → GPIO 14      S1  → GPIO 32
#   S2  → GPIO 16      S3  → GPIO 17
#   OUT → GPIO 34      VCC → 3.3V    GND → GND
#
# USAGE:
#   1. Flash this file as main.py (or run via Thonny REPL)
#   2. Open the serial monitor (115200 baud)
#   3. Hold each colour swatch flat under the sensor (~2-3 cm)
#   4. Watch the printed R/G/B frequencies and detected colour
#   5. Adjust the thresholds in classify_color() to match your
#      readings if the detection is wrong
# ═══════════════════════════════════════════════════════════
 
from machine import Pin, Timer
import utime as time
 
 
# ═══════════════════════════════════════════════════════════
# TCS3200 DRIVER CLASS
# ═══════════════════════════════════════════════════════════
 
class TCS3200(object):
 
    ON  = True
    OFF = False
 
    # Filter (S2, S3)
    RED   = (0, 0)
    BLUE  = (0, 1)
    GREEN = (1, 1)
    CLEAR = (1, 0)
 
    RED_COMP   = 0
    GREEN_COMP = 1
    BLUE_COMP  = 2
    CLEAR_COMP = 3
 
    # Frequency scaling (S0, S1)
    POWER_OFF       = (0, 0)
    TWO_PERCENT     = (0, 1)
    TWENTY_PERCENT  = (1, 0)
    HUNDRED_PERCENT = (1, 1)
 
    def __init__(self, OUT=34, S2=5, S3=17, S0=15, S1=4, LED=None, OE=None):
        # GPIO 34 is input-only on ESP32 — no PULL_UP
        self._OUT = Pin(OUT, Pin.IN)
        self._S2  = Pin(S2,  Pin.OUT)
        self._S3  = Pin(S3,  Pin.OUT)
 
        self._S0  = Pin(S0, Pin.OUT) if S0 is not None else None
        self._S1  = Pin(S1, Pin.OUT) if S1 is not None else None
        self._LED = None
        self._OE  = None
 
        if LED is not None:
            self._LED = Pin(LED, Pin.OUT)
            self._LED.on()
        if OE is not None:
            self._OE = Pin(OE, Pin.OUT)
 
        self._tim        = Timer(0)
        self._timeout    = 5000
        self._cycles     = 100
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
        if not self._S0 or not self._S1:
            return None
        return (self._S0.value(), self._S1.value())
 
    @freq_divider.setter
    def freq_divider(self, freq_div):
        if self._S0 and self._S1:
            self._S0.value(freq_div[0])
            self._S1.value(freq_div[1])
 
    @property
    def cycles(self):
        return self._cycles
 
    @cycles.setter
    def cycles(self, n):
        if n >= 1:
            self._cycles = n
 
    @property
    def meas(self):
        return self._meas
 
    @meas.setter
    def meas(self, startStop):
        if startStop:
            self._meas       = True
            self._cycle      = 0
            self._start_tick = 0
            self._end_tick   = 0
            self._OUT.irq(trigger=Pin.IRQ_RISING, handler=self._cbf)
            self._tim.init(period=self._timeout, mode=Timer.ONE_SHOT,
                           callback=self._timeout_handler)
        else:
            self._meas = False
            self._OUT.irq(trigger=Pin.IRQ_RISING, handler=None)
            self._tim.deinit()
 
    @property
    def measured_freq(self):
        duration = self._end_tick - self._start_tick
        return 1_000_000 * self._cycles / duration

    @property
    def meas_freqs(self):
        filters = (self.RED, self.GREEN, self.BLUE, self.CLEAR)
        freqs   = [0.0] * 4
        for i in range(4):
            self.meas   = self.OFF          # hard-reset IRQ before each channel
            self.filter = filters[i]
            time.sleep_ms(10)              # let filter settle
            self._end_tick = 0
            self._cycle    = 0             # force-reset cycle counter
            self.meas      = self.ON
            t0 = time.ticks_ms()
            while self._end_tick == 0:
                if time.ticks_diff(time.ticks_ms(), t0) > 3000:
                    return [0.0, 0.0, 0.0, 0.0]   # graceful fallback, no crash
                time.sleep_ms(5)
            freqs[i] = self.measured_freq
        return freqs
    def _cbf(self, src):
        t = time.ticks_us()
        if self._cycle == 0:
            self._start_tick = t
        if self._cycle >= self._cycles:
            self._end_tick = t
            self.meas = self.OFF
            return
        self._cycle += 1
 
    def _timeout_handler(self, src):
        self._OUT.irq(trigger=Pin.IRQ_RISING, handler=None)
        raise Exception("TCS3200 timeout!")
 
 
# ═══════════════════════════════════════════════════════════
# SENSOR SETUP
# ═══════════════════════════════════════════════════════════
 
sensor = TCS3200(OUT=34, S2=16, S3=17, S0=14, S1=32)
sensor.freq_divider = TCS3200.TWENTY_PERCENT   # 20% — good balance of speed vs accuracy
sensor.cycles       = 50                       # fewer cycles = faster reading; increase for stability
 
 
# ═══════════════════════════════════════════════════════════
# COLOUR CLASSIFICATION
# ═══════════════════════════════════════════════════════════
#
# HOW TO TUNE:
#   Run the loop below and note the R/G/B raw values printed
#   for each colour you test. Then set thresholds here so
#   that each colour's dominant channel is clearly above the
#   others before that branch is taken.
#
#   TCS3200 outputs HIGHER frequency for MORE of that colour.
#   A pure red card → R >> G, R >> B
#   A pure blue card → B >> R, B >> G
#   Yellow (red+green) → R ≈ G >> B
#   Orange → R > G >> B  (R notably higher than G)
#   Green → G >> R, G >> B
 
def classify_color(r, g, b):
    MIN_SIGNAL = 40    # raise this slightly to reject weak/noisy reads
    MAX_SIGNAL = 5000  # cap for saturated/no-target readings (all channels max out)

    if r < MIN_SIGNAL and g < MIN_SIGNAL and b < MIN_SIGNAL:
        return "black / no target"

    # If all channels are very high and similar → likely white or overexposed
    if r > MAX_SIGNAL and g > MAX_SIGNAL and b > MAX_SIGNAL:
        return "WHITE / too close"

    dominant = max(r, g, b)

    if r == dominant and r > g * 1.4 and r > b * 1.4:
        return "RED"

    if b == dominant and b > r * 1.4 and b > g * 1.4:
        return "BLUE"

    if g == dominant and g > r * 1.4 and g > b * 1.4:
        return "GREEN"

    if r > MIN_SIGNAL and g > MIN_SIGNAL and b < (min(r, g) * 0.5):
        if abs(r - g) < max(r, g) * 0.3:
            return "YELLOW"

    # ORANGE — now requires minimum signal to avoid false triggers
    if r > MIN_SIGNAL and r > g * 1.2 and b < r * 0.5:
        return "ORANGE"

    return "unknown"
 
 
# ═══════════════════════════════════════════════════════════
# TEST LOOP
# ═══════════════════════════════════════════════════════════
 
print("=" * 50)
print("  TCS3200 Colour Sensor Test")
print("  Wiring: S0=14 S1=32 S2=16 S3=17 OUT=34")
print("  Hold target ~2-3 cm below sensor")
print("=" * 50)
print()
 
last_color = ""
read_count = 0
 
while True:
    try:
        freqs = sensor.meas_freqs
        r, g, b, clear = freqs[0], freqs[1], freqs[2], freqs[3]
 
        color = classify_color(r, g, b)
        read_count += 1
 
        # Always print raw values so you can tune thresholds
        print(f"[{read_count:04d}]  R:{r:7.1f}  G:{g:7.1f}  B:{b:7.1f}  "
              f"Clear:{clear:7.1f}   → {color}")
 
        # Extra highlight when colour changes
        if color != last_color:
            print(f"         *** Colour changed: {last_color or 'start'} → {color} ***")
            last_color = color
 
        time.sleep_ms(500)   # 2 readings per second; lower for faster response
 
    except Exception as e:
        print(f"Sensor error: {e}")
        time.sleep_ms(1000)