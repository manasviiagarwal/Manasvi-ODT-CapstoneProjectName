from machine import Pin, I2C
import sh1106
import framebuf

WIDTH = 128
HEIGHT = 64

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
oled = sh1106.SH1106_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, rotate=180)

try:
    oled.sleep(False)
except:
    pass

def draw_big_text(display, text, x, y, scale=2):
    w = 8 * len(text)
    h = 8

    buf = bytearray(w * h)
    fb = framebuf.FrameBuffer(buf, w, h, framebuf.MONO_VLSB)
    fb.text(text, 0, 0, 1)

    for i in range(w):
        for j in range(h):
            if fb.pixel(i, j):
                display.fill_rect(x + i*scale, y + j*scale, scale, scale, 1)

def center_big_text(display, text, scale=2):
    text_w = len(text) * 8 * scale
    text_h = 8 * scale
    x = (WIDTH - text_w) // 2
    y = (HEIGHT - text_h) // 2
    draw_big_text(display, text, x, y, scale)

oled.fill(0)
center_big_text(oled, "Manasvi loves Aditya")
oled.show()