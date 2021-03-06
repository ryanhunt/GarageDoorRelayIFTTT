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
import datetime
import argparse
import pyrebase
import secret
import sys
import os
import logging
from garage import *
import RPi.GPIO as GPIO
from pathlib import Path
from daemon import runner

__author__ = "Ryan Hunt <ryan@ryanhunt.net>"
__copyright__ = "Copyright (c) 2016-2017 Ryan Hunt"

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
		
		# creates a new Garage instance, with a  warning alert interval of 30 seconds (default is 300 secs/5 mins)
		self.garage = Garage(30)

	def open(self):
		logging.basicConfig(level=logging.DEBUG,
						format='%(asctime)s %(levelname)s %(message)s',
						filename=self.log_file,
						filemode='a')
		
		logging.info('door opened.')
		
		self.garage.door.open()
			
	def run(self):
		# Here is your main logic.
		# Initialising code.
		if not self.foreground:
			logging.basicConfig(level=logging.DEBUG,
							format='%(asctime)s %(levelname)s %(message)s',
							filename=self.log_file,
							filemode='a')
		
		lastStatus = self.garage.door.status()
		lastTime = datetime.datetime.now()
		numWarnings = 0
		
		if self.foreground:
			print ("Daemon started at {0}".format( time.ctime() ) )
			
			safeOpenTime = self.garage.door.getSafeOpenTime()
			m, s = divmod(safeOpenTime, 60)
			h, m = divmod(m, 60)
			
			print ("We'll warn you if door is open for more than {0} minutes, {1} seconds".format(int(m), s))
			print (self.garage.door.display())
		else:
			logging.info("Daemon started at {0}".format( time.ctime() ) )
			logging.info('DEBUG: %s', self.garage.door.status())
		
		while True:
			# the main loop code.
			try:
				#str = time.asctime(time.localtime(time.time()))

				nowTime = datetime.datetime.now()
				
				# this checks to see if there is a change in state, and if so - log it. 
				if ( lastStatus != self.garage.door.status() ):
					if self.foreground:
						#print ("Door status: ", self.door.status(), "Car status: " , self.car.status())
						
						print ("{0}: {1} -> {2} ({3})".format(lastStatus, lastTime, nowTime, (nowTime - lastTime)))
						#print ("{0} -> {1} ({2})".format(lastStatus, self.garage.door.status(), (datetime.datetime.now() - lastTime)))
					else:
						#logging.info('DEBUG: Door status: %s Car status %d', self.door.status(), self.car.status())
						#logging.info('DEBUG: %s', self.garage.door.status())
						logging.info("DEBUG: {0}: {1} -> {2} ({3})".format(lastStatus, lastTime, nowTime, (nowTime - lastTime)))
					
					lastTime = nowTime
				
				#else:
					# this means that there is no change, so print/log nothing. We only want to capture changes.

				
				# this part here then does warnings, but only once every 300 second (5 minutes) 
				lastStatus = self.garage.door.status()
				#count = nowTime - ( self.garage.warningTime * numWarnings) - lastTime
				count = nowTime - ( datetime.timedelta(seconds=(self.garage.warningTime * numWarnings)) ) - lastTime
				countFloat = float(count.total_seconds())
				
				if (self.garage.door.isTimeToWorry(countFloat) == True):
					if self.foreground:
						print ("It's time to worry now!")
					else:
						logging.info("DEBUG: It's time to worry now!")
					numWarnings  = numWarnings + 1
					
				time.sleep(0.5)
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