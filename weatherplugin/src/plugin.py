# -*- coding: utf-8 -*-
#
#  Weather Plugin E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2009
#  Support: www.dreambox-tools.info
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#

# for localized messages
from . import _

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from xml.etree.cElementTree import fromstring as cet_fromstring
from twisted.internet import defer
from twisted.web.client import getPage, downloadPage
from urllib import quote
from Components.Pixmap import Pixmap
from enigma import ePicLoad
from os import path as os_path, mkdir as os_mkdir
from Components.AVSwitch import AVSwitch
from Components.config import ConfigSubsection, ConfigSubList, ConfigInteger, config
from setup import initConfig, WeatherPluginEntriesListConfigScreen

config.plugins.WeatherPlugin = ConfigSubsection()
config.plugins.WeatherPlugin.entriescount =  ConfigInteger(0)
config.plugins.WeatherPlugin.Entries = ConfigSubList()
initConfig()

UserAgent = "Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.0.15) Gecko/2009102815 Ubuntu/9.04 (jaunty) Firefox/3."

class WeatherIconItem:
	def __init__(self, url = "", filename = "", index = -1, error = False):
		self.url = url
		self.filename = filename
		self.index = index
		self.error = error

def getXML(url):
	return getPage(url, agent=UserAgent)

def download(item):
	return downloadPage(item.url, file(item.filename, 'wb'), agent=UserAgent)


def main(session,**kwargs):
	session.open(WeatherPlugin)

def Plugins(**kwargs):
	list = [PluginDescriptor(name=_("Weather Plugin"), description=_("Weather Plugin"), where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main)]
	return list


