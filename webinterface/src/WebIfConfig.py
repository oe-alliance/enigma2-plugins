from __future__ import print_function
from __future__ import absolute_import
Version = '$Header$'

from .__init__ import *

from enigma import eListboxPythonMultiContent, gFont
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText, ConfigSelection
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText

from Components.ActionMap import ActionMap

class WebIfConfigScreen(ConfigListScreen, Screen):
	skin = """
		<screen name="WebIfConfigScreen" position="center,center" size="560,400" title="Webinterface: Main Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="5,50" size="550,360" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>"""

	def __init__(self, session, args=0):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [])
		self.createSetup()

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		# SKIN Compat HACK!
		self["key_yellow"] = StaticText("")
		# EO SKIN Compat HACK!
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()

	def createSetup(self):
		list = [ getConfigListEntry(_("Start Webinterface"), config.plugins.Webinterface.enabled), ]

		if config.plugins.Webinterface.enabled.value:
			list.extend( [
				getConfigListEntry(_("Show Setup in Extensions menu"), config.plugins.Webinterface.show_in_extensionsmenu),
				getConfigListEntry(_("Enable /media"), config.plugins.Webinterface.includemedia),
				getConfigListEntry(_("Allow zapping via Webinterface"), config.plugins.Webinterface.allowzapping),
				getConfigListEntry(_("Autowrite timer"), config.plugins.Webinterface.autowritetimer),
				getConfigListEntry(_("Load movie-length"), config.plugins.Webinterface.loadmovielength),
				getConfigListEntry(_("Enable HTTP Access"), config.plugins.Webinterface.http.enabled)
			])

			if config.plugins.Webinterface.http.enabled.value == True:
				list.extend([
					getConfigListEntry(_("HTTP Port"), config.plugins.Webinterface.http.port),
					getConfigListEntry(_("Enable HTTP Authentication"), config.plugins.Webinterface.http.auth)
				])

			list.append( getConfigListEntry(_("Enable HTTPS Access"), config.plugins.Webinterface.https.enabled) )
			if config.plugins.Webinterface.https.enabled.value == True:
				list.extend([
					getConfigListEntry(_("HTTPS Port"), config.plugins.Webinterface.https.port),
					getConfigListEntry(_("Enable HTTPS Authentication"), config.plugins.Webinterface.https.auth)
				])

			#Auth for Streaming (127.0.0.1 Listener)
			list.append(getConfigListEntry(_("Enable Streaming Authentication"), config.plugins.Webinterface.streamauth))
			list.append(getConfigListEntry(_("Simple Anti-Hijack Measures (may break clients)"), config.plugins.Webinterface.anti_hijack))
			list.append(getConfigListEntry(_("Token-based security (may break clients)"), config.plugins.Webinterface.extended_security))
		self["config"].list = list
		self["config"].l.setList(list)

	def layoutFinished(self):
		self.setTitle(_("Webinterface: Main Setup"))

	def save(self):
		print("[Webinterface] Saving Configuration")
		for x in self["config"].list:
			x[1].save()
		self.close(True, self.session)

	def cancel(self):
		print("[Webinterface] Cancel setup changes")
		for x in self["config"].list:
			x[1].cancel()
		self.close(False, self.session)


