from __init__ import _
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from twisted.web.client import downloadPage
from enigma import getDesktop, eListbox, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT
from Tools.LoadPixmap import LoadPixmap
from Plugins.Plugin import PluginDescriptor
import os

#######################


class Satloader(Screen):
	framewidth = getDesktop(0).size().width()
	if framewidth == 1280:
		skin = """
			<screen position="240,130" size="800,510" title="Satloader Plugin" >
				<ePixmap position="8,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_red_sm.png" alphatest="on" />
				<ePixmap position="206,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_green_sm.png" alphatest="on" />
				<ePixmap position="404,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_yellow_sm.png" alphatest="on" />
				<ePixmap position="602,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_blue_sm.png" alphatest="on" />
				<widget name="key_red" position="8,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" position="206,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_yellow" position="404,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_blue" position="602,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="list" position="10,40" size="780,400" scrollbarMode="showOnDemand" />
				<widget name="info" position="10,450" size="710,50" zPosition="1" font="Regular;22" valign="center" halign="center" />
				<ePixmap position="730,457" size="50,35" zPosition="2" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/key_info.png" alphatest="on" />
			</screen>"""
	elif framewidth == 720:
		skin = """
			<screen position="center,center" size="560,460" title="Satloader Plugin" >
				<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
				<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="list" position="10,50" size="540,350" scrollbarMode="showOnDemand" />
				<widget name="info" position="10,410" size="485,40" zPosition="1" font="Regular;20" valign="center" halign="center" />
				<ePixmap position="505,418" size="35,25" zPosition="2" pixmap="/usr/share/enigma2/skin_default/buttons/key_info.png" alphatest="on" />
			</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.list = SatloaderList([])
		self["list"] = self.list
		self["info"] = Label()
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Install"))
		self["key_yellow"] = Label(_("Bouquet"))
		self["key_blue"] = Label(_("Multi Sat"))
		self["myActionMap"] = ActionMap(["OkCancelActions", "ColorActions", "EPGSelectActions"],
		{
			"ok": self.btnOK,
			"cancel": self.btnRed,
			"red": self.btnRed,
			"green": self.btnOK,
			"yellow": self.btnYellow,
			"blue": self.btnBlue,
			"info": self.btnInfo
		}, -1)

		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self.list.clearList()
		self.list.addSelection("Lyngsat", "http://satellites.satloader.net/lyngsat", 0, None)
		self.list.addSelection("Satbeams", "http://satellites.satloader.net/satbeams", 1, None)
		self.list.addSelection("Kingofsat", "http://satellites.satloader.net/kingofsat", 2, None)
		self.list.addSelection("Kingofsat (feeds)", "http://satellites.satloader.net/kingofsat/feeds", 3, None)
		self["info"].setText("%s" % (_("Press ok or green button to install satellites.xml")))

	def btnRed(self):
		print "\n[Satloader] cancel\n"
		self.close(None)

	def btnOK(self):
		self["info"].setText("%s" % (_("Please wait...")))
		saturl = self["list"].l.getCurrentSelection()[0][1] + "/satellites.xml"
		downloadPage(saturl, "/etc/tuxbox/satellites.xml").addCallback(self.downloadListSATCallback).addErrback(self.downloadListError)

	def btnYellow(self):
		self.session.open(SatloaderBouquet)

	def btnBlue(self):
		satname = self["list"].l.getCurrentSelection()[0][0]
		saturl = self["list"].l.getCurrentSelection()[0][1] + "/multisat.tar.gz"
		self.session.open(SatloaderMultiSat, satname, saturl)

	def btnInfo(self):
		self.session.open(SatloaderAbout)

	def downloadListError(self, ret):
		self["info"].setText("%s" % (_("Downloading satellites failed!")))
		self.session.open(MessageBox, "%s" % (_("Downloading satellites failed!")), MessageBox.TYPE_ERROR)

	def downloadListSATCallback(self, ret):
		restart = self.session.openWithCallback(self.restart, MessageBox, "%s\n%s\n\n%s\n%s" % (_("satellites.xml is updated"), str(self["list"].l.getCurrentSelection()[0][0]), _("GUI needs a restart to apply changes."), _("Do you want to restart the GUI now?")), MessageBox.TYPE_YESNO)
		restart.setTitle("%s" % (_("Restart GUI now?")))

	def restart(self, ret):
		if ret is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self["info"].setText("%s" % (_("GUI needs a restart.")))

#######################


class SatloaderAbout(Screen):
	skin = """
		<screen position="center,center" size="360,280" title="%s">
			<ePixmap position="120,40" size="100,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/satloader.png" alphatest="on" />
			<widget name="info" position="10,100" size="340,120" zPosition="10" font="Regular;22" valign="center" halign="center" />
		</screen>""" % (_("About"))

	def __init__(self, session):
		Screen.__init__(self, session)
		self["info"] = Label("Satloader Plugin\nAuthor: Ismail Demir\nwww.satloader.net")
		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"ok": self.close,
			"cancel": self.close
		}, -1)

#######################


class SatloaderBouquet(Screen):
	framewidth = getDesktop(0).size().width()
	if framewidth == 1280:
		skin = """
			<screen position="240,130" size="800,510" title="Satloader Bouquet">
				<ePixmap position="8,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_red_sm.png" alphatest="on" />
				<ePixmap position="206,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_green_sm.png" alphatest="on" />
				<ePixmap position="404,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_yellow_sm.png" alphatest="on" />
				<ePixmap position="602,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_blue_sm.png" alphatest="on" />
				<widget name="key_red" position="8,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" position="206,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="list" position="10,40" size="780,400" scrollbarMode="showOnDemand" />
				<widget name="info" position="10,450" size="780,50" zPosition="10" font="Regular;22" valign="center" halign="center" />
			</screen>"""
	elif framewidth == 720:
		skin = """
			<screen position="center,center" size="560,460" title="Satloader Bouquet">
				<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
				<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="list" position="10,50" size="540,350" scrollbarMode="showOnDemand" />
				<widget name="info" position="10,410" size="540,40" zPosition="10" font="Regular;20" valign="center" halign="center" />
			</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.list = SatloaderList([])
		self["list"] = self.list
		self["info"] = Label()
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Save"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.btnOK,
			"cancel": self.btnRed,
			"red": self.btnRed,
			"green": self.btnGreen
		}, -1)

		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self["info"].setText("%s" % (_("Please wait...")))
		downloadPage("http://satellites.satloader.net/bouquet.tar.gz", "/tmp/bouquet.tar.gz").addCallback(self.downloadListBouquetCallback).addErrback(self.downloadListError)

	def btnRed(self):
		print "\n[SatloaderBouquet] cancel\n"
		self.close(None)

	def btnOK(self):
		if self["list"].l.getCurrentSelection() is not None:
			self.list.toggleSelection()

	def btnGreen(self):
		if self["list"].l.getCurrentSelection() is not None:
			list = self.list.getSelectionsList()
			if len(list) is not 0:
				for item in list:
					if "\"" + item[1] + "\"" not in open("/etc/enigma2/bouquets.tv").read():
						os.system("cp /tmp/bouquet/" + item[1] + " /etc/enigma2/" + item[1])
						f = open("/etc/enigma2/bouquets.tv", 'a')
						f.write("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"" + item[1] + "\" ORDER BY bouquet\n")
						f.flush()
						os.fsync(f.fileno())
						f.close()

				restart = self.session.openWithCallback(self.restart, MessageBox, "%s\n\n%s\n%s" % (_("selected bouquets are installed"), _("GUI needs a restart to apply changes."), _("Do you want to restart the GUI now?")), MessageBox.TYPE_YESNO)
				restart.setTitle("%s" % (_("Restart GUI now?")))

			else:
				self["info"].setText("%s" % (_("Please select at least one bouquet")))

	def downloadListError(self, ret):
		self["info"].setText("%s" % (_("Downloading bouquets failed!")))
		self.session.open(MessageBox, "%s" % (_("Downloading bouquets failed!")), MessageBox.TYPE_ERROR)

	def downloadListBouquetCallback(self, ret):
		self["info"].setText("%s" % (_("Downloading succesfull! Parsing ...")))

		try:
			if os.path.exists('/tmp/bouquet'):
				os.system("rm -rf /tmp/bouquet")
			os.mkdir('/tmp/bouquet', 644)
			os.system("tar -xzf /tmp/bouquet.tar.gz -C/tmp/bouquet")
			os.system("rm -f /tmp/bouquet.tar.gz")

			idx = 0
			self.list.clearList()
			f = open("/tmp/bouquet/list.lst", "r")
			for line in f:
				m = line.split(";")
				self.list.addSelection(m[0], m[1], idx, False)
				idx += 1
			f.close()

			if self.list is not None:
				self["info"].setText("%s" % (_("Press ok button to select bouquet")))

		except Exception, e:
			print "Error:", e
			self["info"].setText("%s\n%s" % (_("Parsing failed!"), e))

	def restart(self, ret):
		if ret is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self["info"].setText("%s" % (_("GUI needs a restart.")))

