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
				<widget name="info" position="10,450" size="780,50" zPosition="1" font="Regular;22" valign="center" halign="center" />
				<ePixmap position="730,458" size="50,35" zPosition="2" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Satloader/key_info.png" alphatest="on" />
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
				<widget name="info" position="10,410" size="540,40" zPosition="1" font="Regular;20" valign="center" halign="center" />
				<ePixmap position="505,418" size="35,25" zPosition="2" pixmap="/usr/share/enigma2/skin_default/buttons/key_info.png" alphatest="on" />
			</screen>"""

	def __init__(self, session, url=None, path=None):
		self.session = session

		Screen.__init__(self, session)
		self.list = SatloaderList([])
		self["list"] = self.list
		self["info"] = Label()
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Install"))
		self["key_yellow"] = Label(_("Satellites"))
		self["key_blue"] = Label(_("Multi Sat"))
		self["myActionMap"] = ActionMap(["OkCancelActions", "ColorActions", "EPGSelectActions"],
		{
			"ok": self.btnOK,
			"cancel": self.btnRed,
			"red": self.btnRed,
			"green": self.btnGreen,
			"yellow": self.btnYellow,
			"blue": self.btnBlue,
			"info": self.btnInfo
		}, -1)

		self.onLayoutFinish.append(self.btnYellow)

	def btnRed(self):
		print "\n[Satloader] cancel\n"
		self.close(None)

	def btnOK(self):
		if self["list"].l.getCurrentSelection() is not None:
			if self["list"].l.getCurrentSelection()[0][3] == None:
				downloadPage(self["list"].l.getCurrentSelection()[0][1], "/etc/tuxbox/satellites.xml").addCallback(self.downloadListSATCallback).addErrback(self.downloadListError)
			else:
				self.list.toggleSelection()

	def btnGreen(self):
		if self["list"].l.getCurrentSelection() is not None:
			if self["list"].l.getCurrentSelection()[0][3] == None:
				downloadPage(self["list"].l.getCurrentSelection()[0][1], "/etc/tuxbox/satellites.xml").addCallback(self.downloadListSATCallback).addErrback(self.downloadListError)
			else:
				list = self.list.getSelectionsList()
				if len(list) is not 0:
					f = open('/etc/tuxbox/satellites.xml', 'w+')
					f.write('<?xml version="1.0" ?>\n<!--\nsatellites.xml generated by Satloader Plugin\n(c)2009-2012 Ismail Demir www.satloader.net\n-->\n\n<satellites>\n')
					for item in list:
						myfile = open('/tmp/transponder/'+item[1], 'r')
						f.write(myfile.read())
						myfile.close()
					f.write('</satellites>')
					f.close()
					
					restart = self.session.openWithCallback(self.restart,MessageBox,_("satellites.xml building finished!")+"\n\n"+_("GUI needs a restart to apply changes.")+"\n"+_("Do you want to restart the GUI now?"), MessageBox.TYPE_YESNO)
					restart.setTitle(_("Restart GUI now?"))
				else:
					self["info"].setText(_("Please select at least one satellite"))

	def btnYellow(self):
		self.list.clearList()
		self.list.addSelection("Kingofsat satellites.xml", "http://satellites.satloader.net/satellites.xml", 0, None)
		self.list.addSelection("Kingofsat satellites.xml (feed)", "http://satellites.satloader.net/feeds.xml", 1, None)
		self.list.addSelection("Satbeams satellites.xml", "http://satellites.satloader.net/satbeam.xml", 2, None)
		self["key_green"].setText(_("Install"))
		self["info"].setText(_("Press ok or green button to install satellites.xml"))

	def btnBlue(self):
		self["info"].setText(_("Downloading satellites from server ..."))
		downloadPage("http://satellites.satloader.net/transponder.tar.gz", "/tmp/transponder.tar.gz").addCallback(self.downloadListTPCallback).addErrback(self.downloadListError)

	def btnInfo(self):
		if self["list"].l.getCurrentSelection() is not None:
			if self["list"].l.getCurrentSelection()[0][3] is not None:
				name = self["list"].l.getCurrentSelection()[0][0]
				url = "/tmp/transponder/"+self["list"].l.getCurrentSelection()[0][1]
				self.session.open(SatloaderConfig, name, url)
			else:
				self.session.open(MessageBox, _("Only for Multi Sat"), MessageBox.TYPE_INFO)

	def downloadListError(self, ret):
		self.session.open(MessageBox, text = _("Downloading satellites failed!"), type = MessageBox.TYPE_ERROR)
		self["info"].setText(_("Downloading satellites failed!"))

	def downloadListSATCallback(self, ret):
		restart = self.session.openWithCallback(self.restart, MessageBox, _("satellites.xml is up-to-date")+"\n\n"+_("GUI needs a restart to apply changes.")+"\n"+_("Do you want to restart the GUI now?"), MessageBox.TYPE_YESNO)
		restart.setTitle(_("Restart GUI now?"))

	def downloadListTPCallback(self, ret):
		self["info"].setText(_("Downloading succesfull! Parsing ..."))

		try:
			if not os.path.exists('/tmp/transponder'):
				os.mkdir('/tmp/transponder', 644)

			os.system("tar -xzf /tmp/transponder.tar.gz -C/tmp/transponder")
			os.system("rm -f /tmp/transponder.tar.gz")
			self.list.clearList()
			idx = 0
			f = open("/tmp/transponder/transponder.lst", "r")
			for line in f.readlines():
				m = line.split(";")
				self.list.addSelection(m[0], m[1], idx, False)
				idx += 1
			f.close()

			if self.list is not None:
				self["info"].setText(_("Press ok button to select satellite"))

		except Exception, e:
			print "Error:", e
			self["info"].setText(_("Parsing failed!")+"\n"+str(e))

	def restart(self, ret):
		if ret is True:
			self.session.open(TryQuitMainloop, 3)


class SatloaderConfig(Screen):
	framewidth = getDesktop(0).size().width()
	if framewidth == 1280:
		skin = """
			<screen position="240,130" size="800,510" title="Satloader Config" >
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
			<screen position="center,center" size="560,460" title="Satloader Config" >
				<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
				<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="list" position="10,50" size="540,350" scrollbarMode="showOnDemand" />
				<widget name="info" position="10,410" size="540,40" zPosition="10" font="Regular;20" valign="center" halign="center" />
			</screen>"""

	def __init__(self, session, name, url):
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

		try:
			f = open(url, "r")
			self.list.clearList()
			idx = 0
			for line in f.readlines():
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
					
					text = "TP:" + " " + str(idx+1).zfill(3) + "   " + _("Frequency:") + " " + str(m[1]).zfill(8)[:5] + " " + pol + "   " + _("Symbol Rate:") + " " + str(m[3]).zfill(8)[:5]
					self.list.addSelection(text, url, idx, True)
					idx += 1
			f.close()

		except Exception, e:
			print "Error:", e
			self["info"].setText(_("Parsing failed!")+"\n"+str(e))

		self["info"].setText(name)

	def btnRed(self):
		print "\n[SatloaderConfig] cancel\n"
		self.close(None)

	def btnOK(self):
		if self["list"].l.getCurrentSelection() is not None:
			if self["list"].l.getCurrentSelection()[0][3] is not None:
				self.list.toggleSelection()

	def btnGreen(self):
		self.session.open(MessageBox, _("Not yet implemented"), MessageBox.TYPE_INFO)


class SatloaderList(MenuList):
	def __init__(self, list):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.l.setItemHeight(25)
		self.l.setFont(0, gFont("Regular", 22))

	def clearList(self):
		self.list = []
		self.setList(self.list)

	def addSelection(self, description, value, index, selected = False):
		self.list.append(SatListEntry(description, value, index, selected))
		self.setList(self.list)

	def toggleSelection(self):
		idx = self.getSelectedIndex()
		item = self.list[idx][0]
		self.list[idx] = SatListEntry(item[0], item[1], item[2], not item[3])
		self.setList(self.list)

	def getSelectionsList(self):
		return [ (item[0][0], item[0][1], item[0][2]) for item in self.list if item[0][3] ]


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
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 0, 25, 24,  LoadPixmap(cached=True, path="/usr/share/enigma2/skin_default/icons/lock_on.png")))
		elif selected == False:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 0, 25, 24,  LoadPixmap(cached=True, path="/usr/share/enigma2/skin_default/icons/lock_off.png")))
		return res


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
