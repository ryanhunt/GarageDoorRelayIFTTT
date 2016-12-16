#!/usr/bin/python3


# Connected to pin 4 (Wiring Pi 7) 
# Delay time required to short = 0.5 seconds
# Time to open fully (from closed) = 15.59 seconds
# time to close fully (from open) = 19.77 seconds


import RPi.GPIO as GPIO
from pathlib import Path
import time
import sys


# If door is opening, or code barfed this file will exist - and then do nothing. 
tempFile = Path("/tmp/GarageDoor.opening")

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(4,GPIO.OUT)

if tempFile.is_file():
	sys.stderr.write("Door is already opening, or script barfed. Quitting...\n")
	sys.exit()
else:
	print("Opening or Closing door...")
	tempFile.touch()
	GPIO.output(4,GPIO.HIGH)
	# Allow wires to short for long enough.
	time.sleep(0.5)
	GPIO.output(4,GPIO.LOW)	
	# Ensure the garage door has enough time to open and/or close
	time.sleep(20)
	tempFile.unlink()

print("Thanks for opening the door with IFTTT")

# This resets all pins
#GPIO.cleanup()
