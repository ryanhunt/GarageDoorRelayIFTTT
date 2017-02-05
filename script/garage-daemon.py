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
import logging
import RPi.GPIO as GPIO
from pathlib import Path
from daemon import runner

__author__ = "Ryan Hunt <ryan@ryanhunt.net>"
__copyright__ = "Copyright (c) 2016-2017 Ryan Hunt"


class Garage():
	def __init__(self):
		import RPi.GPIO as GPIO
		
		# Use BCM GPIO references
		# instead of physical pin numbers
		GPIO.setmode(GPIO.BCM)
		# this is so I can retain the settings between run, and avoid errors
		GPIO.setwarnings(False) 
		
	def status(self, door, car):
		g = {}
		g['carPresent'] = car.status()
		g['doorState'] = door.status()
		return g
		
		
class GarageDoor(Garage):
	def __init__(self):
		super(GarageDoor, self).__init__()
		
		# Reed switches on door
		self.REED_BOTTOM = 17
		self.REED_TOP = 18
		
		# Relay
		self.GPIO_RELAY = 4
		
		# Set relay as output
		GPIO.setup(self.GPIO_RELAY,GPIO.OUT)
		
		self.TEMPFILE = Path("/tmp/GarageDoor.air")
		self.VENTILATIONPERC = 10
		
	# Check door state
	def status(self):
	
		GPIO.setup(self.REED_BOTTOM,GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(self.REED_TOP,GPIO.IN,pull_up_down=GPIO.PUD_UP)
		
		bottom = GPIO.input(self.REED_BOTTOM)
		top = GPIO.input(self.REED_TOP)
		
		if (bottom == 1 and top == 0):
			return "closed"
		elif (bottom == 0 and top == 1):
			return "open"
		elif (bottom == 0 and top == 0):
			if self.TEMPFILE.is_file():
				return "ventilate"
			else:
				return "opening"
		else:
			return "error"	
			
	def trigger(self):
		GPIO.output(self.GPIO_RELAY,GPIO.HIGH)
		# Allow wires to short for long enough.
		time.sleep(0.5)
		GPIO.output(self.GPIO_RELAY,GPIO.LOW)
		
	def forceClose(self):
		self._operate(0,100,1)
		
	def forceOpen(self):
		self._operate(1,100,1)
			
	def close(self):
		self._operate(0, 100,0)
		
	def open(self):
		self._operate(1, 100,0)
		
	def ventilate(self):
		self._operate(1, self.VENTILATIONPERC,0)
	
	# this is a dump door trigger, with some basic logic to set flashing lights based on previous door state.
	def ifttt(self):
		state = self.status()
		
		if (state == "opening"):
			return
			
		self.trigger()
		
		if (state == "ventilate"):
			return
		
		timeOpen = 15.59
		timeClose = 19.77
		timeout_start = time.time()
		
		if (state == "closed"):
			duration = timeOpen
		elif(state == "open"):
			duration = timeClose
				
	# action = open/close where close is 0, open is 1
	# amount = % of door openness based upon a guess of time.
	# Time to open fully (from closed) = 15.59 seconds
	# time to close fully (from open) = 19.77 seconds
	
	def _operate(self, action, amount, force):
	
		timeout_start = time.time()
		timeOpen = 15.59
		timeClose = 19.77
		
		state = self.status()
		
		if (state == "opening" and force == 0):
			# if door currently opening, do nothing.
			return
		elif(state == "opening" and force == 1):
			if (action == 1 or action == 0):
				self.trigger()
			else:
				sys.stderr.write("Error, invalid action. Must be 1 (to open) or 0 (to close)")
		elif state == "open":
			if action == 1:
				#print("Door already opened, quitting.")
				return
			elif action == 0:
				#print("Closing door...")
				self.trigger()
			else:
				sys.stderr.write("Error, invalid action. Must be 1 (to open) or 0 (to close)")
		elif state == "closed":
			if action == 0:
				#print("Door already closed, quitting")
				return
			elif action == 1:
				#print("Opening door...")
				
				duration = (amount/100) * timeOpen
				self.trigger()
				
				if (amount > 0 and amount < 100):
					# create a file on the system to denote I'm opening the door to air.
					self.TEMPFILE.touch()
					# sleep for the time it takes until door is in ventilate mode. 
					time.sleep(duration)
					self.trigger()
			else:
				sys.stderr.write("Error, invalid action. Must be 1 (to open) or 0 (to close)")
		elif state == "ventilate":
			if (action == 1 or action == 0):
				#print("Opening door...")
				
				if amount != 100:
					#print("Door already in ventilation mode, quitting.")
					return
				
				# this is only needed if I wanted to flash lights whilst opening
				#duration = timeOpen - ((self.VENTILATIONPERC/100) * timeOpen)
				
				self.trigger()
				
				# remove the marker that the door is in ventilation mode.
				self.TEMPFILE.unlink()	
			else:
				sys.stderr.write("Error, invalid action. Must be 1 (to open) or 0 (to close)")
		else: 
			print("Something else is up?")
			return
	
	
	def _original_operate(self, action, amount, force):
	
		timeout_start = time.time()
		timeOpen = 15.59
		timeClose = 19.77
		
		state = self.status()
		
		if (state == "opening" and force == 0):
			# if door currently opening, do nothing.
			print("Door currently opening, quitting")
			return
		elif(state == "opening" and force == 1):
			if action == 1:
				print("Opening door...")
				self.trigger()
			elif action == 0:
				print("Closing door...")
				self.trigger()
			else:
				sys.stderr.write("Error, invalid action. Must be 1 (to open) or 0 (to close)")
		elif state == "open":
			if action == 1:
				print("Door already opened, quitting.")
				return
			elif action == 0:
				print("Closing door...")
				self.trigger()
				
				## whilst closing, flash lights for cool effect.
				#while (time.time() < timeout_start + timeClose):
				#	flashRED(0.05)
				#	flashGREEN(0.05)
				
				# this will reset the lights
				#isCarPresent()
					
			else:
				sys.stderr.write("Error, invalid action. Must be 1 (to open) or 0 (to close)")
		elif state == "closed":
			if action == 0:
				print("Door already closed, quitting")
				return
			elif action == 1:
				print("Opening door...")
				
				duration = (amount/100) * timeOpen
				
				self.trigger()
				
				if (amount > 0 and amount < 100):
					# create a file on the system to denote I'm opening the door to air.
					self.TEMPFILE.touch()
					time.sleep(duration)
					self.trigger()
			else:
				sys.stderr.write("Error, invalid action. Must be 1 (to open) or 0 (to close)")
		elif state == "ventilate":
			if action == 1:
				print("Opening door...")
				
				if amount != 100:
					print("Door already in ventilation mode, quitting.")
					return
				
				duration = timeOpen - ((self.VENTILATIONPERC/100) * timeOpen)
				
				self.trigger()
				
				# remove the marker that the door is in ventilation mode.
				self.TEMPFILE.unlink()
				
			elif action == 0:
				print("Closing door...")
				self.trigger()
				
				# since we can't determine the time to close, we'll skip flashing lights for closing after ventilation. 
				self.TEMPFILE.unlink()
					
			else:
				sys.stderr.write("Error, invalid action. Must be 1 (to open) or 0 (to close)")
		else: 
			print("Something else is up?")
			return
	
	
		

class Car(Garage):
	def __init__(self):
		super(Car, self).__init__()
			
		# HC-SR04 sensor:
		self.GPIO_TRIGGER = 24
		self.GPIO_ECHO    = 25
		
		# Found these figures 'more' correct, based upon http://www.engineeringtoolbox.com/air-speed-sound-d_603.html
		# Speed of sound in cm/s at temperature
		self.temperature = 25
		self.speedSound = 34308 + (0.6*self.temperature)
		
		#print("Ultrasonic Measurement")
		#print("Speed of sound is",speedSound/100,"m/s at ",temperature,"deg")
		
		# Set pins as output and input
		GPIO.setup(self.GPIO_TRIGGER,GPIO.OUT)  # Trigger
		GPIO.setup(self.GPIO_ECHO,GPIO.IN)      # Echo
		
		# Set trigger to False (Low)
		GPIO.output(self.GPIO_TRIGGER, False)
		
	def _measure(self):
		# This function measures a distance
		GPIO.output(self.GPIO_TRIGGER, True)
		# Wait 10us
		time.sleep(0.00001)
		GPIO.output(self.GPIO_TRIGGER, False)
		start = time.time()
		
		while GPIO.input(self.GPIO_ECHO)==0:
			start = time.time()
		
		while GPIO.input(self.GPIO_ECHO)==1:
			stop = time.time()
		
		elapsed = stop-start
		distance = (elapsed * self.speedSound)/2
		
		return distance
		
	def _measure_average(self):
		# This function takes 3 measurements and
		# returns the average.
		
		distance1=self._measure()
		time.sleep(0.1)
		distance2=self._measure()
		time.sleep(0.1)
		distance3=self._measure()
		distance = distance1 + distance2 + distance3
		distance = distance / 3
		return distance
	  
	# Check if car is present
	# Rough car height at lowest point is ~ 110cm from sensor.
	# Thus if distance returned is >110cm, car isn't present. 
	  
	def status(self):
		# Allow the HC-SR04 module to settle
		time.sleep(0.5)
		
		distance = self._measure_average()
		if distance < 110:
			presence = 1
		else: 
			presence = 0
			
		#setLights(presence)
		return presence	

class GarageLights(Garage):
	def __init__(self):
		super(GarageLights, self).__init__()
		
		# Lights:
		self.GPIO_RED	= 22
		self.GPIO_GREEN = 23
		
		# Default flash period
		self.flashPeriod = 0.05
		
		# Set LEDs as output
		GPIO.setup(self.GPIO_RED,GPIO.OUT)
		GPIO.setup(self.GPIO_GREEN,GPIO.OUT)
	
	# set LEDs as per car presence 
	def set(self, status):
		# 1 = car present, 0 = no car
		if status == 1:
			# red = on, green = off
			GPIO.output(self.GPIO_RED,GPIO.HIGH)
			GPIO.output(self.GPIO_GREEN,GPIO.LOW)
		else: 
			# red = off, green = on
			GPIO.output(self.GPIO_RED,GPIO.LOW)
			GPIO.output(self.GPIO_GREEN,GPIO.HIGH)
			
	def flashRED(self, duration):
		GPIO.output(self.GPIO_RED,GPIO.HIGH)
		time.sleep(duration)
		GPIO.output(self.GPIO_RED,GPIO.LOW)
		time.sleep(duration)
	
	def flashGREEN(self, duration):
		GPIO.output(self.GPIO_GREEN,GPIO.HIGH)
		time.sleep(duration)
		GPIO.output(self.GPIO_GREEN,GPIO.LOW)
		time.sleep(duration)
		
	def flash(self, duration):
		timeout_start = time.time()
		
		while (time.time() < timeout_start + duration):
			GPIO.output(self.GPIO_RED,GPIO.HIGH)
			GPIO.output(self.GPIO_GREEN,GPIO.LOW)
			time.sleep(self.flashPeriod)
			GPIO.output(self.GPIO_RED,GPIO.LOW)
			GPIO.output(self.GPIO_GREEN,GPIO.HIGH)
			time.sleep(self.flashPeriod)	



class MyDaemonRunner(runner.DaemonRunner):
	
	
	def __init__(self, app):
		# workaround... :(
		self.app_save = app

		self.detach_process = True

		# this is where we define the 'action' to be function 'self._garbage'
		self.action_funcs['open'] = self._open
		#self.action_funcs['close'] = self._close
		#self.action_funcs['ventilate'] = self._ventilate
		runner.DaemonRunner.__init__(self, app)
	
	def _open(self, app):
		# for some reason, I needed this to accept two arguments, but we don't need to pass any. 
		# run the function 'garbage' inside the app.
		self.app_save.open()
		
	def parse_args(self):
		import argparse
		
		parser = argparse.ArgumentParser(description='Example arguments.')
		parser.add_argument("-s", "--start", help="Start process", action='store_true')
		parser.add_argument("-o", "--open", help="Open door.", action='store_true')
		parser.add_argument("-k", "--stop", help="Stop process", action='store_true')
		parser.add_argument("-r", "--restart", help="Restart process", action='store_true')
		parser.add_argument("-l", "--log_file", dest="filename", help="write log to FILE", metavar="FILE")
		parser.add_argument("-p", "--pid_file", dest="pidname", help="write pid to FILE", metavar="FILE")
		parser.add_argument("-f", "--foreground", help="Run in the foreground", action='store_true')
		parser.add_argument("-v", "--verbose", help="Verbose", action='store_true')
		
		
		args = parser.parse_args()
		
		if args.start:
			self.action = 'start'
			#print("Starting ", parser.prog, "...")
		elif args.stop:
			self.action = 'stop'
		elif args.restart:
			self.action = 'restart'
		elif args.foreground:
			self.detach_process = False
			self.app_save.stdout_path = '/dev/tty'
			self.app_save.stderr_path = '/dev/tty'
			self.app_save.foreground = True	
		elif args.open:
			self.action = 'open'
		else:
			print (parser.print_help())
			#print ("Too few arguments")
			parser.exit()
			sys.exit()
		
		# optionals
		
		if args.filename:
			self.app_save.log_file = args.filename
			
		if args.pidname:
			self.app_save.pidfile_path = args.pidname

		if args.verbose:			
			self.verbose = True
#class GarageTemperature(Garage):

class App:
	def __init__(self):
		# python-daemon DaemonRunner requires the below.
		self.stdin_path = '/dev/null'
		self.stdout_path = '/dev/null'
		self.stderr_path = '/dev/null'
		# For debug, you can use '/dev/tty' for stdout/stderr instead.
		#self.stdout_path = '/dev/tty'
		#self.stderr_path = '/dev/tty'
		self.pidfile_path =  '/tmp/foo.pid'
		self.pidfile_timeout = 5
		# The above 5 attributes are mandatory.
		#
		# The below are this App specific. (conf file is not implemented now)
		self.log_file = '/tmp/garage.log'
		self.foreground = False
		
		self.garage = Garage()
		self.car = Car()
		self.door = GarageDoor()

	def open(self):
		logging.basicConfig(level=logging.DEBUG,
						format='%(asctime)s %(levelname)s %(message)s',
						filename=self.log_file,
						filemode='a')
		
		logging.info('door opened.')
		
		self.door.open()
	
	def run(self):
		# Here is your main logic.
		# Initializing code.
		if not self.foreground:
			logging.basicConfig(level=logging.DEBUG,
							format='%(asctime)s %(levelname)s %(message)s',
							filename=self.log_file,
							filemode='a')
		while True:
			# the main loop code.
			try:
				#str = time.asctime(time.localtime(time.time()))
				str = "Door status: ", self.door.status(), "Car status: " , self.car.status()
				
				if self.foreground:
					print ("Door status: ", self.door.status(), "Car status: " , self.car.status())
				else:
					logging.info('DEBUG: Door status: %s Car status %d', self.door.status(), self.car.status())

				time.sleep(1)
			except:
				logging.info(sys.exc_info())
				logging.info('Terminating.')
				sys.exit(1)

def checkPerms():
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
		

#GPIO.cleanup()

if __name__ == '__main__':
	app = App()
	daemon_runner = MyDaemonRunner(app)
	if not app.foreground:
		daemon_runner.do_action()
	else:
		app.run()