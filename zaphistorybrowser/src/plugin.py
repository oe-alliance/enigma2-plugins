# -*- coding: UTF-8 -*-
## Zap-History Browser by AliAbdul
from Components.ActionMap import ActionMap
from Components.config import config, ConfigInteger, ConfigSelection, \
		ConfigYesNo, ConfigSet, ConfigSubsection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, eServiceCenter, \
		eServiceReference, gFont
from Plugins.Plugin import PluginDescriptor
from Screens.ChannelSelection import ChannelSelection
from Screens.ParentalControlSetup import ProtectedScreen
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
from enigma import eServiceReference
import os, gettext

################################################

PluginLanguageDomain = "ZapHistoryBrowser"
PluginLanguagePath = "Extensions/ZapHistoryBrowser/locale/"

def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
		return gettext.gettext(txt)

language.addCallback(localeInit())

################################################

config.plugins.ZapHistoryConfigurator = ConfigSubsection()
config.plugins.ZapHistoryConfigurator.enable_zap_history = ConfigSelection(choices = {"off": _("disabled"), "on": _("enabled"), "parental_lock": _("disabled at parental lock")}, default="on")
config.plugins.ZapHistoryConfigurator.maxEntries_zap_history = ConfigInteger(default=20, limits=(1, 60))
config.plugins.ZapHistoryConfigurator.e1_like_history = ConfigYesNo(default = False)
config.plugins.ZapHistoryConfigurator.history_tv = ConfigSet(choices = [])
config.plugins.ZapHistoryConfigurator.history_radio = ConfigSet(choices = [])

################################################

def addToHistory(instance, ref):
	if config.plugins.ZapHistoryConfigurator.enable_zap_history.value == "off":
		return
	if config.ParentalControl.servicepinactive.value and config.plugins.ZapHistoryConfigurator.enable_zap_history.value == "parental_lock":
		if parentalControl.getProtectionLevel(ref.toCompareString()) != -1:
			return
	if instance.servicePath is not None:
		tmp = instance.servicePath[:]
		tmp.append(ref)
		try: del instance.history[instance.history_pos+1:]
		except Exception, e: pass
		if config.plugins.ZapHistoryConfigurator.e1_like_history.value and tmp in instance.history:
			instance.history.remove(tmp)
		instance.history.append(tmp)
		hlen = len(instance.history)
		if hlen > config.plugins.ZapHistoryConfigurator.maxEntries_zap_history.value:
			del instance.history[0]
			hlen -= 1
		instance.history_pos = hlen-1
		if config.plugins.ZapHistoryConfigurator.e1_like_history.value:
			# TODO: optimize this
			if instance.history == instance.history_tv:
				config.plugins.ZapHistoryConfigurator.history_tv.value = [[y.toString() for y in x] for x in instance.history]
			else:
				config.plugins.ZapHistoryConfigurator.history_radio.value = [[y.toString() for y in x] for x in instance.history]
			config.plugins.ZapHistoryConfigurator.save()

ChannelSelection.addToHistory = addToHistory

def newInit(self, session):
	baseInit(self, session)
	if config.plugins.ZapHistoryConfigurator.e1_like_history.value:
		append = self.history_tv.append
		for x in config.plugins.ZapHistoryConfigurator.history_tv.value:
			append([eServiceReference(y) for y in x])
		append = self.history_radio.append
		for x in config.plugins.ZapHistoryConfigurator.history_radio.value:
			append([eServiceReference(y) for y in x])

		# XXX: self.lastChannelRootTimer was always finished for me, so just fix its mistakes ;)
		if self.history == self.history_tv:
			self.history_pos = len(self.history_tv)-1
		else:
			self.history_pos = len(self.history_radio)-1

baseInit = ChannelSelection.__init__
ChannelSelection.__init__ = newInit

################################################