class WeatherPlugin(Screen):

	skin = """
		<screen name="WeatherPlugin" position="center,center" size="664,190" title="%s">
			<widget render="Label" source="caption" position="10,20" zPosition="1" size="300,23" font="Regular;22" transparent="1"/>
			<widget render="Label" source="currentTemp" position="10,45" zPosition="1" size="300,23" font="Regular;22" transparent="1"/>
			<widget render="Label" source="condition" position="10,100" zPosition="1" size="300,20" font="Regular;18" transparent="1"/>
			<widget render="Label" source="wind_condition" position="10,125" zPosition="1" size="300,20" font="Regular;18" transparent="1"/>
			<widget render="Label" source="humidity" position="10,150" zPosition="1" size="300,20" font="Regular;18" valign="bottom" transparent="1"/>
			<widget render="Label" source="weekday1" position="255,50" zPosition="1" size="72,20" halign="center" valign="center" font="Regular;18" transparent="1"/>
			<widget name="weekday1_icon" position="255,70" zPosition="1" size="72,72" alphatest="blend"/>
			<widget render="Label" source="weekday1_temp" position="241,150" zPosition="1" size="100,20" halign="center" valign="bottom" font="Regular;16" transparent="1"/>
			<widget render="Label" source="weekday2" position="358,50" zPosition="1" size="72,20" halign="center" valign="center" font="Regular;18" transparent="1"/>
			<widget name="weekday2_icon" position="358,70" zPosition="1" size="72,72" alphatest="blend"/>
			<widget render="Label" source="weekday2_temp" position="344,150" zPosition="1" size="100,20" halign="center" valign="bottom" font="Regular;16" transparent="1"/>
			<widget render="Label" source="weekday3" position="461,50" zPosition="1" size="72,20" halign="center" valign="center" font="Regular;18" transparent="1"/>
			<widget name="weekday3_icon" position="461,70" zPosition="1" size="72,72" alphatest="blend"/>
			<widget render="Label" source="weekday3_temp" position="448,150" zPosition="1" size="100,20" halign="center" valign="bottom" font="Regular;16" transparent="1"/>
			<widget render="Label" source="weekday4" position="564,50" zPosition="1" size="72,20" halign="center" valign="center" font="Regular;18" transparent="1"/>
			<widget name="weekday4_icon" position="564,70" zPosition="1" size="72,72" alphatest="blend"/>
			<widget render="Label" source="weekday4_temp" position="550,150" zPosition="1" size="100,20" halign="center" valign="bottom" font="Regular;16" transparent="1"/>
			<widget render="Label" source="statustext" position="0,0" zPosition="1" size="664,190" font="Regular;20" halign="center" valign="center" transparent="1"/>
		</screen>""" %  _("Weather Plugin")
	
	def __init__(self, session):
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions"],
		{
			"back": self.close,
			"input_date_time": self.config,
			"right": self.nextItem,
			"left": self.previousItem
		}, -1)

		self["statustext"] = StaticText()
		self["caption"] = StaticText()
		self["currentTemp"] = StaticText()
		self["condition"] = StaticText()
		self["wind_condition"] = StaticText()
		self["humidity"] = StaticText()

		i = 1
		while i < 5:
			self["weekday%s" % i] = StaticText()
			self["weekday%s_icon" %i] = WeatherIcon()
			self["weekday%s_temp" % i] = StaticText()
			i += 1
		del i

		self.appdir = "/usr/lib/enigma2/python/Plugins/Extensions/WeatherPlugin/icons/" 
		if not os_path.exists(self.appdir):
			os_mkdir(self.appdir)

		self.weatherPluginEntryIndex = -1
		self.weatherPluginEntryCount = config.plugins.WeatherPlugin.entriescount.value
		if self.weatherPluginEntryCount >= 1:
			self.weatherPluginEntry = config.plugins.WeatherPlugin.Entries[0]
			self.weatherPluginEntryIndex = 1
		else:
			self.weatherPluginEntry = None

		self.onLayoutFinish.append(self.startRun)

	def startRun(self):
		if self.weatherPluginEntry is not None:
			self["statustext"].text = _("Getting weather information...")
			url = ("http://www.google.com/ig/api?weather=%s&hl=%s" % (quote(self.weatherPluginEntry.city.value), self.weatherPluginEntry.language.value))
			getXML(url).addCallback(self.xmlCallback).addErrback(self.error)
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
		self.weatherPluginEntry = config.plugins.WeatherPlugin.Entries[self.weatherPluginEntryIndex-1]
		self.clearFields()
		self.startRun()

	def clearFields(self):
		self["caption"].text = ""
		self["currentTemp"].text = ""
		self["condition"].text = ""
		self["wind_condition"].text = ""
		self["humidity"].text = ""
		i = 1
		while i < 5:
			self["weekday%s" % i].text = ""
			self["weekday%s_icon" %i].hide()
			self["weekday%s_temp" % i].text = ""
			i += 1

	def errorIconDownload(self, error = None, item = None):
		item.error = True

	def finishedIconDownload(self, result, item):
		if not item.error:
			self.showIcon(item.index,item.filename)

	def showIcon(self,index, filename):
		self["weekday%s_icon" % index].updateIcon(filename)
		self["weekday%s_icon" % index].show()

	def xmlCallback(self, xmlstring):
		self["statustext"].text = ""
		metric = 0
		index = 0
		UnitSystemText = "F"
		IconDownloadList = []
		root = cet_fromstring(xmlstring)
		for childs in root.findall("weather"):
			for items in childs:
				if items.tag == "problem_cause":
					self["statustext"].text = items.attrib.get("data").encode("utf-8", 'ignore')
				elif items.tag == "forecast_information":
					for items2 in items:
						if items2.tag == "city":
							self["caption"].text = items2.attrib.get("data").encode("utf-8", 'ignore')
						elif items2.tag == "unit_system":
							if items2.attrib.get("data").encode("utf-8", 'ignore') == "SI":
								metric = 1
								UnitSystemText = "C"
				elif items.tag == "current_conditions":
					for items2 in items:
						if items2.tag == "condition":
							self["condition"].text = _("Current: %s") % items2.attrib.get("data").encode("utf-8", 'ignore')
						elif items2.tag == "temp_f" and metric == 0:
							self["currentTemp"].text =  ("%s °F" % items2.attrib.get("data").encode("utf-8", 'ignore')) 
						elif items2.tag == "temp_c" and metric == 1:
							self["currentTemp"].text =  ("%s °C" % items2.attrib.get("data").encode("utf-8", 'ignore')) 
						elif items2.tag == "humidity":
							self["humidity"].text = items2.attrib.get("data").encode("utf-8", 'ignore')
						elif items2.tag == "wind_condition":
							self["wind_condition"].text = items2.attrib.get("data").encode("utf-8", 'ignore')
				elif items.tag == "forecast_conditions":
					index = index + 1
					lowTemp = ""
					highTemp = ""
					icon = ""
					for items2 in items:
						if items2.tag == "day_of_week":
							self["weekday%s" % index].text = items2.attrib.get("data").encode("utf-8", 'ignore')
						elif items2.tag == "low":
							lowTemp = items2.attrib.get("data").encode("utf-8", 'ignore')
						elif items2.tag == "high":
							highTemp = items2.attrib.get("data").encode("utf-8", 'ignore')
							self["weekday%s_temp" % index].text = "%s °%s | %s °%s" % (highTemp, UnitSystemText, lowTemp, UnitSystemText)
						elif items2.tag == "icon":
							url = "http://www.google.com%s" % items2.attrib.get("data").encode("utf-8", 'ignore')
							parts = url.split("/")
							filename = self.appdir + parts[-1]
							if not os_path.exists(filename):
								IconDownloadList.append(WeatherIconItem(url = url,filename = filename, index = index))
							else:
								self.showIcon(index,filename)
		if len(IconDownloadList) != 0:
			ds = defer.DeferredSemaphore(tokens=len(IconDownloadList))
			downloads = [ds.run(download,item ).addErrback(self.errorIconDownload, item).addCallback(self.finishedIconDownload,item) for item in IconDownloadList]
			finished = defer.DeferredList(downloads).addErrback(self.error)

	def config(self):
		self.session.openWithCallback(self.setupFinished, WeatherPluginEntriesListConfigScreen)

	def setupFinished(self, index, entry = None):
		self.weatherPluginEntryCount = config.plugins.WeatherPlugin.entriescount.value
		if self.weatherPluginEntryCount >= 1:
			if entry is not None:
				self.weatherPluginEntry = entry
				self.weatherPluginEntryIndex = index + 1
			if self.weatherPluginEntry is None:
				self.weatherPluginEntry = config.plugins.WeatherPlugin.Entries[0]
				self.weatherPluginEntryIndex = 1
		else:
			self.weatherPluginEntry = None
			self.weatherPluginEntryIndex = -1

		self.clearFields()
		self.startRun()

	def error(self, error = None):
		if error is not None:
			self.clearFields()
			self["statustext"].text = str(error.getErrorMessage())


class WeatherIcon(Pixmap):
	def __init__(self):
		Pixmap.__init__(self)
		self.IconFileName = ""
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintIconPixmapCB)

	def onShow(self):
		Pixmap.onShow(self)
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((self.instance.size().width(), self.instance.size().height(), sc[0], sc[1], 0, 0, '#00000000'))

	def paintIconPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr != None:
			self.instance.setPixmap(ptr.__deref__())

	def updateIcon(self, filename):
		new_IconFileName = filename
		if (self.IconFileName != new_IconFileName):
			self.IconFileName = new_IconFileName
			self.picload.startDecode(self.IconFileName)

