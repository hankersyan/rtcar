import RPi.GPIO as GPIO
import time
from time import sleep
import threading

in1 = 24
in2 = 23
en = 25

in3 = 17
in4 = 27
en2 = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(in1, GPIO.OUT)
GPIO.setup(in2, GPIO.OUT)
GPIO.setup(en, GPIO.OUT)
GPIO.output(in1, GPIO.LOW)
GPIO.output(in2, GPIO.LOW)

GPIO.setup(in3, GPIO.OUT)
GPIO.setup(in4, GPIO.OUT)
GPIO.setup(en2, GPIO.OUT)
GPIO.output(in3, GPIO.LOW)
GPIO.output(in4, GPIO.LOW)
p = GPIO.PWM(en, 1000)
p2 = GPIO.PWM(en2, 1000)

last_action_time = 0
t = 0

def stop_thread():
    while(last_action_time >= 0):
        ts = time.time() * 1000
        if (ts >= last_action_time):
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.LOW)
            GPIO.output(in3, GPIO.LOW)
            GPIO.output(in4, GPIO.LOW)
        sleep(0.5)

class Motor(object):
    def __init__(self):
        p.start(25)
        p2.start(25)
        t = threading.Thread(target=stop_thread)
        t.start()
        #t.join()
        print("\n")
        print("The default speed & direction of motor is LOW & Forward.....")
        print("w-forward s-backward a-left d-right l-low m-medium h-high e-exit")
        print("\n")

    def ahead(self):
        last_action_time = time.time() * 1000
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.HIGH)
        GPIO.output(in4, GPIO.LOW)

    def rear(self):
        last_action_time = time.time() * 1000
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.HIGH)

    def right(self):
        last_action_time = time.time() * 1000
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.HIGH)

    def left(self):
        last_action_time = time.time() * 1000
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.HIGH)
        GPIO.output(in4, GPIO.LOW)

    def stop(self):
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.LOW)

    def quit(self):
        GPIO.cleanup()
        last_action_time = -1

    def slow(self):
        p.ChangeDutyCycle(25)
        p2.ChangeDutyCycle(25)

    def medium(self):
        p.ChangeDutyCycle(50)
        p2.ChangeDutyCycle(50)

    def high(self):
        p.ChangeDutyCycle(75)
        p2.ChangeDutyCycle(75)
