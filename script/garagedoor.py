#!/usr/bin/python3
#
# This script allows me to control a Raspberry Pi, connected to my garage door.
# It controls the following items:
# * Garage Door relay (to open/close)
# * 2 x reed switches to determine door state (open/closed)
# * 1x HC-SR04 module to determine if car is parked in garage
# * 2 x LEDs (Red, Green) inside of Ping pong balls to display parking spot availability. This is purely for fun, and to mimic a commercial shopping centre. 
#
# This script will allow someone to:
# Open the door, close the door, open the door a small amount for ventilation. 
# 
# It will also report the state of the garage (i.e. if the door is open/closed/ventilating/moving) and if the car is parked inside or not. 
# It will update the 2x LEDs to display state - red will be lit if the car is inside the garage (i.e. spot taken) and green will be lit if the garage is empty (i.e. spot available). The LEDs will also flash when the door is opening or closing from a fully closed or open state.
# 
# In order for this script to run properly, you'll need to grant root access to it to the web user (who will call this ultimately).
#
# Credit to Matt Hawkins for the sensing components
# http://www.raspberrypi-spy.co.uk/tag/ultrasonic/
# -----------------------

from __future__ import print_function
import json
import time
import argparse
import sys
import os
import RPi.GPIO as GPIO
import dht11
from pathlib import Path

__author__ = "Ryan Hunt <ryan@ryanhunt.net>"
__copyright__ = "Copyright (c) 2016-2017 Ryan Hunt"

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
	# Allow the HC-SR04 module to settle
	time.sleep(0.5)
	
	distance = measure_average()
	if distance < 110:
		presence = 1
	else: 
		presence = 0
		
	setLights(presence)
	return presence
		
