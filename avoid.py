from gpiozero import Robot, DistanceSensor
from signal import pause

sensor = DistanceSensor(20, 21, max_distance=1, threshold_distance=0.2)
robot = Robot(left=(24, 23), right=(17, 27))

sensor.when_in_range = robot.backward
sensor.when_out_of_range = robot.stop
pause()