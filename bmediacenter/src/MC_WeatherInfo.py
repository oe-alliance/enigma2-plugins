# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from .__init__ import _  # for localized messages
from os import system
from requests import get, exceptions
from subprocess import check_output, Popen
from six.moves.urllib.parse import quote
from six import ensure_binary
from time import strptime, strftime
from twisted.internet import defer
from twisted.internet.reactor import callInThread
from xml.etree.cElementTree import fromstring as cet_fromstring
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER, ePicLoad, eEnv
from Components.Pixmap import Pixmap
from Components.AVSwitch import AVSwitch
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.config import ConfigSubsection, getConfigListEntry, ConfigText, ConfigSelection, ConfigSubList, configfile, ConfigInteger, config
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Tools.Directories import fileExists, pathExists
from .GlobalFunctions import Showiframe

config.plugins.mc_wi = ConfigSubsection()
config.plugins.mc_wi.entrycount = ConfigInteger(0)
config.plugins.mc_wi.Entry = ConfigSubList()


def initWeatherPluginEntryConfig():
	s = ConfigSubsection()
	s.city = ConfigText(default="Berlin", visible_width=100, fixed_size=False)
	s.degreetype = ConfigSelection(choices=[("C", _("metric system")), ("F", _("imperial system"))], default="C")
	s.weatherlocationcode = ConfigText(default="", visible_width=100, fixed_size=False)
	config.plugins.mc_wi.Entry.append(s)
	return s


def initConfig():
	count = config.plugins.mc_wi.entrycount.value
	if count != 0:
		i = 0
		while i < count:
			initWeatherPluginEntryConfig()
			i += 1


initConfig()
path = "/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/"


class WeatherIconItem:
	def __init__(self, url="", filename="", index=-1, error=False):
		self.url = url
		self.filename = filename
		self.index = index
		self.error = error


def download(item):
	return callInThread(threadDownloadPage, item.url, open(item.filename, 'wb'))


def threadDownloadPage(self, link, file):
	link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', ''))
	try:
		response = get(link)
		response.raise_for_status()
		with open(file, "wb") as f:
			f.write(response.content)
	except exceptions.RequestException as error:
		pass


def threadGetPage(self, link, success, fail=None):
	link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', ''))
	try:
		response = get(ensure_binary(link))
		response.raise_for_status()
		success(response.content)
	except exceptions.RequestException as error:
		if fail is not None:
			fail(error)


