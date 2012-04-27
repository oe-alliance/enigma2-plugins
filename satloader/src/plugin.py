from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.ActionMap import ActionMap
from Components.Label import Label
from twisted.web.client import downloadPage
from enigma import getDesktop
from Plugins.Plugin import PluginDescriptor

#######################

class Satloader(Screen):
	framewidth = getDesktop(0).size().width()
	if framewidth == 1280:
		skin = """
			<screen position="240,130" size="800,450" title="Satloader Plugin" >
				<ePixmap position="8,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_red_sm.png" alphatest="on" />
				<ePixmap position="206,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_green_sm.png" alphatest="on" />
				<ePixmap position="404,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_yellow_sm.png" alphatest="on" />
				<ePixmap position="602,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_blue_sm.png" alphatest="on" />
				<widget name="key_red" position="8,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" position="206,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_yellow" position="404,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_blue" position="602,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="config" position="10,40" size="780,360" scrollbarMode="showOnDemand" />
				<widget name="info" position="10,410" size="780,30" zPosition="10" font="Regular;22" valign="center" halign="center" />
			</screen>"""
	elif framewidth == 720:
		skin = """
			<screen position="center,center" size="560,440" title="Satloader Plugin" >
				<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
				<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="config" position="10,50" size="540,350" scrollbarMode="showOnDemand" />
				<widget name="info" position="10,410" size="540,30" zPosition="10" font="Regular;22" valign="center" halign="center" />
			</screen>"""

	def __init__(self, session, url=None, path=None):
		self.session = session

		Screen.__init__(self, session)
		self["config"] = MenuList(list)
		self["info"] = Label()
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label()
		self["key_yellow"] = Label(_("Satellites"))
		self["key_blue"] = Label(_("Transponder"))
		self["myActionMap"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.btnOK,
			"cancel": self.btnRed,
			"red": self.btnRed,
			"green": self.btnGreen,
			"yellow": self.btnYellow,
			"blue": self.btnBlue
		}, -1)

		self.onLayoutFinish.append(self.btnYellow)

	def btnOK(self):
		if self["key_green"].getText() == "OK":
			self.downloadList("sat")
		else:
			self.downloadList("tp")

	def btnRed(self):
		print "\n[Satloader] cancel\n"
		self.close(None)

	def btnGreen(self):
		if self["key_green"].getText() == "OK":
			self.downloadList("sat")
		else:
			self.buildSatellites()

	def btnYellow(self):
		list = []
		list.append((_("Kingofsat satellites.xml (no feed)"), "http://satellites.satloader.net/satellites.xml"))
		list.append((_("Kingofsat satellites.xml (with feed)"), "http://satellites.satloader.net/feeds.xml"))
		list.append((_("Satbeams satellites.xml"), "http://satellites.satloader.net/satbeam.xml"))

		self["key_green"].setText("OK")
		self["info"].setText("Press green or ok button to download satellites.xml")
		self["config"].setList(list)

	def btnBlue(self):
		self["info"].setText("Downloading feeds from server ...")
		self.downloadList("list")

	def downloadList(self, key):
		if key == "sat":
			downloadPage(self["config"].l.getCurrentSelection()[1], "/etc/tuxbox/satellites.xml").addCallback(self.downloadListSATCallback).addErrback(self.downloadListError)
		elif key == "tp":
			downloadPage(self["config"].l.getCurrentSelection()[1], "/tmp/tp_"+self["config"].l.getCurrentSelection()[0]+".xml").addCallback(self.downloadListBUILDCallback).addErrback(self.downloadListError)
		elif key == "list":
			downloadPage("http://satellites.satloader.net/transponder/transponder.lst", "/tmp/transponder.lst").addCallback(self.downloadListTPCallback).addErrback(self.downloadListError)

	def downloadListError(self, raw):
		self.session.open(MessageBox, text = _("Error downloading!"), type = MessageBox.TYPE_ERROR)
		self["info"].setText("Error downloading!")

	def downloadListSATCallback(self, raw):
		restart = self.session.openWithCallback(self.restart,MessageBox,_("satellites.xml is up-to-date")+_("\n\n")+_("GUI needs a restart to apply changes.")+_("\n")+_("Do you want to restart the GUI now?"), MessageBox.TYPE_YESNO)
		restart.setTitle(_("Restart GUI now?"))

	def downloadListTPCallback(self, raw):
		self["info"].setText("Parsing Feeds ...")

		try:
			list = []
			f = open('/tmp/transponder.lst', 'r')
			for line in f.readlines():
				m = line.split(";")
				list.append((_(m[0]), m[1]))
			f.close()
			
			if list is not None:
				self["key_green"].setText("Build")
				self["info"].setText("Press ok button to download selected transponders")
				self["config"].setList(list)
		except Exception, e:
			print "Error:", e
			self["info"].setText("Error:", e)

	def downloadListBUILDCallback(self, raw):
		self["info"].setText(self["config"].l.getCurrentSelection()[0] + " added.")

	def restart(self, ret):
		if ret is True:
			self.session.open(TryQuitMainloop, 3)

	def buildSatellites(self):
		self.session.open(MessageBox, text = _("coming soon ..."), type = MessageBox.TYPE_INFO)

#######################

def main(session, **kwargs):
	print "\n[Satloader] start\n"	
	session.open(Satloader)

#######################

def Plugins(**kwargs):
	return [
		PluginDescriptor(name="Satloader Plugin", description="update satellites.xml", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
		PluginDescriptor(name="Satloader Plugin", description="update satellites.xml", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
		]
