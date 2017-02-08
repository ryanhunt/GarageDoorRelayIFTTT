#!/usr/bin/python3
#
# This script allows me to control a Raspberry Pi, connected to my garage door.
# It controls the following items:
# * Garage Door relay (to open/close)
# * 2 x reed switches to determine door state (open/closed)
# * 1 x HC-SR04 module to determine if car is parked in garage
# * 2 x LEDs (Red, Green) inside of Ping pong balls to display parking spot availability. This is purely for fun, and to mimic a commercial shopping centre. 
# * 1 x DHT11 module to determine temperature and humidity in garage. 
#
# This script will allow someone to:
# Open the door, close the door, open the door a small amount for ventilation. 
# 
# It will also report the state of the garage (i.e. if the door is open/closed/ventilating/moving) and if the car is parked inside or not. 
# It will update the 2x LEDs to display state - red will be lit if the car is inside the garage (i.e. spot taken) and green will be lit if the garage is empty (i.e. spot available). The LEDs will also flash when the door is opening or closing from a fully closed or open state.
# It will report upon the weather conditions inside the garage, as well outside. It does this by an additional python file I've called 'garagesecret.py'. Which contains the following functions:
#
# --------------------------------
# def getOWMKey():
#    return "myOWMKey"
#
# def getLat():
#    return YYYYYYYY
#
# def getLong():
#    return YYYYYYY
#
# def getCoords():
#    return (getLat(), getLong())
# -------------------------------
#
# This enables me seperate out my location and my OWM key into a seperate file that is not checked into git.
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
import meteocalc as mc
from pathlib import Path

__author__ = "Ryan Hunt <ryan@ryanhunt.net>"
__copyright__ = "Copyright (c) 2016-2017 Ryan Hunt"


class Garage():
	def __init__(self):
		
		# Use BCM GPIO references
		# instead of physical pin numbers
		GPIO.setmode(GPIO.BCM)
		# this is so I can retain the settings between run, and avoid errors
		GPIO.setwarnings(False) 
		
		self.car = Car()
		self.door = GarageDoor()
		self.weather = GarageWeather()
		
	def status(self):
	    
	    # prints out all garage stats in JSON friendly format
		g = {}
		g['carPresent'] = self.car.status()
		g['doorState'] = self.door.status()
		(g['temperature'], g['humidity'], g['heatIndex']) = self.weather.status()
		(g['weatherLocation'], g['oTemperature'], g['oHumidity'], g['oHeatIndex'], g['rainfall']) = self.weather.outside.status()
		return g
		
	def display(self):
		#str = "Door status: ", door.status(), "Car status: " , car.status(), "Temperature: ", t, "Humidity: ", h
		str = "{0}\n{1}\n{2}".format(self.door.display(), self.car.display(), self.weather.display())
		return str

class GarageDoor(Garage):
	def __init__(self):
		#super(GarageDoor, self).__init__()
		
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
			
	def display(self):
		#print("Door is", self.status())
		str = "Door is {0}".format(self.status())
		return str
		
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
			sys.stderr.write("Something else is up?")
			return
class Car(Garage):
	def __init__(self):
		#super(Car, self).__init__()
			
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
		
	def display(self):
		if self.status() == 1:
			str = "Car is present"
		else:
			str =  "Car is not present"
		return str 


