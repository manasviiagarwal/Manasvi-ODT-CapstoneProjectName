from machine import Pin, time_pulse_us
import time

# Front sensor
trig_f = Pin(12, Pin.OUT)
echo_f = Pin(13 ,  Pin.IN)

# Left sensor
#trig_l = Pin(17, Pin.OUT)
#echo_l = Pin(5, Pin.IN)

# Right sensor
#trig_r = Pin(18, Pin.OUT)
#echo_r = Pin(19, Pin.IN)

def get_distance(trig, echo):
    trig.off()
    time.sleep_us(2)
    trig.on()
    time.sleep_us(10)
    trig.off()
    
    duration = time_pulse_us(echo, 1, 30000)
    
    time.sleep_ms(10)
    
    if duration < 0:
        return 999
    return duration / 58

while True:
    f = get_distance(trig_f, echo_f)
    #l = get_distance(trig_l, echo_l)
    #r = get_distance(trig_r, echo_r)
    
    print(f"Front: {f:.1f}cm")
    time.sleep(0.5)