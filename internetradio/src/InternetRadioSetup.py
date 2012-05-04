#
# InternetRadio E2
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

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.config import config, getConfigListEntry, configfile
from Components.FileList import FileList
from Components.Sources.StaticText import StaticText

class InternetRadioSetup(Screen, ConfigListScreen):

	skin = """
		<screen name="InternetRadioSetup" position="center,center" size="600,400" title="InternetRadio Setup" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="300,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="445,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="10,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="150,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="10,50" size="580,400" scrollbarMode="showOnDemand" />
		</screen>""" 

	def __init__(self, session):
		Screen.__init__(self, session)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self.list = [
			getConfigListEntry(_("Show in extension menu:"), config.plugins.internetradio.showinextensions),
			getConfigListEntry(_("Visualization"), config.plugins.internetradio.visualization),
			getConfigListEntry(_("Fullscreen Layout"), config.plugins.internetradio.fullscreenlayout),
			getConfigListEntry(_("Fullscreen auto activation"), config.plugins.internetradio.fullscreenautoactivation),
			getConfigListEntry(_("Show cover arts"), config.plugins.internetradio.googlecover),
			getConfigListEntry(_("Rip to single file, name is timestamped"), config.plugins.internetradio.riptosinglefile),
			getConfigListEntry(_("Create a directory for each stream"), config.plugins.internetradio.createdirforeachstream),
			getConfigListEntry(_("Add sequence number to output file"), config.plugins.internetradio.addsequenceoutputfile),
			]
		self.dirname = getConfigListEntry(_("Recording location:"), config.plugins.internetradio.dirname)
		self.list.append(self.dirname)
		
		ConfigListScreen.__init__(self, self.list, session)
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyClose,
			"ok": self.keySelect,
		}, -2)

	def keySelect(self):
		cur = self["config"].getCurrent()
		if cur == self.dirname:
			self.session.openWithCallback(self.pathSelected,InternetRadioStreamripperRecordingPath,config.plugins.internetradio.dirname.value)

	def pathSelected(self, res):
		if res is not None:
			config.plugins.internetradio.dirname.value = res

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		self.close(True)

	def keyClose(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close(False)
		
		
class InternetRadioStreamripperRecordingPath(Screen):
	skin = """<screen name="InternetRadioStreamripperRecordingPath" position="center,center" size="560,320" title="Select record path for streamripper">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget name="target" position="0,60" size="540,22" valign="center" font="Regular;22" />
			<widget name="filelist" position="0,100" zPosition="1" size="560,220" scrollbarMode="showOnDemand"/>
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""
		
	def __init__(self, session, initDir):
		Screen.__init__(self, session)
		inhibitDirs = ["/bin", "/boot", "/dev", "/etc", "/lib", "/proc", "/sbin", "/sys", "/usr", "/var"]
		inhibitMounts = []
		self["filelist"] = FileList(initDir, showDirectories = True, showFiles = False, inhibitMounts = inhibitMounts, inhibitDirs = inhibitDirs)
		self["target"] = Label()
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions"],
		{
			"back": self.cancel,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
			"ok": self.ok,
			"green": self.green,
			"red": self.cancel
			
		}, -1)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

	def cancel(self):
		self.close(None)

	def green(self):
		self.close(self["filelist"].getSelection()[0])

	def up(self):
		self["filelist"].up()
		self.updateTarget()

	def down(self):
		self["filelist"].down()
		self.updateTarget()

	def left(self):
		self["filelist"].pageUp()
		self.updateTarget()

	def right(self):
		self["filelist"].pageDown()
		self.updateTarget()

	def ok(self):
		if self["filelist"].canDescent():
			self["filelist"].descent()
			self.updateTarget()

	def updateTarget(self):
		currFolder = self["filelist"].getSelection()[0]
		if currFolder is not None:
			self["target"].setText(currFolder)
		else:
			self["target"].setText(_("Invalid Location"))
