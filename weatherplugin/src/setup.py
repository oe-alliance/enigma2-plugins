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

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, \
	RT_VALIGN_CENTER
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import ConfigSubsection, ConfigText, ConfigSelection, \
	getConfigListEntry, config, configfile
from xml.etree.cElementTree import fromstring as cet_fromstring
from twisted.web.client import getPage
from urllib import quote as urllib_quote

def initWeatherPluginEntryConfig():
	s = ConfigSubsection()
	s.city = ConfigText(default = "Heidelberg", visible_width = 100, fixed_size = False)
	s.degreetype = ConfigSelection(choices = [("C", _("metric system")), ("F", _("imperial system"))], default = "C")
	s.weatherlocationcode = ConfigText(default = "", visible_width = 100, fixed_size = False)
	config.plugins.WeatherPlugin.Entry.append(s)
	return s

def initConfig():
	count = config.plugins.WeatherPlugin.entrycount.value
	if count != 0:
		i = 0
		while i < count:
			initWeatherPluginEntryConfig()
			i += 1

class MSNWeatherPluginEntriesListConfigScreen(Screen):
	skin = """
		<screen name="MSNWeatherPluginEntriesListConfigScreen" position="center,center" size="550,400">
			<widget render="Label" source="city" position="5,60" size="400,50" font="Regular;20" halign="left"/>
			<widget render="Label" source="degreetype" position="410,60" size="130,50" font="Regular;20" halign="left"/>
			<widget name="entrylist" position="0,80" size="550,300" scrollbarMode="showOnDemand"/>
			<widget render="Label" source="key_red" position="0,10" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,10" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="green" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_yellow" position="280,10" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="yellow" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_blue" position="420,10" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap position="0,10" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,10" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,10" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,10" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		</screen>"""

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
		self["actions"] = ActionMap(["WizardActions","MenuActions","ShortcutActions"],
			{
			 "ok"	:	self.keyOK,
			 "back"	:	self.keyClose,
			 "red"	:	self.keyClose,
			 "green":	self.keyGreen,			 
			 "yellow":	self.keyYellow,
			 "blue": 	self.keyDelete,
			 }, -1)
		self.updateList()

	def updateList(self):
		self["entrylist"].buildList()

	def keyClose(self):
		self.close(-1, None)

	def keyGreen(self):
		self.session.openWithCallback(self.updateList,MSNWeatherPluginEntryConfigScreen,None)

	def keyOK(self):
		try:sel = self["entrylist"].l.getCurrentSelection()[0]
		except: sel = None
		self.close(self["entrylist"].getCurrentIndex(), sel)

	def keyYellow(self):
		try:sel = self["entrylist"].l.getCurrentSelection()[0]
		except: sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.updateList,MSNWeatherPluginEntryConfigScreen,sel)

	def keyDelete(self):
		try:sel = self["entrylist"].l.getCurrentSelection()[0]
		except: sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this WeatherPlugin Entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		sel = self["entrylist"].l.getCurrentSelection()[0]
		config.plugins.WeatherPlugin.entrycount.value -= 1
		config.plugins.WeatherPlugin.entrycount.save()
		config.plugins.WeatherPlugin.Entry.remove(sel)
		config.plugins.WeatherPlugin.Entry.save()
		config.plugins.WeatherPlugin.save()
		configfile.save()
		self.updateList()

class WeatherPluginEntryList(MenuList):
	def __init__(self, list, enableWrapAround = True):
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
		for c in config.plugins.WeatherPlugin.Entry:
			res = [
				c,
				(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 400, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(c.city.value)),
				(eListboxPythonMultiContent.TYPE_TEXT, 410, 0, 80, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(c.degreetype .value)),
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
			language = config.osd.language.value.replace("_","-")
			if language == "en-EN": # hack
				language = "en-US"
			elif language == "no-NO": # hack
				language = "nn-NO"
			url = "http://weather.service.msn.com/find.aspx?src=vista&outputview=search&weasearchstr=%s&culture=%s" % (urllib_quote(self.current.city.value), language)
			getPage(url).addCallback(self.xmlCallback).addErrback(self.error)
		else:
			self.session.open(MessageBox, _("You need to enter a valid city name before you can search for the location code."), MessageBox.TYPE_ERROR)

	def keySave(self):
		if self.current.city.value != "" and self.current.weatherlocationcode.value != "":
			if self.newmode == 1:
				config.plugins.WeatherPlugin.entrycount.value = config.plugins.WeatherPlugin.entrycount.value + 1
				config.plugins.WeatherPlugin.entrycount.save()
			ConfigListScreen.keySave(self)
			config.plugins.WeatherPlugin.save()
			configfile.save()
			self.close()
		else:
			if self.current.city.value == "":
				self.session.open(MessageBox, _("Please enter a valid city name."), MessageBox.TYPE_ERROR)
			else:
				self.session.open(MessageBox, _("Please enter a valid location code for the city."), MessageBox.TYPE_ERROR)

	def keyCancel(self):
		if self.newmode == 1:
			config.plugins.WeatherPlugin.Entry.remove(self.current)
		ConfigListScreen.cancelConfirm(self, True)

	def keyDelete(self):
		if self.newmode == 1:
			self.keyCancel()
		else:		
			self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this WeatherPlugin Entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		config.plugins.WeatherPlugin.entrycount.value = config.plugins.WeatherPlugin.entrycount.value - 1
		config.plugins.WeatherPlugin.entrycount.save()
		config.plugins.WeatherPlugin.Entry.remove(self.current)
		config.plugins.WeatherPlugin.Entry.save()
		config.plugins.WeatherPlugin.save()
		configfile.save()
		self.close()
		
		
	def xmlCallback(self, xmlstring):
		if xmlstring:
			errormessage = ""
			root = cet_fromstring(xmlstring)
			for childs in root:
				if childs.tag == "weather" and childs.attrib.has_key("errormessage"):
					errormessage = childs.attrib.get("errormessage").encode("utf-8", 'ignore')
					break
			if len(errormessage) !=0:
				self.session.open(MessageBox, errormessage, MessageBox.TYPE_ERROR)					
			else:
				self.session.openWithCallback(self.searchCallback, MSNWeatherPluginSearch, xmlstring)
			
	def error(self, error = None):
		if error is not None:
			print error
		
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
		self["actions"] = ActionMap(["WizardActions","MenuActions","ShortcutActions"],
			{
			 "ok"	:	self.keyOK,
			 "green": self.keyOK,
			 "back"	:	self.keyClose,
			 "red": self.keyClose,
			 }, -1)
		self.updateList(xmlstring)

	def updateList(self, xmlstring):
		self["entrylist"].buildList(xmlstring)

	def keyClose(self):
		self.close(None)

	def keyOK(self):
		pass
		try:sel = self["entrylist"].l.getCurrentSelection()[0]
		except: sel = None
		self.close(sel)
		

class MSNWeatherPluginSearchResultList(MenuList):
	def __init__(self, list, enableWrapAround = True):
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
					(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 500, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, searchlocation),
					(eListboxPythonMultiContent.TYPE_TEXT, 5, 22, 500, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, searchresult),
				]
				list.append(res)
		self.list = list
		self.l.setList(list)
		self.moveToIndex(0)
