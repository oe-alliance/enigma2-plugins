# -*- coding: utf-8 -*-
# for localized messages
from __init__ import _
from Screens.Screen import Screen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.Sources.List import List

from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from UserDialog import UserDialog
from os import unlink, listdir

class UserManager(Screen):
	skin = """
		<screen name="UserManager" position="90,140" size="560,350" title="UserManager">
			<widget source="config" render="Listbox" position="10,10" size="540,220" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template": [
							MultiContentEntryText(pos = (80, 5), size = (400, 50), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 0 is the name
							MultiContentEntryPixmapAlphaTest(pos = (0, 0), size = (48, 48), png = 3), # index 4 is the status pixmap
						],
					"fonts": [gFont("Regular", 40)],
					"itemHeight": 50
					}
				</convert>
			</widget>
			<widget name="introduction" position="50,270" size="500,20" zPosition="10" font="Regular;21" halign="center" transparent="1" />
			<widget name="ButtonRedtext" position="410,305" size="140,21" zPosition="10" font="Regular;21" transparent="1" />
			<widget name="ButtonRed" pixmap="skin_default/buttons/button_red.png" position="390,305" zPosition="10" size="15,16" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/button_yellow.png" position="30,305" zPosition="10" size="15,16" transparent="1" alphatest="on" />
			<widget name="deletetext" position="50,305" size="350,21" zPosition="10" font="Regular;21" transparent="1" />
			<ePixmap pixmap="skin_default/bottombar.png" position="10,250" size="540,120" zPosition="1" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session, plugin_path):
		self.skin_path = plugin_path
		self.session = session
		Screen.__init__(self, session)
		self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions"],
		{
			"ok": self.keyOK,
			"back": self.exit,
			"cancel": self.exit,
			"red": self.exit,
			"yellow": self.delete,
		})
		self["ButtonRed"] = Pixmap()
		self["ButtonRedtext"] = Label(_("Close"))
		self["introduction"] = Label(_("Press OK to edit selected settings."))
		self["deletetext"] = Label(_("Delete"))

		self.list = []
		self["config"] = List(self.list)
		self.updateList()
		self.onShown.append(self.setWindowTitle)

	def setWindowTitle(self):
		self.setTitle(_("Usermanager"))

	def updateList(self):
		self.list = []
		for file in listdir('/etc/enigma2'):
			if file.endswith('.cache'):
				if file == 'networkbrowser.cache':
					continue
				else:
					hostpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/host.png"))
					self.list.append(( file[:-6],'edit',file,hostpng ))
		self["config"].setList(self.list)

	def exit(self):
		self.close()

	def keyOK(self, returnValue = None):
		cur = self["config"].getCurrent()
		if cur:
			returnValue = cur[1]
			hostinfo = cur[0]
			if returnValue is "edit":
				self.session.open(UserDialog, self.skin_path,hostinfo)

	def delete(self, returnValue = None):
		cur = self["config"].getCurrent()
		if cur:
			returnValue = cur[2]
			cachefile = '/etc/enigma2/' + returnValue.strip()
			if os_path.exists(cachefile):
				unlink(cachefile)
				self.updateList()

