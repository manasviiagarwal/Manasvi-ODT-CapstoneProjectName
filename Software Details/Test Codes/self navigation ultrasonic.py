from machine import Pin,PWM, time_pulse_us
import time


#LEFT MOTOR
IN1 = Pin(27, Pin.OUT)
IN2 = Pin(26, Pin.OUT)
ENA = PWM(Pin(14), freq=1000)

#RIGHT MOTOR 
IN3 = Pin(25, Pin.OUT)
IN4 = Pin(33, Pin.OUT)
ENB = PWM(Pin(32), freq=1000)

FULL_SPEED = 600
TURN_SPEED = 400
SPEED = 300


trig = Pin(12,  Pin.OUT)
echo = Pin(13,  Pin.IN)

SAFE_DISTANCE = 20
APPROACH = 35


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

def set_speed(left, right):
    ENA.duty(left)
    ENB.duty(right)

def move_forward():
    IN1.value(1)
    IN2.value(0)    # left forward
    IN3.value(1)
    IN4.value(0)    # right forward
    set_speed(FULL_SPEED, FULL_SPEED)
    
def move_forward_approach():
    IN1.value(1)
    IN2.value(0)    # left forward
    IN3.value(1)
    IN4.value(0)    # right forward
    set_speed(SPEED, SPEED)

def turn_left(): #0.6 seconds
    IN1.value(0)
    IN2.value(1)    # left stop
    IN3.value(1)
    IN4.value(0)
    # right forward
    set_speed(TURN_SPEED, TURN_SPEED)
    time.sleep(0.8)              # tune until 90 degrees
    stop()#have to keep full speed n not turn speed because with such less speed its not moving however left motor is.

def turn_right(): #0.63 seconds
    IN1.value(1)
    IN2.value(0)    # left forward
    IN3.value(0)
    IN4.value(1)    # right stop
    set_speed(TURN_SPEED, TURN_SPEED)
    time.sleep(0.8)              # tune until 90 degrees
    stop()

def stop():
    IN1.value(0); IN2.value(0)
    IN3.value(0); IN4.value(0)
    set_speed(0, 0)
# ─── MAIN LOOP ───────────────────────────────────────────
stop()
time.sleep(1)

while True:
    
    dist = get_distance(trig,echo)
    print("Distance:", dist)
    
    if dist > APPROACH:
        move_forward()
    
    elif dist > SAFE_DISTANCE and dist < APPROACH:
        move_forward_approach()

    elif dist < SAFE_DISTANCE:
        
        # Obstacle detected → stop and figure out where to go
        stop()
        time.sleep(1)

        # Try left first
        turn_left()
        time.sleep(1)
        
        dist = get_distance(trig,echo)# small pause before checking

        if dist > SAFE_DISTANCE:
            move_forward()

        else:
            # Left blocked → try right (turn right twice from left position
            # = back to original + one right = facing right)
            turn_right()
            time.sleep(0.5)
            turn_right()
            time.sleep(1)
            
            dist = get_distance(trig,echo)

            if dist > SAFE_DISTANCE:
                move_forward()

            else:
                # Right also blocked → turn right once more = facing back
                turn_right()
                time.sleep(1)
                

    time.sleep(0.1)



