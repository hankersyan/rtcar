from gpiozero import DistanceSensor
from time import sleep

Sensor = DistanceSensor(echo=21, trigger=20)

while True:
	print(Sensor.distance)
	sleep(1)