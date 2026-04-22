from machine import Pin, time_pulse_us
import time

# ─── MOTORS ──────────────────────────────────────────────
IN1 = Pin(27, Pin.OUT)
IN2 = Pin(26, Pin.OUT)
IN3 = Pin(25, Pin.OUT)
IN4 = Pin(33, Pin.OUT)

# ─── ULTRASONIC SENSORS ──────────────────────────────────
TRIG_F = Pin(5,  Pin.OUT)
ECHO_F = Pin(4,  Pin.IN)

TRIG_L = Pin(23, Pin.OUT)
ECHO_L = Pin(15, Pin.IN)

TRIG_R = Pin(13, Pin.OUT)
ECHO_R = Pin(12, Pin.IN)

SAFE_DISTANCE = 20

# ─── GET DISTANCE ────────────────────────────────────────
def get_distance(trig, echo):
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    duration = time_pulse_us(echo, 1, 30000)
    if duration < 0:
        return 999
    return (duration * 0.0343) / 2

# ─── MOTORS ──────────────────────────────────────────────
def stop():
    IN1.value(0); IN2.value(0)
    IN3.value(0); IN4.value(0)

def move_forward():
    IN1.value(1); IN2.value(0)
    IN3.value(1); IN4.value(0)

def turn_left():
    IN1.value(0); IN2.value(1)
    IN3.value(1); IN4.value(0)
    time.sleep(0.5)
    stop()

def turn_right():
    IN1.value(1); IN2.value(0)
    IN3.value(0); IN4.value(1)
    time.sleep(0.5)
    stop()

def turn_around():
    IN1.value(0); IN2.value(1)
    IN3.value(1); IN4.value(0)
    time.sleep(0.65)
    stop()

# ─── MAIN LOOP ───────────────────────────────────────────
stop()

while True:
    l = get_distance(TRIG_L, ECHO_L)
    f = get_distance(TRIG_F, ECHO_F)
    r = get_distance(TRIG_R, ECHO_R)

    print(f"L:{l:.1f}  F:{f:.1f}  R:{r:.1f}")

    if l > SAFE_DISTANCE:
        stop(); turn_left(); move_forward()
    elif f > SAFE_DISTANCE:
        move_forward()
    elif r > SAFE_DISTANCE:
        stop(); turn_right(); move_forward()
    else:
        stop(); turn_around(); move_forward()

    time.sleep(0.1)