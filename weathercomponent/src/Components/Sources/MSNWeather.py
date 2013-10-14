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

import time
from Source import Source
from Components.WeatherMSN import weathermsn

class MSNWeather(Source):

	def __init__(self):
		Source.__init__(self)
		weathermsn.callbacksAllIconsDownloaded.append(self.callbackAllIconsDownloaded)
		weathermsn.getData()

	def callbackAllIconsDownloaded(self):
		self.changed((self.CHANGED_ALL,))
	
	def getCity(self):
		return weathermsn.weatherData.city
		
	def getObservationPoint(self):
		skey = "-1"
		if weathermsn.weatherData.weatherItems.has_key(skey):
			return weathermsn.weatherData.weatherItems[skey].observationpoint
		else:
			return _("n/a")
		
	def getObservationTime(self):
		skey = "-1"
		if weathermsn.weatherData.weatherItems.has_key(skey):
			item = weathermsn.weatherData.weatherItems[skey]
			if item.observationtime != "":
				c =  time.strptime(item.observationtime, "%H:%M:%S")
				return  time.strftime("%H:%M",c)
			else:
				return _("n/a")
		else:
			return _("n/a")
		
	def getTemperature_Heigh(self, key):
		skey = str(key)
		if skey == "-1":
			skey = "1"
		if weathermsn.weatherData.weatherItems.has_key(skey):
			item = weathermsn.weatherData.weatherItems[skey]
			highTemp = item.high
			return "%s°%s" % (highTemp, weathermsn.weatherData.degreetype)
		else:
			return _("n/a")
			
	
	def getTemperature_Low(self, key):
		skey = str(key)
		if skey == "-1":
			skey = "1"
		if weathermsn.weatherData.weatherItems.has_key(skey):
			item = weathermsn.weatherData.weatherItems[skey]
			lowTemp = item.low
			return "%s°%s" % (lowTemp, weathermsn.weatherData.degreetype)
		else:
			return _("n/a")
			
	def getTemperature_Heigh_Low(self, key):
		skey = str(key)
		if skey == "-1":
			skey = "1"
		if weathermsn.weatherData.weatherItems.has_key(skey):
			item = weathermsn.weatherData.weatherItems[skey]
			highTemp = item.high
			high =  "%s°%s" % (highTemp, weathermsn.weatherData.degreetype)
			low = self.getTemperature_Low(key)
			return "%s - %s" % (high, low)
		else:
			return _("n/a")		
	
	
	
	def getTemperature_Text(self, key):
		skey = str(key)
		if weathermsn.weatherData.weatherItems.has_key(skey):
			item = weathermsn.weatherData.weatherItems[skey]
			if skey == "-1":
				return item.skytext
			else:
				return  item.skytextday
		else:
			return _("n/a")
			
	def getTemperature_Current(self):
		skey = "-1"
		if weathermsn.weatherData.weatherItems.has_key(skey):
			return "%s°%s" % (weathermsn.weatherData.weatherItems[skey].temperature, weathermsn.weatherData.degreetype)
		else:
			return _("n/a")
			
	def getFeelslike(self):
		skey = "-1"
		if weathermsn.weatherData.weatherItems.has_key(skey):
			return weathermsn.weatherData.weatherItems[skey].feelslike
		else:
			return _("n/a")
	
	def getHumidity(self):
		skey = "-1"
		if weathermsn.weatherData.weatherItems.has_key(skey):
			return weathermsn.weatherData.weatherItems[skey].humidity
		else:
			return _("n/a")
			
	def getWinddisplay(self):
		skey = "-1"
		if weathermsn.weatherData.weatherItems.has_key(skey):
			return weathermsn.weatherData.weatherItems[skey].winddisplay
		else:
			return _("n/a")
	
	def getWeekday(self, key, short):
		skey = str(key)
		if skey == "-1":
			skey = "1"
		if weathermsn.weatherData.weatherItems.has_key(skey):
			item = weathermsn.weatherData.weatherItems[skey]
			if short:
				return item.shortday
			else:
				return item.day
		else:
			return _("n/a")
			
	def getDate(self, key):
		skey = str(key)
		if skey == "-1":
			skey = "1"
		if weathermsn.weatherData.weatherItems.has_key(skey):
			item = weathermsn.weatherData.weatherItems[skey]
			c = time.strptime(item.date,"%Y-%m-%d")
			return time.strftime("%d. %b",c)
		else:
			return _("n/a")
			
	def getWeatherIconFilename(self, key):
		if weathermsn.weatherData.weatherItems.has_key(str(key)):
			return weathermsn.weatherData.weatherItems[str(key)].iconFilename
		else:
			return ""
			
	def getCode(self, key):
		if weathermsn.weatherData.weatherItems.has_key(str(key)):
			return weathermsn.weatherData.weatherItems[str(key)].code
		else:
			return ""

	def destroy(self):
		weathermsn.callbacksAllIconsDownloaded.remove(self.callbackAllIconsDownloaded)
		Source.destroy(self)