#######################


class SatloaderMultiSat(Screen):
	framewidth = getDesktop(0).size().width()
	if framewidth == 1280:
		skin = """
			<screen position="240,130" size="800,510" title="Satloader MultiSat">
				<ePixmap position="8,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_red_sm.png" alphatest="on" />
				<ePixmap position="206,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_green_sm.png" alphatest="on" />
				<ePixmap position="404,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_yellow_sm.png" alphatest="on" />
				<ePixmap position="602,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_blue_sm.png" alphatest="on" />
				<widget name="key_red" position="8,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" position="206,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_yellow" position="404,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="list" position="10,40" size="780,400" scrollbarMode="showOnDemand" />
				<widget name="info" position="10,450" size="780,25" zPosition="10" font="Regular;22" valign="center" halign="center" />
				<widget name="desc" position="10,475" size="780,25" zPosition="10" font="Regular;22" valign="center" halign="center" />
			</screen>"""
	elif framewidth == 720:
		skin = """
			<screen position="center,center" size="560,460" title="Satloader MultiSat">
				<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
				<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="list" position="10,50" size="540,350" scrollbarMode="showOnDemand" />
				<widget name="info" position="10,410" size="540,20" zPosition="10" font="Regular;20" valign="center" halign="center" />
				<widget name="desc" position="10,430" size="540,20" zPosition="10" font="Regular;20" valign="center" halign="center" />
			</screen>"""

	def __init__(self, session, satname=None, saturl=None):
		Screen.__init__(self, session)
		self.satname = satname
		self.saturl = saturl
		self.list = SatloaderList([])
		self["list"] = self.list
		self["info"] = Label()
		self["desc"] = Label("%s %s" % (_("Source:"), self.satname))
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("OK"))
		self["key_yellow"] = Label(_("Transponder"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.btnOK,
			"cancel": self.btnRed,
			"red": self.btnRed,
			"green": self.btnGreen,
			"yellow": self.btnYellow
		}, -1)

		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self["info"].setText("%s %s" % (_("Download:"), self.satname))
		downloadPage(self.saturl, "/tmp/multisat.tar.gz").addCallback(self.downloadListMultiSatCallback).addErrback(self.downloadListError)

	def btnRed(self):
		print "\n[SatloaderMultiSat] cancel\n"
		self.close(None)

	def btnOK(self):
		if self["list"].l.getCurrentSelection() is not None:
			self.list.toggleSelection()

	def btnGreen(self):
		if self["list"].l.getCurrentSelection() is not None:
			list = self.list.getSelectionsList()
			if len(list) is not 0:
				f = open('/etc/tuxbox/satellites.xml', 'w+')
				f.write('<?xml version="1.0" ?>\n<!--\nsatellites.xml generated by Satloader Plugin\n(c)2009-2012 Ismail Demir www.satloader.net\n-->\n\n<satellites>\n')
				for item in list:
					myfile = open(item[1], 'r')
					f.write(myfile.read())
					myfile.close()
				f.write('</satellites>')
				f.flush()
				os.fsync(f.fileno())
				f.close()
				
				restart = self.session.openWithCallback(self.restart, MessageBox, "%s\n%s\n\n%s\n%s" % (_("satellites.xml has been built."), str(self.satname), _("GUI needs a restart to apply changes."), _("Do you want to restart the GUI now?")), MessageBox.TYPE_YESNO)
				restart.setTitle("%s" % (_("Restart GUI now?")))
			else:
				self["info"].setText("%s" % (_("Please select at least one satellite")))

	def btnYellow(self):
		if self["list"].l.getCurrentSelection() is not None:
			satname = self["list"].l.getCurrentSelection()[0][0]
			satfile = self["list"].l.getCurrentSelection()[0][1]
			self.session.open(TransponderSelection, satname, satfile)

	def downloadListError(self, ret):
		self["info"].setText("%s" % (_("Downloading satellites failed!")))
		self.session.open(MessageBox, "%s" % (_("Downloading satellites failed!")), MessageBox.TYPE_ERROR)

	def downloadListMultiSatCallback(self, ret):
		self["info"].setText("%s" % (_("Downloading succesfull! Parsing ...")))

		try:
			if os.path.exists('/tmp/multisat'):
				os.system("rm -rf /tmp/multisat")
			os.mkdir('/tmp/multisat', 644)
			os.system("tar -xzf /tmp/multisat.tar.gz -C/tmp/multisat")
			os.system("rm -f /tmp/multisat.tar.gz")

			idx = 0
			self.list.clearList()
			f = open("/tmp/multisat/satlist.lst", "r")
			for line in f:
				m = line.split(";")
				self.list.addSelection(m[0], "/tmp/multisat/" + m[1], idx, False)
				idx += 1
			f.close()

			if self.list is not None:
				self["info"].setText("%s" % (_("Press ok button to select satellite")))

		except Exception, e:
			print "Error:", e
			self["info"].setText("%s\n%s" % (_("Parsing failed!"), e))

	def restart(self, ret):
		if ret is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self["info"].setText("%s" % (_("GUI needs a restart.")))

