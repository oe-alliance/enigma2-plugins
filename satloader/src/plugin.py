from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from twisted.web.client import downloadPage
from enigma import getDesktop
from Plugins.Plugin import PluginDescriptor

###########################################################################

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
				<widget name="config" position="10,40" size="780,360" scrollbarMode="showOnDemand" />
				<widget name="introduction" position="10,410" size="780,30" zPosition="10" font="Regular;22" valign="center" halign="center" />
			</screen>"""
	elif framewidth == 720:
		skin = """
			<screen position="center,center" size="560,440" title="Satloader Plugin" >
				<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
				<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
				<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="config" position="10,50" size="540,350" scrollbarMode="showOnDemand" />
				<widget name="introduction" position="10,410" size="540,30" zPosition="10" font="Regular;22" valign="center" halign="center" />
			</screen>"""

	
	def __init__(self, session, url = None, path = None):
		self.session = session
		
		list = []
		list.append((_("Kingofsat satellites.xml (no feed)"), "http://satellites.satloader.net/satellites.xml"))
		list.append((_("Kingofsat satellites.xml (with feed)"), "http://satellites.satloader.net/feeds.xml"))
		list.append((_("Satbeams satellites.xml"), "http://satellites.satloader.net/satbeam.xml"))

		Screen.__init__(self, session)
		self["config"] = MenuList(list)
		self["introduction"] = Label(_("Press green or ok button to download satellites.xml"))
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("OK"))
		self["myActionMap"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.start,
			"cancel": self.cancel,
			"red": self.cancel,
			"green": self.start,
		}, -1)

	def start(self):
		getSatfromUrl(self.session, self["config"].l.getCurrentSelection()[1], "/etc/tuxbox/satellites.xml")

	def cancel(self):
		print "\n[Satloader] cancel\n"
		self.close(None)

###########################################################################

class getSatfromUrl(object):
	def __init__(self, session, url=None, path=None):
		self.session = session
		self.download(url, path)

	def download(self, url, path):
		downloadPage(url, path).addCallback(self.downloadDone).addErrback(self.downloadError)

	def downloadError(self, raw):
		self.session.open(MessageBox, text = _("Error downloading"), type = MessageBox.TYPE_ERROR)

	def downloadDone(self,raw):
		self.session.open(MessageBox, text = _("Downloading: Success\n\nPlease restart Enigma2 manually"), type = MessageBox.TYPE_INFO)

###########################################################################

def main(session, **kwargs):
	print "\n[Satloader] start\n"	
	session.open(Satloader)

###########################################################################

def Plugins(**kwargs):
	return PluginDescriptor(
			name="Satloader Plugin",
			description="update satellites.xml",
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc=main)