class MC_WeatherInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions"],
		{
			"back": self.exit,
			"blue": self.config,
			"right": self.nextItem,
			"left": self.previousItem
		}, -1)
		self["statustext"] = StaticText()
		self["currenticon"] = WeatherIcon()
		self["CurrentCity"] = StaticText()
		self["currentTemp"] = StaticText()
		self["condition"] = StaticText()
		self["wind_condition"] = StaticText()
		self["humidity"] = StaticText()
		self["observationtime"] = StaticText()
		self["observationpoint"] = StaticText()
		self["feelsliketemp"] = StaticText()
		self.showiframe = Showiframe()
		self.mvion = False

		i = 1
		while i <= 5:
			self["weekday%s" % i] = StaticText()
			self["weekday%s_icon" % i] = WeatherIcon()
			self["weekday%s_temp" % i] = StaticText()
			self["weekday%s_tempname" % i] = StaticText()
			i += 1
		del i

		self.appdir = eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/BMediaCenter/icons/70x70/")
		self.weatherPluginEntryIndex = -1
		self.weatherPluginEntryCount = config.plugins.mc_wi.entrycount.value
		if self.weatherPluginEntryCount >= 1:
			self.weatherPluginEntry = config.plugins.mc_wi.Entry[0]
			self.weatherPluginEntryIndex = 1
		else:
			self.weatherPluginEntry = None
		self.language = config.osd.language.value.replace("_", "-")
		if self.language == "en-EN":  # hack
			self.language = "en-US"
		self.webSite = ""
		self.onLayoutFinish.append(self.startRun)

	def exit(self):
		self.showiframe.finishStillPicture()
		self.close()

	def startRun(self):
		if self.weatherPluginEntry is not None:
			self["statustext"].text = _("Loading information...")
			url = "http://weather.service.msn.com/data.aspx?weadegreetype=%s&culture=%s&wealocations=%s" % (self.weatherPluginEntry.degreetype.value, self.language, self.weatherPluginEntry.weatherlocationcode.value)
			callInThread(threadGetPage, url, self.xmlCallback, self.error)

		else:
			self["statustext"].text = _("No locations defined...\nPress 'Blue' to do that.")

	def mvidown(self, stadt):
		downlink = "http://www.meinestadt.de/" + stadt + "/bilder"
		downname = "/tmp/.stadtindex"
		stadd = stadt
		if fileExists(downname):
			system("rm -rf " + downname)
		callInThread(self.threadDownloadPage, downlink, downname, (self.jpgdown, stadd), elf.error)

	def jpgdown(self, value, stadd):
		downlink = check_output("cat /tmp/.stadtindex | grep \"background-image:url('http://mytown.de/\" | cut -d \"'\" -f2")
		stadt = stadd
		downname = "/tmp/" + stadt + ".jpg"
		callInThread(self.threadDownloadPage, downlink, downname, (self.makemvi, stadt), self.error)
	
	def makemvi(self, value, stadt):
		mviname = "/tmp/" + stadt + ".m1v"
		if fileExists(mviname) is False:
			import subprocess
			if fileExists("/sbin/ffmpeg"):
				ffmpeg = "/sbin/ffmpeg"
			else:
				ffmpeg = "/usr/bin/ffmpeg"
			if fileExists("/sbin/ffmpeg") or fileExists("/sbin/ffmpeg"):
				cmd = [ffmpeg, "-f", "image2", "-i", "/tmp/" + stadt + ".jpg", mviname]
				Popen(cmd).wait()
			if fileExists(mviname):
				self.showiframe.showStillpicture(mviname)

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
		self.weatherPluginEntry = config.plugins.mc_wi.Entry[self.weatherPluginEntryIndex - 1]
		self.clearFields()
		self.startRun()

	def clearFields(self):
		self["CurrentCity"].text = ""
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
			self["weekday%s_icon" % i].hide()
			self["weekday%s_temp" % i].text = ""
			self["weekday%s_tempname" % i].text = ""
			i += 1

	def errorIconDownload(self, error=None, item=None):
		item.error = True

	def finishedIconDownload(self, result, item):
		if not item.error:
			self.showIcon(item.index, item.filename)

	def showIcon(self, index, filename):
		if index != -1:
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
				self["CurrentCity"].text = self.weatherPluginEntry.city.value  # childs.attrib.get("weatherlocationname").encode("utf-8", 'ignore')
				degreetype = childs.attrib.get("degreetype").encode("utf-8", 'ignore')
				imagerelativeurl = "%slaw/" % childs.attrib.get("imagerelativeurl").encode("utf-8", 'ignore')
				self.webSite = childs.attrib.get("url").encode("utf-8", 'ignore')
			for items in childs:
				if items.tag == "current":
					self["currentTemp"].text = "%s°%s" % (items.attrib.get("temperature").encode("utf-8", 'ignore'), degreetype)
					self["condition"].text = items.attrib.get("skytext").encode("utf-8", 'ignore')
					self["humidity"].text = _("Humidity: %s %%") % items.attrib.get("humidity").encode("utf-8", 'ignore')
					self["wind_condition"].text = items.attrib.get("winddisplay").encode("utf-8", 'ignore')
					c = strptime(items.attrib.get("observationtime").encode("utf-8", 'ignore'), "%H:%M:%S")
					self["observationtime"].text = _("Observation time: %s") % strftime("%H:%M", c)
					self["observationpoint"].text = _("Observation point: %s") % items.attrib.get("observationpoint").encode("utf-8", 'ignore')
					self["feelsliketemp"].text = _("Feels like %s") % items.attrib.get("feelslike").encode("utf-8", 'ignore') + "°" + degreetype
					skycode = "%s.gif" % items.attrib.get("skycode").encode("utf-8", 'ignore')
					filename = path + "icons/" + skycode
					skycodepng = "%s.png" % items.attrib.get("skycode").encode("utf-8", 'ignore')
					filenamepng = path + "icons/" + skycodepng
					if not pathExists(filenamepng):
						if not pathExists(filename):
							url = "%s%s" % (imagerelativeurl, skycode)
							IconDownloadList.append(WeatherIconItem(url=url, filename=filename, index=-1))
					else:
						self.showIcon(-1, filenamepng)
				elif items.tag == "forecast" and index <= 4:
					index += 1
					c = strptime(items.attrib.get("date").encode("utf-8", 'ignore'), "%Y-%m-%d")
					self["weekday%s" % index].text = "%s\n%s" % (items.attrib.get("day").encode("utf-8", 'ignore'), strftime("%d. %b", c))
					lowTemp = items.attrib.get("low").encode("utf-8", 'ignore')
					highTemp = items.attrib.get("high").encode("utf-8", 'ignore')
					self["weekday%s_temp" % index].text = "Min: %s°%s \n Max: %s°%s" % (lowTemp, degreetype, highTemp, degreetype)
					self["weekday%s_tempname" % index].text = "%s" % (items.attrib.get("skytextday").encode("utf-8", 'ignore'))
					skycodeday = "%s.gif" % items.attrib.get("skycodeday").encode("utf-8", 'ignore')
					skycodedaypng = "%s.png" % items.attrib.get("skycodeday").encode("utf-8", 'ignore')
					filename = self.appdir + skycodeday
					filenamepng = self.appdir + skycodedaypng
					if not pathExists(filenamepng):
						if not pathExists(filename):
							url = "%s%s" % (imagerelativeurl, skycodeday)
							IconDownloadList.append(WeatherIconItem(url=url, filename=filename, index=index))
					else:
						self.showIcon(index, filenamepng)
		if len(IconDownloadList) != 0:
			ds = defer.DeferredSemaphore(tokens=len(IconDownloadList))
			downloads = [ds.run(download, item).addErrback(self.errorIconDownload, item).addCallback(self.finishedIconDownload, item) for item in IconDownloadList]
			finished = defer.DeferredList(downloads).addErrback(self.error)
		stadt = config.plugins.mc_wi.Entry[self.weatherPluginEntryIndex - 1].city.value
		stadt = stadt.split(",")[0]
		stadt = stadt.replace('Ä', 'Ae')
		stadt = stadt.replace('ä', 'ae')
		stadt = stadt.replace('Ö', 'Oe')
		stadt = stadt.replace('ö', 'oe')
		stadt = stadt.replace('Ü', 'Ue')
		stadt = stadt.replace('ü', 'ue')
		stadt = stadt.replace('ß', 'ss')
		stadt = stadt.lower()
		if self.mvion == True:
			self.showiframe.finishStillPicture()
		bild = "/tmp/" + stadt + ".m1v"
		if fileExists(bild):
			self.showiframe.showStillpicture(bild)
			self.mvion = True
		else:
			self.mvidown(stadt)

	def config(self):
		self.session.openWithCallback(self.setupFinished, WeatherSetup)

	def setupFinished(self, index, entry=None):
		self.weatherPluginEntryCount = config.plugins.mc_wi.entrycount.value
		if self.weatherPluginEntryCount >= 1:
			if entry is not None:
				self.weatherPluginEntry = entry
				self.weatherPluginEntryIndex = index + 1
			if self.weatherPluginEntry is None:
				self.weatherPluginEntry = config.plugins.mc_wi.Entry[0]
				self.weatherPluginEntryIndex = 1
		else:
			self.weatherPluginEntry = None
			self.weatherPluginEntryIndex = -1
		self.clearFields()
		self.startRun()

	def error(self, error=None):
		self.mvion = False
		self.showiframe.showStillpicture("/usr/share/enigma2/black.mvi")
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
		self.picload.setPara((self.instance.size().width(), self.instance.size().height(), sc[0], sc[1], True, 2, '#ff000000'))

	def paintIconPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr is not None:
			self.instance.setPixmap(ptr.__deref__())
		else:
			self.instance.setPixmap(None)

	def updateIcon(self, filename):
		new_IconFileName = filename
		if (self.IconFileName != new_IconFileName):
			self.IconFileName = new_IconFileName
			self.picload.startDecode(self.IconFileName)


