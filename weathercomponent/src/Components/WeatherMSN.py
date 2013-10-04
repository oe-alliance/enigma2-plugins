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

from enigma import eEnv, eTimer
from Plugins.Extensions.WeatherPlugin.MSNWeather import MSNWeather

class WeatherMSN:
	TIMER_INTERVAL = 1800
	def __init__(self):
		self.weatherData = MSNWeather()
		self.callbacks = [ ]
		self.callbacksAllIconsDownloaded = []
		self.timer = eTimer()
		self.timer.callback.append(self.getData)
	
	def getData(self):
		self.timer.stop()
		self.weatherData.getDefaultWeatherData(self.callback, self.callbackAllIconsDownloaded)
		self.timer.startLongTimer(self.TIMER_INTERVAL)
		
	def updateWeather(self, weather, result, errortext):
		if result == MSNWeather.OK:
			self.timer.stop()
			self.weatherData = weather
			self.weatherData.callback = None
			self.weatherData.callbackShowIcon = None
			self.weatherData.callbackAllIconsDownloaded = None
			self.callback(result, errortext)
			self.callbackAllIconsDownloaded()
			self.timer.startLongTimer(self.TIMER_INTERVAL)

	def callbackAllIconsDownloaded(self):
		for x in self.callbacksAllIconsDownloaded:
			x()

	def callback(self, result, errortext):
		for x in self.callbacks:
			x(result, errortext)
	
weathermsn = WeatherMSN()