# Check door state
def getDoorState():

	GPIO.setup(REED_BOTTOM,GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(REED_TOP,GPIO.IN,pull_up_down=GPIO.PUD_UP)
	
	bottom = GPIO.input(REED_BOTTOM)
	top = GPIO.input(REED_TOP)
	
	if (bottom == 1 and top == 0):
		return "closed"
	elif (bottom == 0 and top == 1):
		return "open"
	elif (bottom == 0 and top == 0):
		if TEMPFILE.is_file():
			return "ventilate"
		else:
			return "opening"
	else:
		return "error"	
		
# set LEDs as per car presence 
def setLights(status):
	# 1 = car present, 0 = no car
	if status == 1:
		# red = on, green = off
		GPIO.output(GPIO_RED,GPIO.HIGH)
		GPIO.output(GPIO_GREEN,GPIO.LOW)
	else: 
		# red = off, green = on
		GPIO.output(GPIO_RED,GPIO.LOW)
		GPIO.output(GPIO_GREEN,GPIO.HIGH)
		
def flashRED(duration):
	GPIO.output(GPIO_RED,GPIO.HIGH)
	time.sleep(duration)
	GPIO.output(GPIO_RED,GPIO.LOW)
	time.sleep(duration)

def flashGREEN(duration):
	GPIO.output(GPIO_GREEN,GPIO.HIGH)
	time.sleep(duration)
	GPIO.output(GPIO_GREEN,GPIO.LOW)
	time.sleep(duration)


def forceCloseDoor():
	operateDoor(0,100,1)
	
def forceOpenDoor():
	operateDoor(1,100,1)
		
def closeDoor():
	operateDoor(0, 100,0)
	
def openDoor():
	operateDoor(1, 100,0)
	
def openDoorGap():
	operateDoor(1, VENTILATIONPERC,0)

def weather():
	(temperature, humidity) = getWeather()
	
	DEGC = u"\u2103"
    print("Temperature: %d%s" % (temperature, DEGC))
    print("Humidity: %d%%" % humidity)
		
def getWeather():
	instance = dht11.DHT11(pin=DHT11_PIN)
	
	while True:
		result = instance.read()
		if result.is_valid():
			return (result.temperature, result.humidity)
			break	
		time.sleep(0.1)

# this is a dump door trigger, with some basic logic to set flashing lights based on previous door state.
def ifttt():
	state = getDoorState()
	
	if (state == "opening"):
		return
		
	triggerDoor()
	
	if (state == "ventilate"):
		return
	
	timeOpen = 15.59
	timeClose = 19.77
	timeout_start = time.time()
	
	if (state == "closed"):
		duration = timeOpen
	elif(state == "open"):
		duration = timeClose
	
	while (time.time() < timeout_start + duration):
		flashRED(0.05)
		flashGREEN(0.05)
	
	# this will reset the lights
	isCarPresent()
	

# action = open/close where close is 0, open is 1
# amount = % of door openness based upon a guess of time.
# Time to open fully (from closed) = 15.59 seconds
# time to close fully (from open) = 19.77 seconds

def operateDoor(action, amount, force):

	timeout_start = time.time()
	timeOpen = 15.59
	timeClose = 19.77
	
	state = getDoorState()
	
	if (state == "opening" and force == 0):
		# if door currently opening, do nothing.
		print("Door currently opening, quitting")
		return
	elif(state == "opening" and force == 1):
		if action == 1:
			print("Opening door...")
			triggerDoor()
		elif action == 0:
			print("Closing door...")
			triggerDoor()
		else:
			sys.stderr.write("Error, invalid action. Must be 1 (to open) or 0 (to close)")
	elif state == "open":
		if action == 1:
			print("Door already opened, quitting.")
			return
		elif action == 0:
			print("Closing door...")
			triggerDoor()
			
			# whilst closing, flash lights for cool effect.
			while (time.time() < timeout_start + timeClose):
				flashRED(0.05)
				flashGREEN(0.05)
			
			# this will reset the lights
			isCarPresent()
				
		else:
			sys.stderr.write("Error, invalid action. Must be 1 (to open) or 0 (to close)")
	elif state == "closed":
		if action == 0:
			print("Door already closed, quitting")
			return
		elif action == 1:
			print("Opening door...")
			
			duration = (amount/100) * timeOpen
			
			triggerDoor()
			
			# whilst opening, flash lights for cool effect.
			while (time.time() < timeout_start + duration):
				flashRED(0.05)
				flashGREEN(0.05)
			
			# this will reset the lights
			isCarPresent()
			
			if (amount > 0 and amount < 100):
				# create a file on the system to denote I'm opening the door to air.
				TEMPFILE.touch()
				triggerDoor()
		else:
			sys.stderr.write("Error, invalid action. Must be 1 (to open) or 0 (to close)")
	elif state == "ventilate":
		if action == 1:
			if amount != 100:
				print("Door already in ventilation mode, quitting.")
				return
			
			print("Opening door...")
			
			duration = timeOpen - ((VENTILATIONPERC/100) * timeOpen)
			
			triggerDoor()
			
			# whilst opening, flash lights for cool effect.
			while (time.time() < timeout_start + duration):
				flashRED(0.05)
				flashGREEN(0.05)
			
			# this will reset the lights
			isCarPresent()
			
			# remove the marker that the door is in ventilation mode.
			TEMPFILE.unlink()
			
		elif action == 0:
			print("Closing door...")
			triggerDoor()
			
			# since we can't determine the time to close, we'll skip flashing lights for closing after ventilation. 
			TEMPFILE.unlink()
				
		else:
			sys.stderr.write("Error, invalid action. Must be 1 (to open) or 0 (to close)")
	else: 
		print("Something else is up?")
		return


def triggerDoor():
	GPIO.output(GPIO_RELAY,GPIO.HIGH)
	# Allow wires to short for long enough.
	time.sleep(0.5)
	GPIO.output(GPIO_RELAY,GPIO.LOW)

# -----------------------
# Main Script
# -----------------------

# add optional commands, if not specified, run in human friendly format.
parser = argparse.ArgumentParser(description='Operate a Garage Door.')
parser.add_argument("-r", "--cron", help="check door status and log, expected to be run by cron", action='store_true')
parser.add_argument("-j", "--json", help="output door status in JSON", action='store_true')
parser.add_argument("-o", "--open", help="Open Door", action='store_true')
parser.add_argument("-c", "--close", help="Close Door", action='store_true')
parser.add_argument("-f", "--force", help="Force/Override Open/Close", action='store_true')
parser.add_argument("-v", "--ventilate", help="Open the door a crack, to let some air in.", action='store_true')
parser.add_argument("-i", "--ifttt", help="Dumb trigger for IFTTT, which simply triggers the door.", action='store_true')
parser.add_argument("-w", "--weather", help="Tell me the conditions of the Garage.", action='store_true')
args = parser.parse_args()

# check for GPIO permissions. 
# we assume is user is member of 'gpio' (gid = 997) then we're all good.
userid = os.getuid()

if userid == 0:
	sys.stderr.write("Not recommended to run as root. Create a user that is a member of the 'gpio' group, and try again.\n")
	sys.exit()
	
groups = os.getgroups()

if 997 not in groups:
	sys.stderr.write("Not a member of 'gpio', unable to read/write required pins. Add the current user to the 'gpio' group and try again.\n")
	sys.exit()
	

# Use BCM GPIO references
# instead of physical pin numbers
GPIO.setmode(GPIO.BCM)
# this is so I can retain the settings between run, and avoid errors
GPIO.setwarnings(False) 

# Define GPIO to use on Pi

# HC-SR04 sensor:
GPIO_TRIGGER = 24
GPIO_ECHO    = 25

# Lights:
GPIO_RED	= 22
GPIO_GREEN = 23

# Reed switches on door
REED_BOTTOM = 17
REED_TOP = 18

# Relay
GPIO_RELAY = 4

# DHT11 temp/humidity sensor
DHT11_PIN = 21

TEMPFILE = Path("/tmp/GarageDoor.air")
VENTILATIONPERC = 10

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

# Set relay as output
GPIO.setup(GPIO_RELAY,GPIO.OUT)

# Set trigger to False (Low)
GPIO.output(GPIO_TRIGGER, False)


if args.force:
	if args.open:
		forceOpenDoor()
	elif args.close:
		forceCloseDoor()
	else:
		sys.stderr.write("Force requires an action of close or open.\n")
	sys.exit()

if args.ifttt:
	ifttt()
	sys.exit()
	
if args.weather:
	weather()
	sys.exit()
	
if args.open:
	openDoor()
	sys.exit()

if args.close:
	closeDoor()
	sys.exit()
	
if args.ventilate:
	openDoorGap()
	sys.exit()


if args.json:
	garageStatus = {}
	garageStatus['carPresent'] = isCarPresent()
	garageStatus['doorState'] = getDoorState()
	(garageStatus['temperature'], garageStatus['humidity']) = getWeather()
	print(json.dumps(garageStatus))
elif args.cron:
	#print("doing something for cron")
	# this will update the LED lights on a regular basis, unsure what happens in a race condition when cron runs and user triggers the script.
	isCarPresent()
	
	#TODO: log status elsewhere - and setup triggers such as SMS alerts for periods when door is open too long.
else:
	print("Door is", getDoorState())
	if isCarPresent() == 1:
		print("Car is present.")
	else:
		print("Car is not present.")
	weather()
	
#GPIO.cleanup()