class WeatherSetup(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.title = _("WeatherPlugin: List of Entries")
		self["city"] = StaticText(_("City"))
		self["degreetype"] = StaticText(_("System"))
		self["key_red"] = StaticText(_("Back"))
		self["key_green"] = StaticText(_("Add"))
		self["key_yellow"] = StaticText(_("Edit"))
		self["key_blue"] = StaticText(_("Delete"))
		self["entrylist"] = WeatherPluginEntryList([])
		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions"],
			{
			 "ok": self.keyOK,
			 "back": self.keyClose,
			 "red": self.keyClose,
			 "green": self.keyGreen,
			 "yellow": self.keyYellow,
			 "blue": self.keyDelete,
			 }, -1)
		self.updateList()

	def updateList(self):
		self["entrylist"].buildList()

	def keyClose(self):
		self.close(-1, None)

	def keyGreen(self):
		self.session.openWithCallback(self.updateList, MSNWeatherPluginEntryConfigScreen, None)

	def keyOK(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		self.close(self["entrylist"].getCurrentIndex(), sel)

	def keyYellow(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.updateList, MSNWeatherPluginEntryConfigScreen, sel)

	def keyDelete(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		sel = self["entrylist"].l.getCurrentSelection()[0]
		config.plugins.mc_wi.entrycount.value -= 1
		config.plugins.mc_wi.entrycount.save()
		config.plugins.mc_wi.Entry.remove(sel)
		config.plugins.mc_wi.Entry.save()
		config.plugins.mc_wi.save()
		configfile.save()
		self.updateList()


class WeatherPluginEntryList(MenuList):
	def __init__(self, list, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(20)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def buildList(self):
		list = []
		for c in config.plugins.mc_wi.Entry:
			res = [
				c,
				(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 400, 20, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(c.city.value)),
				(eListboxPythonMultiContent.TYPE_TEXT, 410, 0, 80, 20, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(c.degreetype .value)),
			]
			list.append(res)
		self.list = list
		self.l.setList(list)
		self.moveToIndex(0)


class MSNWeatherPluginEntryConfigScreen(ConfigListScreen, Screen):
	skin = """
		<screen name="MSNWeatherPluginEntryConfigScreen" position="center,center" size="550,400">
			<widget name="config" position="20,60" size="520,300" scrollbarMode="showOnDemand" />
			<ePixmap position="0,10" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,10" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="420,10" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<ePixmap position="280,10" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="0,10" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="140,10" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_yellow" position="280,10" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="yellow" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_blue" render="Label" position="420,10" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, entry):
		Screen.__init__(self, session)
		self.title = _("WeatherPlugin: Edit Entry")
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"blue": self.keyDelete,
			"yellow": self.searchLocation,
			"cancel": self.keyCancel
		}, -2)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_blue"] = StaticText(_("Delete"))
		self["key_yellow"] = StaticText(_("Search Code"))

		if entry is None:
			self.newmode = 1
			self.current = initWeatherPluginEntryConfig()
		else:
			self.newmode = 0
			self.current = entry
		cfglist = [
			getConfigListEntry(_("City"), self.current.city),
			getConfigListEntry(_("Location code"), self.current.weatherlocationcode),
			getConfigListEntry(_("System"), self.current.degreetype)
		]
		ConfigListScreen.__init__(self, cfglist, session)

	def searchLocation(self):
		if self.current.city.value != "":
			language = config.osd.language.value.replace("_", "-")
			if language == "en-EN":  # hack
				language = "en-US"
			url = "http://weather.service.msn.com/find.aspx?outputview=search&weasearchstr=%s&culture=%s" % (quote(self.current.city.value), language)
			callInThread(threadGetPage, url, self.xmlCallback, self.error)
		else:
			self.session.open(MessageBox, _("You need to enter a valid city name before you can search for the location code."), MessageBox.TYPE_ERROR)

	def keySave(self):
		if self.current.city.value != "" and self.current.weatherlocationcode.value != "":
			if self.newmode == 1:
				config.plugins.mc_wi.entrycount.value = config.plugins.mc_wi.entrycount.value + 1
				config.plugins.mc_wi.entrycount.save()
			ConfigListScreen.keySave(self)
			config.plugins.mc_wi.save()
			configfile.save()
			self.close()
		else:
			if self.current.city.value == "":
				self.session.open(MessageBox, _("Please enter a valid city name."), MessageBox.TYPE_ERROR)
			else:
				self.session.open(MessageBox, _("Please enter a valid location code for the city."), MessageBox.TYPE_ERROR)

	def keyCancel(self):
		if self.newmode == 1:
			config.plugins.mc_wi.Entry.remove(self.current)
		ConfigListScreen.cancelConfirm(self, True)

	def keyDelete(self):
		if self.newmode == 1:
			self.keyCancel()
		else:
			self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this WeatherPlugin Entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		config.plugins.mc_wi.entrycount.value = config.plugins.mc_wi.entrycount.value - 1
		config.plugins.mc_wi.entrycount.save()
		config.plugins.mc_wi.Entry.remove(self.current)
		config.plugins.mc_wi.Entry.save()
		config.plugins.mc_wi.save()
		configfile.save()
		self.close()

	def xmlCallback(self, xmlstring):
		if xmlstring:
			self.session.openWithCallback(self.searchCallback, MSNWeatherPluginSearch, xmlstring)

	def error(self, error=None):
		if error is not None:
			print(error)

	def searchCallback(self, result):
		if result:
			self.current.weatherlocationcode.value = result[0]
			self.current.city.value = result[1]


class MSNWeatherPluginSearch(Screen):
	skin = """
		<screen name="MSNWeatherPluginSearch" position="center,center" size="550,400">
			<widget name="entrylist" position="0,60" size="550,200" scrollbarMode="showOnDemand"/>
			<widget render="Label" source="key_red" position="0,10" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,10" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="green" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap position="0,10" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,10" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,10" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,10" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session, xmlstring):
		Screen.__init__(self, session)
		self.title = _("MSN location search result")
		self["key_red"] = StaticText(_("Back"))
		self["key_green"] = StaticText(_("OK"))
		self["entrylist"] = MSNWeatherPluginSearchResultList([])
		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions"],
			{
			 "ok": self.keyOK,
			 "green": self.keyOK,
			 "back": self.keyClose,
			 "red": self.keyClose,
			 }, -1)
		self.updateList(xmlstring)

	def updateList(self, xmlstring):
		self["entrylist"].buildList(xmlstring)

	def keyClose(self):
		self.close(None)

	def keyOK(self):
		pass
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		self.close(sel)


class MSNWeatherPluginSearchResultList(MenuList):
	def __init__(self, list, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(44)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def buildList(self, xml):
		root = cet_fromstring(xml)
		searchlocation = ""
		searchresult = ""
		weatherlocationcode = ""
		list = []
		for childs in root:
			if childs.tag == "weather":
				searchlocation = childs.attrib.get("searchlocation").encode("utf-8", 'ignore')
				searchresult = childs.attrib.get("searchresult").encode("utf-8", 'ignore')
				weatherlocationcode = childs.attrib.get("weatherlocationcode").encode("utf-8", 'ignore')
				res = [
					(weatherlocationcode, searchlocation),
					(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 500, 20, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, searchlocation),
					(eListboxPythonMultiContent.TYPE_TEXT, 5, 22, 500, 20, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, searchresult),
				]
				list.append(res)
		self.list = list
		self.l.setList(list)
		self.moveToIndex(0)
