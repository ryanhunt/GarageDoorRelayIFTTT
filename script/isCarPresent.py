#!/usr/bin/python3
# Credit to Matt Hawkins
# http://www.raspberrypi-spy.co.uk/tag/ultrasonic/
# -----------------------
from __future__ import print_function
import time
import RPi.GPIO as GPIO

# -----------------------
# Define some functions
# -----------------------
def measure():
	# This function measures a distance
	GPIO.output(GPIO_TRIGGER, True)
	# Wait 10us
	time.sleep(0.00001)
	GPIO.output(GPIO_TRIGGER, False)
	start = time.time()
	
	while GPIO.input(GPIO_ECHO)==0:
		start = time.time()
	
	while GPIO.input(GPIO_ECHO)==1:
		stop = time.time()
	
	elapsed = stop-start
	distance = (elapsed * speedSound)/2
	
	return distance
	
def measure_average():
	# This function takes 3 measurements and
	# returns the average.
	
	distance1=measure()
	time.sleep(0.1)
	distance2=measure()
	time.sleep(0.1)
	distance3=measure()
	distance = distance1 + distance2 + distance3
	distance = distance / 3
	return distance
  
# Check if car is present
# Rough car height at lowest point is ~ 110cm from sensor.
# Thus if distance returned is >110cm, car isn't present. 
  
def isCarPresent():
	distance = measure_average()
	if distance < 110:
		return True
	else: 
		return False

# -----------------------
# Main Script
# -----------------------

# Use BCM GPIO references
# instead of physical pin numbers
GPIO.setmode(GPIO.BCM)
# this is so I can retain the settings between run, and avoid errors
GPIO.setwarnings(False) 

# Define GPIO to use on Pi
GPIO_TRIGGER = 24
GPIO_ECHO    = 25

GPIO_RED	= 22
GPIO_GREEN = 23

# Found these figures 'more' correct, based upon http://www.engineeringtoolbox.com/air-speed-sound-d_603.html
# Speed of sound in cm/s at temperature
temperature = 25
speedSound = 34308 + (0.6*temperature)

#print("Ultrasonic Measurement")
#print("Speed of sound is",speedSound/100,"m/s at ",temperature,"deg")

# Set pins as output and input
GPIO.setup(GPIO_TRIGGER,GPIO.OUT)  # Trigger
GPIO.setup(GPIO_ECHO,GPIO.IN)      # Echo

# Set LEDs as output
GPIO.setup(GPIO_RED,GPIO.OUT)
GPIO.setup(GPIO_GREEN,GPIO.OUT)

## Turn them both off.
#GPIO.output(GPIO_RED,GPIO.LOW)
#GPIO.output(GPIO_GREEN,GPIO.LOW)

# Set trigger to False (Low)
GPIO.output(GPIO_TRIGGER, False)

# Allow module to settle
time.sleep(0.5)

# Wrap main content in a try block so we can
# catch the user pressing CTRL-C and run the
# GPIO cleanup function. This will also prevent
# the user seeing lots of unnecessary error
# messages.


if isCarPresent():
	print("Yep.")
	GPIO.output(GPIO_RED,GPIO.HIGH)
	GPIO.output(GPIO_GREEN,GPIO.LOW)
else: 
	print("Nope.")
	GPIO.output(GPIO_RED,GPIO.LOW)
	GPIO.output(GPIO_GREEN,GPIO.HIGH)
	
#GPIO.cleanup()