class GarageWeather(Garage):
	def __init__(self, unit="c"):
		#super(GarageWeather, self).__init__()
		
		import dht11
		import meteocalc as mc
		
		# DHT11 module, dht11 module handles pin management. 
		self.DHT11_PIN = 21
		
		# ensure we declare an instance of the dht11 interface. 
		self.dht11 = dht11
		
		# get outside weather too
		self.outside = OutsideWeather(unit)
		
		DEGC = u"\u2103"
		DEGF = u"\u2109"
		DEGK = u"\u212a"
		self.unit = unit
		
		if (unit == "c"):
		    self.DEG = DEGC
		elif (unit == "f"):
		    self.DEG = DEGF
		else:
		    self.DEG = DEGK
		
		#self.status()
		
	def status(self):
	
		instance = self.dht11.DHT11(pin=self.DHT11_PIN)
		
		self.outside.status()
		
		while True:
			result = instance.read()
			if result.is_valid():
				if (self.unit == "f"):
				    temperature = 9.0/5.0 * result.temperature + 32
				elif (self.unit == "k"):
				    temperature = result.temperature + 273
				else:
				    temperature = result.temperature
				humidity = result.humidity
				
				# based on these calculate the 'feels like' temp
				#t = mc.Temp(result.temperature, 'c')
				t = mc.Temp(temperature, self.unit)
				
				hi = mc.heat_index(temperature=t, humidity=humidity)
				
				
				if (self.unit == "f"):
				    heatIndex = round(hi.f,2)
				elif (self.unit == "k"):
				    heatIndex = round(hi.k,2)
				else:
				    heatIndex = round(hi.c,2)
				# want the value in Celsius, so hi.c
				#self.heatIndex = round(hi.c,2)
				
				return (temperature, humidity, heatIndex)
				break	
			time.sleep(0.1)	
	
	def display(self):
		#print("Temperature: %d%s, Humidity: %d%%" % (self.temperature, self.DEGC, self.humidity))
		
		(temp, humidity, heatIndex) = self.status()
		insideWeather = "Temperature inside: {0}{3} (Feels like: {1}{3}), Humidity: {2}%".format(temp, heatIndex, humidity, self.DEG)
		outsideWeather = self.outside.display()
		
		str = "{0}\n{1}".format(insideWeather, outsideWeather)
		
		return str
	
class OutsideWeather():
    def __init__(self, unit='c'):
        # pull in my garage lat/long and API keys from external file so as not to check it into Github
        import garagesecret as sekret
        import pyowm
        
        (lat,long) = sekret.getCoords()
        owmKey = sekret.getOWMKey()
        owm = pyowm.OWM(owmKey)
        
        DEGC = u"\u2103"
        DEGF = u"\u2109"
        DEGK = u"\u212a"
        self.unit = unit
        
        if (unit == "c"):
            self.DEG = DEGC
        elif (unit == "f"):
            self.DEG = DEGF
        else:
            self.DEG = DEGK
        
        try:
                self.obs = owm.weather_at_coords(lat, long)
        except:
                print("I reckon you've got the wrong API key, or you haven't waited 10 minutes for the API Key to be registered.")
                sys.exit()
        
        #self.status()
        
    
    def status(self):
        w = self.obs.get_weather()
        l = self.obs.get_location()
        
        name = l.get_name()
        humidity = w.get_humidity()
        
        #get rainfall, in mm. If no value returned, assume zero (0).
        r = w.get_rain()
        
        if ('3h' in r):
            rainfall = r['3h']
        else:
            rainfall = 0
        
        if (self.unit == "f"):
            temp = w.get_temperature(unit='fahrenheit')['temp']
        elif (self.unit == "k"):
            temp = w.get_temperature(unit='kelvin')['temp']
        else:
            temp = w.get_temperature(unit='celsius')['temp']
             
        t = mc.Temp(temp, self.unit)	    
        hi = mc.heat_index(temperature=t, humidity=humidity)
         
        if (self.unit == "f"):
            heatIndex = round(hi.f,2)
        elif (self.unit == "k"):
            heatIndex = round(hi.k,2)
        else:
            heatIndex = round(hi.c,2)
            
        return (name, temp, humidity, heatIndex, rainfall)
        
    def display(self):
        (name, temp, humidity, heatIndex, rainfall) = self.status()
        str = "Temperature at {0}: {1}{5} (Feels like: {2}{5}), Humidity: {3}%, Rainfall last 3 hours: {4}mm".format(name, temp, heatIndex, humidity, rainfall, self.DEG)
        return str
        

class GarageLights(Garage):
	def __init__(self):
		#super(GarageLights, self).__init__()
		
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