# -*- coding: utf-8 -*-
#
# WeatherPlugin E2
#
# Coded by Dr.Best (c) 2012-2013
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Multimedia GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Multimedia GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Multimedia GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from Components.Converter.Converter import Converter
from Components.Element import cached


class MSNWeather(Converter, object):

	CURRENT = -1
	CITY = 0
	DAY1 = 1
	DAY2 = 2
	DAY3 = 3
	DAY4 = 4
	DAY5 = 5
	TEMPERATURE_HEIGH = 6
	TEMPERATURE_LOW = 7
	TEMPERATURE_TEXT = 8
	TEMPERATURE_CURRENT = 9
	WEEKDAY = 10
	WEEKSHORTDAY = 11
	DATE = 12
	OBSERVATIONTIME = 13
	OBSERVATIONPOINT = 14
	FEELSLIKE = 15
	HUMIDITY = 16
	WINDDISPLAY = 17
	ICON = 18
	TEMPERATURE_HEIGH_LOW = 19
	CODE = 20
	PATH = 21

	def __init__(self, type):
		Converter.__init__(self, type)
		self.index = None
		self.mode = None
		self.path = None
		self.extension = None
		if type == "city":
			self.mode = self.CITY
		elif type == "observationtime":
			self.mode = self.OBSERVATIONTIME
		elif type == "observationpoint":
			self.mode = self.OBSERVATIONPOINT
		elif type == "temperature_current":
				self.mode = self.TEMPERATURE_CURRENT
		elif type == "feelslike":
				self.mode = self.FEELSLIKE
		elif type == "humidity":
				self.mode = self.HUMIDITY
		elif type == "winddisplay":
				self.mode = self.WINDDISPLAY
		else:
			if type.find("weathericon") != -1:
				self.mode = self.ICON
			elif type.find("temperature_high") != -1:
				self.mode = self.TEMPERATURE_HEIGH
			elif type.find("temperature_low") != -1:
				self.mode = self.TEMPERATURE_LOW
			elif type.find("temperature_heigh_low") != -1:
				self.mode = self.TEMPERATURE_HEIGH_LOW
			elif type.find("temperature_text") != -1:
				self.mode = self.TEMPERATURE_TEXT
			elif type.find("weekday") != -1:
				self.mode = self.WEEKDAY
			elif type.find("weekshortday") != -1:
				self.mode = self.WEEKSHORTDAY
			elif type.find("date") != -1:
				self.mode = self.DATE
			if self.mode is not None:
				dd = type.split(",")
				if len(dd) >= 2:
					self.index = self.getIndex(dd[1])
				if self.mode == self.ICON and len(dd) == 4:
					self.path = dd[2]
					self.extension = dd[3]

	def getIndex(self, key):
		if key == "current":
			return self.CURRENT
		elif key == "day1":
			return self.DAY1
		elif key == "day2":
			return self.DAY2
		elif key == "day3":
			return self.DAY3
		elif key == "day4":
			return self.DAY4
		elif key == "day5":
			return self.DAY5
		else:
			return None

	@cached
	def getText(self):
		if self.mode == self.CITY:
			return self.source.getCity()
		elif self.mode == self.OBSERVATIONPOINT:
			return self.source.getObservationPoint()
		elif self.mode == self.OBSERVATIONTIME:
			return self.source.getObservationTime()
		elif self.mode == self.TEMPERATURE_CURRENT:
			return self.source.getTemperature_Current()
		elif self.mode == self.FEELSLIKE:
			return self.source.getFeelslike()
		elif self.mode == self.HUMIDITY:
			return self.source.getHumidity()
		elif self.mode == self.WINDDISPLAY:
			return self.source.getWinddisplay()
		elif self.mode == self.TEMPERATURE_HEIGH and self.index is not None:
			return self.source.getTemperature_Heigh(self.index)
		elif self.mode == self.TEMPERATURE_LOW and self.index is not None:
			return self.source.getTemperature_Low(self.index)
		elif self.mode == self.TEMPERATURE_HEIGH_LOW and self.index is not None:
			return self.source.getTemperature_Heigh_Low(self.index)
		elif self.mode == self.TEMPERATURE_TEXT and self.index is not None:
			return self.source.getTemperature_Text(self.index)
		elif self.mode == self.WEEKDAY and self.index is not None:
			return self.source.getWeekday(self.index, False)
		elif self.mode == self.WEEKSHORTDAY and self.index is not None:
			return self.source.getWeekday(self.index, True)
		elif self.mode == self.DATE and self.index is not None:
			return self.source.getDate(self.index)
		else:
			return ""

	text = property(getText)

	@cached
	def getIconFilename(self):
		if self.mode == self.ICON and self.index in (self.CURRENT, self.DAY1, self.DAY2, self.DAY3, self.DAY4, self.DAY5):
			if self.path is not None and self.extension is not None:
				return self.path + self.source.getCode(self.index) + "." + self.extension
			else:
				return self.source.getWeatherIconFilename(self.index)
		else:
			return ""

	iconfilename = property(getIconFilename)
