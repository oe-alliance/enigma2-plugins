# -*- coding: utf-8 -*-
#
# WeatherPlugin E2
#
# Coded by Dr.Best (c) 2012
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

# for localized messages
from . import _

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from enigma import ePicLoad, eRect, eSize, gPixmapPtr
from Components.AVSwitch import AVSwitch
from Components.config import ConfigSubsection, ConfigSubList, ConfigInteger, config
from setup import initConfig, MSNWeatherPluginEntriesListConfigScreen
from MSNWeather import MSNWeather
import time

try:
	from Components.WeatherMSN import weathermsn
	WeatherMSNComp = weathermsn
except:
	WeatherMSNComp = None

config.plugins.WeatherPlugin = ConfigSubsection()
config.plugins.WeatherPlugin.entrycount =  ConfigInteger(0)
config.plugins.WeatherPlugin.Entry = ConfigSubList()
initConfig()


def main(session,**kwargs):
	session.open(MSNWeatherPlugin)

def Plugins(**kwargs):
	list = [PluginDescriptor(name=_("Weather Plugin"), description=_("Show Weather Forecast"), where = [PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU], icon = "weather.png", fnc=main)]
	return list

class MSNWeatherPlugin(Screen):

	skin = """
		<screen name="MSNWeatherPlugin" position="center,center" size="664,340" title="Weather Plugin">
			<widget render="Label" source="caption" position="10,20" zPosition="1" size="600,28" font="Regular;24" transparent="1"/>
			<widget render="Label" source="observationtime" position="374,45" zPosition="1" size="280,20" font="Regular;14" transparent="1" halign="right" />
			<widget render="Label" source="observationpoint" position="204,65" zPosition="1" size="450,40" font="Regular;14" transparent="1" halign="right" />
			<widget name="currenticon" position="10,95" zPosition="1" size="55,45" alphatest="blend"/>
			<widget render="Label" source="currentTemp" position="90,95" zPosition="1" size="100,23" font="Regular;22" transparent="1"/>
			<widget render="Label" source="feelsliketemp" position="90,120" zPosition="1" size="155,40" font="Regular;14" transparent="1"/>
			<widget render="Label" source="condition" position="270,95" zPosition="1" size="300,20" font="Regular;18" transparent="1"/>
			<widget render="Label" source="wind_condition" position="270,115" zPosition="1" size="300,20" font="Regular;18" transparent="1"/>
			<widget render="Label" source="humidity" position="270,135" zPosition="1" size="300,20" font="Regular;18" valign="bottom" transparent="1"/>
			<widget render="Label" source="weekday1" position="35,170" zPosition="1" size="105,40" halign="center" valign="center" font="Regular;18" transparent="1"/>
			<widget name="weekday1_icon" position="60,215" zPosition="1" size="55,45" alphatest="blend"/>
			<widget render="Label" source="weekday1_temp" position="35,270" zPosition="1" size="105,60" halign="center" valign="bottom" font="Regular;16" transparent="1"/>
			<widget render="Label" source="weekday2" position="155,170" zPosition="1" size="105,40" halign="center" valign="center" font="Regular;18" transparent="1"/>
			<widget name="weekday2_icon" position="180,215" zPosition="1" size="55,45" alphatest="blend"/>
			<widget render="Label" source="weekday2_temp" position="155,270" zPosition="1" size="105,60" halign="center" valign="bottom" font="Regular;16" transparent="1"/>
			<widget render="Label" source="weekday3" position="275,170" zPosition="1" size="105,40" halign="center" valign="center" font="Regular;18" transparent="1"/>
			<widget name="weekday3_icon" position="300,215" zPosition="1" size="55,45" alphatest="blend"/>
			<widget render="Label" source="weekday3_temp" position="275,270" zPosition="1" size="105,60" halign="center" valign="bottom" font="Regular;16" transparent="1"/>
			<widget render="Label" source="weekday4" position="395,170" zPosition="1" size="105,40" halign="center" valign="center" font="Regular;18" transparent="1"/>
			<widget name="weekday4_icon" position="420,215" zPosition="1" size="55,45" alphatest="blend"/>
			<widget render="Label" source="weekday4_temp" position="395,270" zPosition="1" size="105,60" halign="center" valign="bottom" font="Regular;16" transparent="1"/>
			<widget render="Label" source="weekday5" position="515,170" zPosition="1" size="105,40" halign="center" valign="center" font="Regular;18" transparent="1"/>
			<widget name="weekday5_icon" position="540,215" zPosition="1" size="55,45" alphatest="blend"/>
			<widget render="Label" source="weekday5_temp" position="515,270" zPosition="1" size="105,60" halign="center" valign="bottom" font="Regular;16" transparent="1"/>
			<widget render="Label" source="statustext" position="0,0" zPosition="1" size="664,340" font="Regular;20" halign="center" valign="center" transparent="1"/>
		</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)
		self.title = _("Weather Plugin")
		self["actions"] = ActionMap(["SetupActions", "DirectionActions"],
		{
			"cancel": self.close,
			"menu": self.config,
			"right": self.nextItem,
			"left": self.previousItem,
			"info": self.showWebsite
		}, -1)

		self["statustext"] = StaticText()
		self["currenticon"] = WeatherIcon()
		self["caption"] = StaticText()
		self["currentTemp"] = StaticText()
		self["condition"] = StaticText()
		self["wind_condition"] = StaticText()
		self["humidity"] = StaticText()
		self["observationtime"] = StaticText()
		self["observationpoint"] = StaticText()
		self["feelsliketemp"] = StaticText()
		
		i = 1
		while i <= 5:
			self["weekday%s" % i] = StaticText()
			self["weekday%s_icon" %i] = WeatherIcon()
			self["weekday%s_temp" % i] = StaticText()
			i += 1
		del i
		

		self.weatherPluginEntryIndex = -1
		self.weatherPluginEntryCount = config.plugins.WeatherPlugin.entrycount.value
		if self.weatherPluginEntryCount >= 1:
			self.weatherPluginEntry = config.plugins.WeatherPlugin.Entry[0]
			self.weatherPluginEntryIndex = 1
		else:
			self.weatherPluginEntry = None


		self.webSite = ""
		
		self.weatherData = None
		self.onLayoutFinish.append(self.startRun)
		self.onClose.append(self.__onClose)
		
	def __onClose(self):
		if self.weatherData is not None:
			self.weatherData.cancel()

	def startRun(self):
		if self.weatherPluginEntry is not None:
			self["statustext"].text = _("Getting weather information...")
			if self.weatherData is not None:
				self.weatherData.cancel()
				self.weatherData = None
			self.weatherData = MSNWeather()
			self.weatherData.getWeatherData(self.weatherPluginEntry.degreetype.value, self.weatherPluginEntry.weatherlocationcode.value, self.weatherPluginEntry.city.value, self.getWeatherDataCallback, self.showIcon)
		else:
			self["statustext"].text = _("No locations defined...\nPress 'Menu' to do that.")

	def nextItem(self):
		if self.weatherPluginEntryCount != 0:
			if self.weatherPluginEntryIndex < self.weatherPluginEntryCount:
				self.weatherPluginEntryIndex = self.weatherPluginEntryIndex + 1
			else:
				self.weatherPluginEntryIndex = 1
			self.setItem()

	def previousItem(self):
		if self.weatherPluginEntryCount != 0:
			if self.weatherPluginEntryIndex >= 2:
				self.weatherPluginEntryIndex = self.weatherPluginEntryIndex - 1
			else:
				self.weatherPluginEntryIndex = self.weatherPluginEntryCount
			self.setItem()

	def setItem(self):
		self.weatherPluginEntry = config.plugins.WeatherPlugin.Entry[self.weatherPluginEntryIndex-1]
		self.clearFields()
		self.startRun()

	def clearFields(self):
		self["caption"].text = ""
		self["currentTemp"].text = ""
		self["condition"].text = ""
		self["wind_condition"].text = ""
		self["humidity"].text = ""
		self["observationtime"].text = ""
		self["observationpoint"].text = ""
		self["feelsliketemp"].text = ""
		self["currenticon"].hide()
		self.webSite = ""
		i = 1
		while i <= 5:
			self["weekday%s" % i].text = ""
			self["weekday%s_icon" %i].hide()
			self["weekday%s_temp" % i].text = ""
			i += 1

	def showIcon(self,index, filename):
		if index <> -1:
			self["weekday%s_icon" % index].updateIcon(filename)
			self["weekday%s_icon" % index].show()
		else:
			self["currenticon"].updateIcon(filename)
			self["currenticon"].show()

	def getWeatherDataCallback(self, result, errortext):
		self["statustext"].text = ""
		if result == MSNWeather.ERROR:
			self.error(errortext)
		else:
			self["caption"].text = self.weatherData.city
			self.webSite = self.weatherData.url
			for weatherData in self.weatherData.weatherItems.items():
				item = weatherData[1]
				if weatherData[0] == "-1": # current
					self["currentTemp"].text = "%s°%s" % (item.temperature, self.weatherData.degreetype)
					self["condition"].text = item.skytext
					self["humidity"].text = _("Humidity: %s %%") % item.humidity
					self["wind_condition"].text = item.winddisplay
					c =  time.strptime(item.observationtime, "%H:%M:%S")
					self["observationtime"].text = _("Observation time: %s") %  time.strftime("%H:%M",c)
					self["observationpoint"].text = _("Observation point: %s") % item.observationpoint
					self["feelsliketemp"].text = _("Feels like %s") % item.feelslike + "°" +  self.weatherData.degreetype
				else:
					index = weatherData[0]
					c = time.strptime(item.date,"%Y-%m-%d")
					self["weekday%s" % index].text = "%s\n%s" % (item.day, time.strftime("%d. %b",c))
					lowTemp = item.low
					highTemp = item.high
					self["weekday%s_temp" % index].text = "%s°%s|%s°%s\n%s" % (highTemp, self.weatherData.degreetype, lowTemp, self.weatherData.degreetype, item.skytextday)
		
		if self.weatherPluginEntryIndex == 1 and WeatherMSNComp is not None:
			WeatherMSNComp.updateWeather(self.weatherData, result, errortext)

	def config(self):
		self.session.openWithCallback(self.setupFinished, MSNWeatherPluginEntriesListConfigScreen)

	def setupFinished(self, index, entry = None):
		self.weatherPluginEntryCount = config.plugins.WeatherPlugin.entrycount.value
		if self.weatherPluginEntryCount >= 1:
			if entry is not None:
				self.weatherPluginEntry = entry
				self.weatherPluginEntryIndex = index + 1
			if self.weatherPluginEntry is None:
				self.weatherPluginEntry = config.plugins.WeatherPlugin.Entry[0]
				self.weatherPluginEntryIndex = 1
		else:
			self.weatherPluginEntry = None
			self.weatherPluginEntryIndex = -1

		self.clearFields()
		self.startRun()

	def error(self, errortext):
		self.clearFields()
		self["statustext"].text = errortext

	def showWebsite(self):
		try:
			from Plugins.Extensions.Browser.Browser import Browser
			if self.webSite:
				self.session.open(Browser, config.plugins.WebBrowser.fullscreen.value, self.webSite, False)
		except: pass # I dont care if browser is installed or not...

class WeatherIcon(Pixmap):
	def __init__(self):
		Pixmap.__init__(self)
		self.IconFileName = ""
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintIconPixmapCB)

	def onShow(self):
		Pixmap.onShow(self)
		sc = AVSwitch().getFramebufferScale()
		self._aspectRatio = eSize(sc[0], sc[1])
		self._scaleSize = self.instance.size()
		self.picload.setPara((self._scaleSize.width(), self._scaleSize.height(), sc[0], sc[1], True, 2, '#ff000000'))

	def paintIconPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr is not None:
			pic_scale_size = eSize()
			# To be added in the future:
			if 'scale' in eSize.__dict__ and self._scaleSize.isValid() and self._aspectRatio.isValid():
				pic_scale_size = ptr.size().scale(self._scaleSize, self._aspectRatio)
			# To be removed in the future:
			elif 'scaleSize' in gPixmapPtr.__dict__:
				pic_scale_size = ptr.scaleSize()

			if pic_scale_size.isValid():
				pic_scale_width = pic_scale_size.width()
				pic_scale_height = pic_scale_size.height()
				dest_rect = eRect(0, 0, pic_scale_width, pic_scale_height)
				self.instance.setScale(1)
				self.instance.setScaleDest(dest_rect)
			else:
				self.instance.setScale(0)
			self.instance.setPixmap(ptr)
		else:
			self.instance.setPixmap(None)
		
	def updateIcon(self, filename):
		new_IconFileName = filename
		if (self.IconFileName != new_IconFileName):
			self.IconFileName = new_IconFileName
			self.picload.startDecode(self.IconFileName)

