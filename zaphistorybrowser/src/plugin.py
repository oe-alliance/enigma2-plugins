# -*- coding: UTF-8 -*-
## Zap-History Browser by AliAbdul
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from enigma import eServiceCenter
from os import environ
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
import gettext

################################################

def localeInit():
	lang = language.getLanguage()
	environ["LANGUAGE"] = lang[:2]
	gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
	gettext.textdomain("enigma2")
	gettext.bindtextdomain("ZapHistoryBrowser", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/ZapHistoryBrowser/locale/"))

def _(txt):
	t = gettext.dgettext("ZapHistoryBrowser", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

################################################

class ZapHistoryBrowser(Screen):
	skin = """
	<screen position="200,80" size="320,440" title="%s" >
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="170,0" size="140,40" transparent="1" alphatest="on" />
		<widget name="key_red" position="10,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="key_green" position="170,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="list" position="0,40" size="320,400" scrollbarMode="showOnDemand" />
	</screen>""" % _("Zap-History Browser")

	def __init__(self, session, servicelist):
		Screen.__init__(self, session)
		self.session = session
		
		self.servicelist = servicelist
		self.serviceHandler = eServiceCenter.getInstance()
		
		self["list"] = MenuList([])
		self["key_red"] = Label(_("Clear"))
		self["key_green"] = Label(_("Delete"))
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"ok": self.zap,
				"cancel": self.close,
				"red": self.clear,
				"green": self.delete
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
			name = info.getName(ref).replace('\xc2\x86', '').replace('\xc2\x87', '')
			list.append(name)
		list.reverse()
		self["list"].setList(list)

	def zap(self):
		length = len(self.servicelist.history)
		if length > 0:
			self.servicelist.history_pos = (length - self["list"].getSelectionIndex()) - 1
			self.servicelist.setHistoryPath()

	def clear(self):
		for i in range(0, len(self.servicelist.history)):
			del self.servicelist.history[0]
		self.buildList()
		self.servicelist.history_pos = 0

	def delete(self):
		length = len(self.servicelist.history)
		if length > 0:
			idx = (length - self["list"].getSelectionIndex()) - 1
			del self.servicelist.history[idx]
			self.buildList()
			
			# We must check if the current service is still in the zap-history
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

################################################

def main(session, servicelist, **kwargs):
	session.open(ZapHistoryBrowser, servicelist)

def Plugins(**kwargs):
	return PluginDescriptor(name=_("Zap-History Browser"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