#######################


class TransponderSelection(Screen):
	framewidth = getDesktop(0).size().width()
	if framewidth == 1280:
		skin = """
			<screen position="240,130" size="800,510" title="%s">
				<ePixmap position="8,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_red_sm.png" alphatest="on" />
				<ePixmap position="206,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_green_sm.png" alphatest="on" />
				<ePixmap position="404,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_yellow_sm.png" alphatest="on" />
				<ePixmap position="602,4" size="190,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/button_blue_sm.png" alphatest="on" />
				<widget name="key_red" position="8,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" position="206,4" size="190,32" valign="center" halign="center" zPosition="1" font="Regular;22" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="list" position="10,40" size="780,400" scrollbarMode="showOnDemand" />
				<widget name="info" position="10,450" size="780,50" zPosition="10" font="Regular;22" valign="center" halign="center" />
			</screen>""" % (_("Transponder selection"))
	elif framewidth == 720:
		skin = """
			<screen position="center,center" size="560,460" title="%s">
				<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
				<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="list" position="10,50" size="540,350" scrollbarMode="showOnDemand" />
				<widget name="info" position="10,410" size="540,40" zPosition="10" font="Regular;20" valign="center" halign="center" />
			</screen>""" % (_("Transponder selection"))

	def __init__(self, session, satname, satfile):
		Screen.__init__(self, session)
		self.satname = satname
		self.satfile = satfile
		self.list = SatloaderList([])
		self["list"] = self.list
		self["info"] = Label()
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Save"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.btnOK,
			"cancel": self.btnRed,
			"red": self.btnRed,
			"green": self.btnGreen
		}, -1)

		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self.list.clearList()
		f = open(self.satfile, "r")
		self.satheader = f.readline()
		idx = 0
		for line in f:
			if "transponder" in line:
				m = line.split("\"")
				pol = ""
				if m[5] == "0":
					pol = "H"
				elif m[5] == "1":
					pol = "V"
				elif m[5] == "2":
					pol = "L"
				elif m[5] == "3":
					pol = "R"

				text = "TP: %s   %s %s %s   %s %s" % (str(idx + 1).zfill(3), _("Frequency:"), str(m[1]).zfill(8)[:5], str(pol), _("Symbol Rate:"), str(m[3]).zfill(8)[:5])
				self.list.addSelection(text, line, idx, True)
				idx += 1
		f.close()
		self["info"].setText("%s" % (self.satname))

	def btnRed(self):
		print "\n[TransponderSelection] cancel\n"
		self.close(None)

	def btnOK(self):
		if self["list"].l.getCurrentSelection() is not None:
			self.list.toggleSelection()

	def btnGreen(self):
		list = self.list.getSelectionsList()
		if len(list) is not 0:
			f = open(self.satfile, 'w+')
			f.write(self.satheader)
			for item in list:
				f.write(item[1])
			f.write("\t</sat>\n")
			f.flush()
			os.fsync(f.fileno())
			f.close()
			
			self.session.open(MessageBox, "\"%s\" %s" % (str(self.satfile), _("has been saved.")), MessageBox.TYPE_INFO, timeout=3)
			self.close(None)
		else:
			self["info"].setText("%s" % (_("Please select at least one transponder")))

