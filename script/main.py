#!/usr/bin/python3

from __future__ import print_function
import json
import time
import argparse
import sys
import os
import RPi.GPIO as GPIO
import meteocalc as mc
import garage
from pathlib import Path

__author__ = "Ryan Hunt <ryan@ryanhunt.net>"
__copyright__ = "Copyright (c) 2016-2017 Ryan Hunt"

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

	# add optional commands, if not specified, run in human friendly format.
	parser = argparse.ArgumentParser(description='Operate a Garage Door.')
	parser.add_argument("-r", "--cron", help="check door status and log, expected to be run by cron", action='store_true')
	parser.add_argument("-j", "--json", help="output door status in JSON", action='store_true')
	parser.add_argument("-o", "--open", help="Open Door", action='store_true')
	parser.add_argument("-c", "--close", help="Close Door", action='store_true')
	parser.add_argument("-f", "--force", help="Force/Override Open/Close", action='store_true')
	parser.add_argument("-v", "--ventilate", help="Open the door a crack, to let some air in.", action='store_true')
	parser.add_argument("-i", "--ifttt", help="Dumb trigger for IFTTT, which simply triggers the door.", action='store_true')
	args = parser.parse_args()
	
	checkPerms()
	
	garage = Garage()
	
	if args.force:
		if args.open:
			garage.door.forceOpen()
		elif args.close:
			garage.door.forceClose()
		else:
			sys.stderr.write("Force requires an action of close or open.\n")
		sys.exit()
	
	if args.ifttt:
		garage.door.ifttt()
		sys.exit()
		
	if args.open:
		garage.door.open()
		sys.exit()
	
	if args.close:
		garage.door.close()
		sys.exit()
		
	if args.ventilate:
		garage.door.ventilate()
		sys.exit()
	
	if args.json:
		status = garage.status()
		print(json.dumps(status))
	elif args.cron:
		#print("doing something for cron")
		# this will update the LED lights on a regular basis, unsure what happens in a race condition when cron runs and user triggers the script.
		garage.car.status()
		
		#TODO: log status elsewhere - and setup triggers such as SMS alerts for periods when door is open too long.
	else:
		print(garage.display())
