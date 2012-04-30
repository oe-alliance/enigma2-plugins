from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.ActionMap import ActionMap
from Components.Label import Label
from twisted.web.client import downloadPage
from enigma import getDesktop, eListbox, eListboxPythonMultiContent, gFont, RT_VALIGN_CENTER
from Tools.LoadPixmap import LoadPixmap
from Plugins.Plugin import PluginDescriptor
import os

#######################

class Satloader(Screen):
	framewidth = getDesktop(0).size().width()
	if framewidth == 1280:
		skin = """
			<screen position="240,130" size="800,500" title="Satloader Plugin" >
				<ePixmap position="8,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_red_sm.png" alphatest="on" />
				<ePixmap position="206,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_green_sm.png" alphatest="on" />
				<ePixmap position="404,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_yellow_sm.png" alphatest="on" />
				<ePixmap position="602,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_blue_sm.png" alphatest="on" />
				<widget name="key_red" position="8,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" position="206,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_yellow" position="404,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_blue" position="602,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="config" position="10,40" size="780,400" scrollbarMode="showOnDemand" />
				<widget name="info" position="10,450" size="780,40" zPosition="10" font="Regular;22" valign="center" halign="center" />
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
		self["config"] = SatloaderList(list)
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
		png="/usr/share/enigma2/skin_default/icons/lock_off.png"
		list = []
		list.append((self, MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(35, 25), png=LoadPixmap(png)), MultiContentEntryText(pos=(40, 3), size=(750, 25), font=0, flags=RT_VALIGN_CENTER, text="Kingofsat satellites.xml"), "http://satellites.satloader.net/satellites.xml"))
		list.append((self, MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(35, 25), png=LoadPixmap(png)), MultiContentEntryText(pos=(40, 3), size=(750, 25), font=0, flags=RT_VALIGN_CENTER, text="Kingofsat satellites.xml (feed)"), "http://satellites.satloader.net/feeds.xml"))
		list.append((self, MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(35, 25), png=LoadPixmap(png)), MultiContentEntryText(pos=(40, 3), size=(750, 25), font=0, flags=RT_VALIGN_CENTER, text="Satbeams satellites.xml"), "http://satellites.satloader.net/satbeam.xml"))

		self["key_green"].setText("OK")
		self["info"].setText("Press green or ok button to download satellites.xml")
		self["config"].setList(list)

	def btnBlue(self):
		self["info"].setText("Downloading feeds from server ...")
		self.downloadList("entry")

	def downloadList(self, key):
		if key == "entry":
			downloadPage("http://satellites.satloader.net/transponder/transponder.lst", "/tmp/transponder.lst").addCallback(self.downloadListEntryCallback).addErrback(self.downloadListError)
		elif key == "sat":
			downloadPage(self["config"].l.getCurrentSelection()[3], "/etc/tuxbox/satellites.xml").addCallback(self.downloadListSATCallback).addErrback(self.downloadListError)
		elif key == "tp":
	  		if not os.path.exists("/tmp/transponder"):
				os.mkdir("/tmp/transponder")

			satname=self["config"].l.getCurrentSelection()[3].split("/")
			downloadPage(self["config"].l.getCurrentSelection()[3], "/tmp/transponder/"+satname[4]).addCallback(self.downloadListTPCallback).addErrback(self.downloadListError)

	def downloadListError(self, ret):
		self.session.open(MessageBox, text = _("Error downloading!"), type = MessageBox.TYPE_ERROR)
		self["info"].setText("Error downloading!")

	def downloadListEntryCallback(self, ret):
		png = "/usr/share/enigma2/skin_default/icons/lock_off.png"
		self["info"].setText("Parsing Feeds ...")

		try:
			list = []
			f = open('/tmp/transponder.lst', 'r')
			for line in f.readlines():
				m = line.split(";")
				list.append((self, MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(35, 25), png=LoadPixmap(png)), MultiContentEntryText(pos=(40, 3), size=(750, 25), font=0, flags=RT_VALIGN_CENTER, text=m[0]), m[1]))
			f.close()

			if list is not None:
				self["key_green"].setText("Build")
				self["info"].setText("Press ok button to download selected transponders")
				self["config"].setList(list)
		except Exception, e:
			print "Error:", e
			self["info"].setText("Error:", e)

	def downloadListSATCallback(self, ret):
		restart = self.session.openWithCallback(self.restart,MessageBox,_("satellites.xml is up-to-date")+"\n\n"+_("GUI needs a restart to apply changes.")+"\n"+_("Do you want to restart the GUI now?"), MessageBox.TYPE_YESNO)
		restart.setTitle(_("Restart GUI now?"))

	def downloadListTPCallback(self, ret):
		self["info"].setText(self["config"].l.getCurrentSelection()[2][7]+" added.")

	def buildSatellites(self):
		f = open('/etc/tuxbox/satellites.xml', 'w+')
		f.write('<?xml version="1.0" ?>\n<!--\nsatellites.xml generated by Satloader Plugin\n(c)2009-2012 Ismail Demir www.satloader.net\n-->\n\n<satellites>\n')
		
		for fname in os.listdir("/tmp/transponder"):
			f.write(open("/tmp/transponder/"+fname,"rb").read())
			os.remove("/tmp/transponder/"+fname)

		f.write('</satellites>')
		f.close()
		
		restart = self.session.openWithCallback(self.restart,MessageBox,_("satellites.xml building finished!")+"\n\n"+_("GUI needs a restart to apply changes.")+"\n"+_("Do you want to restart the GUI now?"), MessageBox.TYPE_YESNO)
		restart.setTitle(_("Restart GUI now?"))

	def restart(self, ret):
		if ret is True:
			self.session.open(TryQuitMainloop, 3)

class SatloaderList(MenuList):
	def __init__(self, list):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.l.setItemHeight(25)
		self.l.setFont(0, gFont("Regular", 22))

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
