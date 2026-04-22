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

IR = Pin(18, Pin.IN)

def stop():
    IN1.value(0)
    IN2.value(0)
    IN3.value(0)
    IN4.value(0)

def turn_right():
    # Left wheel forward, right wheel back
    IN1.value(1)
    IN2.value(0)
    IN3.value(0)
    IN4.value(0)
    time.sleep(0.1)
    stop()
    
    

def turn_left():
    # Left wheel back, right wheel forward
    IN1.value(0)
    IN2.value(0)
    IN3.value(1)
    IN4.value(0)
    time.sleep(0.1)
    stop()
    
    

while True:
    if IR.value() == 1:
        # light detected
        turn_right()
        
        
        
    else:
        # no light
        turn_left()

    time.sleep_ms(50)

