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
from xml.etree.cElementTree import fromstring as cet_fromstring
from twisted.internet import defer
from twisted.web.client import getPage, downloadPage
from urllib import quote
from Components.Pixmap import Pixmap
from enigma import ePicLoad, eEnv
from os import path as os_path, mkdir as os_mkdir
from Components.AVSwitch import AVSwitch
from Components.config import ConfigSubsection, ConfigSubList, ConfigInteger, config
from setup import initConfig, MSNWeatherPluginEntriesListConfigScreen
import time
config.plugins.WeatherPlugin = ConfigSubsection()
config.plugins.WeatherPlugin.entrycount =  ConfigInteger(0)
config.plugins.WeatherPlugin.Entry = ConfigSubList()
initConfig()

class WeatherIconItem:
	def __init__(self, url = "", filename = "", index = -1, error = False):
		self.url = url
		self.filename = filename
		self.index = index
		self.error = error

def download(item):
	return downloadPage(item.url, file(item.filename, 'wb'))


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
			<widget render="Label" source="feelsliketemp" position="90,120" zPosition="1" size="140,20" font="Regular;14" transparent="1"/>
			<widget render="Label" source="condition" position="270,95" zPosition="1" size="300,20" font="Regular;18" transparent="1"/>
			<widget render="Label" source="wind_condition" position="270,115" zPosition="1" size="300,20" font="Regular;18" transparent="1"/>
			<widget render="Label" source="humidity" position="270,135" zPosition="1" size="300,20" font="Regular;18" valign="bottom" transparent="1"/>
			<widget render="Label" source="weekday1" position="35,170" zPosition="1" size="105,40" halign="center" valign="center" font="Regular;18" transparent="1"/>
			<widget name="weekday1_icon" position="60,215" zPosition="1" size="55,45" alphatest="on"/>
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
		

		self.appdir = eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/WeatherPlugin/icons/")
		if not os_path.exists(self.appdir):
			os_mkdir(self.appdir)

		self.weatherPluginEntryIndex = -1
		self.weatherPluginEntryCount = config.plugins.WeatherPlugin.entrycount.value
		if self.weatherPluginEntryCount >= 1:
			self.weatherPluginEntry = config.plugins.WeatherPlugin.Entry[0]
			self.weatherPluginEntryIndex = 1
		else:
			self.weatherPluginEntry = None

		self.language = config.osd.language.value.replace("_","-")
		if self.language == "en-EN": # hack
			self.language = "en-US"
		self.webSite = ""		
		self.onLayoutFinish.append(self.startRun)

	def startRun(self):
		if self.weatherPluginEntry is not None:
			self["statustext"].text = _("Getting weather information...")
			url = "http://weather.service.msn.com/data.aspx?weadegreetype=%s&culture=%s&wealocations=%s" % (self.weatherPluginEntry.degreetype.value, self.language, self.weatherPluginEntry.weatherlocationcode.value)
			getPage(url).addCallback(self.xmlCallback).addErrback(self.error)
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

	def errorIconDownload(self, error = None, item = None):
		item.error = True

	def finishedIconDownload(self, result, item):
		if not item.error:
			self.showIcon(item.index,item.filename)

	def showIcon(self,index, filename):
		if index <> -1:
			self["weekday%s_icon" % index].updateIcon(filename)
			self["weekday%s_icon" % index].show()
		else:
			self["currenticon"].updateIcon(filename)
			self["currenticon"].show()

	def xmlCallback(self, xmlstring):
		self["statustext"].text = ""
		IconDownloadList = []
		root = cet_fromstring(xmlstring)
		index = 0
		degreetype = "C"
		imagerelativeurl = ""
		errormessage = ""
		for childs in root:
			if childs.tag == "weather":
				errormessage = childs.attrib.get("errormessage")
				if errormessage:
					self["statustext"].text = errormessage.encode("utf-8", 'ignore')
					break
				self["caption"].text = self.weatherPluginEntry.city.value #childs.attrib.get("weatherlocationname").encode("utf-8", 'ignore')
				degreetype = childs.attrib.get("degreetype").encode("utf-8", 'ignore')
				imagerelativeurl = "%slaw/" % childs.attrib.get("imagerelativeurl").encode("utf-8", 'ignore')
				self.webSite = childs.attrib.get("url").encode("utf-8", 'ignore')
			for items in childs:
				if items.tag == "current":
					self["currentTemp"].text = "%s°%s" % (items.attrib.get("temperature").encode("utf-8", 'ignore') , degreetype)
					self["condition"].text = items.attrib.get("skytext").encode("utf-8", 'ignore')
					self["humidity"].text = _("Humidity: %s %%") % items.attrib.get("humidity").encode("utf-8", 'ignore')
					self["wind_condition"].text = items.attrib.get("winddisplay").encode("utf-8", 'ignore')
					c =  time.strptime(items.attrib.get("observationtime").encode("utf-8", 'ignore'), "%H:%M:%S")
					self["observationtime"].text = _("Observation time: %s") %  time.strftime("%H:%M",c)
					self["observationpoint"].text = _("Observation point: %s") % items.attrib.get("observationpoint").encode("utf-8", 'ignore')
					self["feelsliketemp"].text = _("Feels like %s") % items.attrib.get("feelslike").encode("utf-8", 'ignore') + "°" +  degreetype
					skycode = "%s.gif" % items.attrib.get("skycode").encode("utf-8", 'ignore')
					filename = self.appdir + skycode
					if not os_path.exists(filename):
						url = "%s%s" % (imagerelativeurl, skycode)
						IconDownloadList.append(WeatherIconItem(url = url,filename = filename, index = -1))
					else:
						self.showIcon(-1,filename)
				elif items.tag == "forecast" and index <= 4:
					index +=1
					c = time.strptime(items.attrib.get("date").encode("utf-8", 'ignore'),"%Y-%m-%d")
					self["weekday%s" % index].text = "%s\n%s" % (items.attrib.get("day").encode("utf-8", 'ignore'), time.strftime("%d. %b",c))
					lowTemp = items.attrib.get("low").encode("utf-8", 'ignore')
					highTemp = items.attrib.get("high").encode("utf-8", 'ignore')
					self["weekday%s_temp" % index].text = "%s°%s|%s°%s\n%s" % (highTemp, degreetype, lowTemp, degreetype, items.attrib.get("skytextday").encode("utf-8", 'ignore'))
					skycodeday = "%s.gif" % items.attrib.get("skycodeday").encode("utf-8", 'ignore')
					filename = self.appdir + skycodeday
					if not os_path.exists(filename):
						url = "%s%s" % (imagerelativeurl, skycodeday)
						IconDownloadList.append(WeatherIconItem(url = url,filename = filename, index = index))
					else:
						self.showIcon(index,filename)
		if len(IconDownloadList) != 0:
			ds = defer.DeferredSemaphore(tokens=len(IconDownloadList))
			downloads = [ds.run(download,item ).addErrback(self.errorIconDownload, item).addCallback(self.finishedIconDownload,item) for item in IconDownloadList]
			finished = defer.DeferredList(downloads).addErrback(self.error)

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

	def error(self, error = None):
		if error is not None:
			self.clearFields()
			self["statustext"].text = str(error.getErrorMessage())

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
		self.picload.setPara((self.instance.size().width(), self.instance.size().height(), sc[0], sc[1], True, 2, '#ff000000'))

	def paintIconPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr is not None:
			try:
				pic_scale_size = ptr.scaleSize()
				if pic_scale_size.isValid():
					pic_scale_width = pic_scale_size.width()
					pic_scale_height = pic_scale_size.height()
					dest_rect = eRect(0, 0, pic_scale_width, pic_scale_height)
					self.instance.setScale(1)
					self.instance.setScaleDest(dest_rect)
				else:
					self.instance.setScale(0)
			except:
				self.instance.setScale(0)
			self.instance.setPixmap(ptr)
		else:
			self.instance.setPixmap(None)
		
	def updateIcon(self, filename):
		new_IconFileName = filename
		if (self.IconFileName != new_IconFileName):
			self.IconFileName = new_IconFileName
			self.picload.startDecode(self.IconFileName)