#######################


class SatloaderList(MenuList):
	def __init__(self, list):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.l.setItemHeight(25)
		self.l.setFont(0, gFont("Regular", 22))

	def clearList(self):
		self.list = []
		self.setList(self.list)

	def addSelection(self, description, value, index, selected=False):
		self.list.append(SatListEntry(description, value, index, selected))
		self.setList(self.list)

	def toggleSelection(self):
		idx = self.getSelectedIndex()
		item = self.list[idx][0]
		self.list[idx] = SatListEntry(item[0], item[1], item[2], not item[3])
		self.setList(self.list)

	def getSelectionsList(self):
		return [(item[0][0], item[0][1], item[0][2]) for item in self.list if item[0][3]]

#######################


def SatListEntry(description, value, index, selected):
	if selected == None:
		res = [
			(description, value, index, selected),
			(eListboxPythonMultiContent.TYPE_TEXT, 10, 0, 760, 25, 0, RT_HALIGN_LEFT, description)
		]
		return res
	else:
		res = [
			(description, value, index, selected),
			(eListboxPythonMultiContent.TYPE_TEXT, 40, 0, 730, 25, 0, RT_HALIGN_LEFT, description)
		]
		if selected == True:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 0, 25, 24, LoadPixmap(cached=True, path="/usr/share/enigma2/skin_default/icons/lock_on.png")))
		elif selected == False:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 0, 25, 24, LoadPixmap(cached=True, path="/usr/share/enigma2/skin_default/icons/lock_off.png")))
		return res

#######################


def main(session, **kwargs):
	print "\n[Satloader] start\n"
	session.open(Satloader)

#######################


def Plugins(**kwargs):
	return [
		PluginDescriptor(name="Satloader Plugin", description="updates satellites.xml", icon="satloader.png", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
		PluginDescriptor(name="Satloader Plugin", description="updates satellites.xml", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
		]
