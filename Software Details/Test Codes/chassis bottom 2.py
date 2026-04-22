from machine import Pin, PWM
import time

#LEFT MOTOR
IN1 = Pin(27, Pin.OUT)
IN2 = Pin(26, Pin.OUT)


#RIGHT MOTOR 
IN3 = Pin(25, Pin.OUT)
IN4 = Pin(33, Pin.OUT)



def move_forward():
    IN1.value(0); IN2.value(1)    # left forward
    IN3.value(0); IN4.value(1)    # right forward
    

def turn_left():
    IN1.value(0); IN2.value(0)    # left stop
    IN3.value(0); IN4.value(1)
    time.sleep(0.5)              # tune until clean 90 degrees
    stop()
# right forward
    

def turn_right():
    IN1.value(0); IN2.value(1)    # left forward
    IN3.value(0); IN4.value(0)
    time.sleep(0.5)               # tune until clean 90 degrees
    stop()
# right stop
    
def turn_around():
    IN1.value(1); IN2.value(0)    # left backward
    IN3.value(0); IN4.value(1)    # right forward
    time.sleep(0.65)
    stop()

def stop():
    IN1.value(0); IN2.value(0)
    IN3.value(0); IN4.value(0)
   

turn_right()