class ZapHistoryConfigurator(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="420,80" title="%s" >
			<widget name="config" position="0,0" size="420,80" scrollbarMode="showOnDemand" />
		</screen>""" % _("Zap-History Configurator")

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		
		ConfigListScreen.__init__(self, [
			getConfigListEntry(_("Enable zap history:"), config.plugins.ZapHistoryConfigurator.enable_zap_history),
			getConfigListEntry(_("Maximum zap history entries:"), config.plugins.ZapHistoryConfigurator.maxEntries_zap_history),
			getConfigListEntry(_("Enigma1-like history:"), config.plugins.ZapHistoryConfigurator.e1_like_history)])
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.save, "cancel": self.exit}, -2)

	def save(self):
		# alternative to notifier
		if config.plugins.ZapHistoryConfigurator.e1_like_history.value and config.plugins.ZapHistoryConfigurator.e1_like_history.isChanged():
			from Screens.InfoBar import InfoBar
			try:
				csel = InfoBar.instance.servicelist
			except AttributeError, e:
				pass
			else:
				config.plugins.ZapHistoryConfigurator.history_tv.value = [[y.toString() for y in x] for x in csel.history_tv]
				config.plugins.ZapHistoryConfigurator.history_radio.value = [[y.toString() for y in x] for x in csel.history_radio]
				config.plugins.ZapHistoryConfigurator.history_tv.save()
				config.plugins.ZapHistoryConfigurator.history_radio.save()

		for x in self["config"].list:
			x[1].save()
		self.close()

	def exit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

################################################

class ZapHistoryBrowserList(MenuList):
	def __init__(self, list, enableWrapAround=False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setItemHeight(40)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))

def ZapHistoryBrowserListEntry(serviceName, eventName):
	res = [serviceName]
	res.append(MultiContentEntryText(pos=(0, 0), size=(560, 22), font=0, text=serviceName))
	res.append(MultiContentEntryText(pos=(0, 22), size=(560, 18), font=1, text=eventName))
	return res

################################################

class ZapHistoryBrowser(Screen, ProtectedScreen):
	skin = """
	<screen position="center,center" size="560,440" title="%s" >
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="list" position="0,40" size="560,400" scrollbarMode="showOnDemand" />
	</screen>""" % _("Zap-History Browser")

	def __init__(self, session, servicelist):
		Screen.__init__(self, session)
		ProtectedScreen.__init__(self)
		self.session = session
		
		self.servicelist = servicelist
		self.serviceHandler = eServiceCenter.getInstance()
		self.allowChanges = True
		
		self["list"] = ZapHistoryBrowserList([])
		self["key_red"] = Label(_("Clear"))
		self["key_green"] = Label(_("Delete"))
		self["key_yellow"] = Label(_("Zap"))
		self["key_blue"] = Label(_("Config"))
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"ok": self.zapAndClose,
				"cancel": self.close,
				"red": self.clear,
				"green": self.delete,
				"yellow": self.zap,
				"blue": self.config
			}, prio=-1)
		
		self.onLayoutFinish.append(self.buildList)

	def buildList(self):
		list = []
		for x in self.servicelist.history:
			if len(x) == 2: # Single-Bouquet
				ref = x[1]
			else: # Multi-Bouquet
				ref = x[2]
			info = self.serviceHandler.info(ref)
			if info:
				name = info.getName(ref).replace('\xc2\x86', '').replace('\xc2\x87', '')
				event = info.getEvent(ref)
				if event is not None:
					eventName = event.getEventName()
					if eventName is None:
						eventName = ""
				else:
					eventName = ""
			else:
				name = "N/A"
				eventName = ""
			list.append(ZapHistoryBrowserListEntry(name, eventName))
		list.reverse()
		self["list"].setList(list)

	def zap(self):
		length = len(self.servicelist.history)
		if length > 0:
			self.servicelist.history_pos = (length - self["list"].getSelectionIndex()) - 1
			self.servicelist.setHistoryPath()

	def clear(self):
		if self.allowChanges:
			for i in range(0, len(self.servicelist.history)):
				del self.servicelist.history[0]
			self.buildList()
			self.servicelist.history_pos = 0

	def delete(self):
		if self.allowChanges:
			length = len(self.servicelist.history)
			if length > 0:
				idx = (length - self["list"].getSelectionIndex()) - 1
				del self.servicelist.history[idx]
				self.buildList()
				currRef = self.session.nav.getCurrentlyPlayingServiceReference()
				idx = 0
				for x in self.servicelist.history:
					if len(x) == 2: # Single-Bouquet
						ref = x[1]
					else: # Multi-Bouquet
						ref = x[2]
					if ref == currRef:
						self.servicelist.history_pos = idx
						break
					else:
						idx += 1

	def zapAndClose(self):
		self.zap()
		self.close()

	def config(self):
		if self.allowChanges:
			self.session.open(ZapHistoryConfigurator)

	def isProtected(self):
		return config.ParentalControl.setuppinactive.value
	
	def pinEntered(self, result):
		if result is None:
			self.allowChanges = False
		elif not result:
			self.allowChanges = False
		else:
			self.allowChanges = True

################################################

def main(session, servicelist, **kwargs):
	session.open(ZapHistoryBrowser, servicelist)

def Plugins(**kwargs):
	return PluginDescriptor(name=_("Zap-History Browser"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
