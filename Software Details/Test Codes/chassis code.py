from machine import Pin, PWM
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
TURN_SPEED = 500

def set_speed(left, right):
    ENA.duty(left)
    ENB.duty(right)

def move_forward():
    IN1.value(1)
    IN2.value(0)    # left forward
    IN3.value(1)
    IN4.value(0)    # right forward
    set_speed(FULL_SPEED, FULL_SPEED)

def turn_left(): #0.6 seconds
    IN1.value(0)
    IN2.value(1)    # left stop
    IN3.value(1)
    IN4.value(0)    # right forward
    set_speed(450, 500) #have to keep full speed n not turn speed because with such less speed its not moving however left motor is.

def turn_right(): #0.63 seconds
    IN1.value(1)
    IN2.value(0)    # left forward
    IN3.value(0)
    IN4.value(1)    # right stop
    set_speed(TURN_SPEED, TURN_SPEED)
    

def turn_around():
    IN1.value(0)
    IN2.value(1)    # left backward
    IN3.value(1)
    IN4.value(0)    # right forward
    set_speed(TURN_SPEED, TURN_SPEED)


def stop():
    IN1.value(0); IN2.value(0)
    IN3.value(0); IN4.value(0)
    set_speed(0, 0)

turn_left()
time.sleep(0.5)
stop()
#time.sleep(0.63)
