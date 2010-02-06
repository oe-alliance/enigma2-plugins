#
#  VirtualZap E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2010
#  Coding idea by vali
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Label import Label
from enigma import eServiceReference,  eTimer, getDesktop
from ServiceReference import ServiceReference
from Components.SystemInfo import SystemInfo
from enigma import eServiceCenter, getBestPlayableServiceReference
from Components.VideoWindow import VideoWindow
from enigma import ePoint, eEPGCache
from time import localtime, time
from Screens.InfoBarGenerics import InfoBarShowHide, NumberZap
from Screens.InfoBar import InfoBar

from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop

InfoBarShowHideINIT = None

from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo, getConfigListEntry, configfile
from Components.ConfigList import ConfigList, ConfigListScreen

# for localized messages
from . import _

config.plugins.virtualzap = ConfigSubsection()
config.plugins.virtualzap.mode = ConfigSelection(default="0", choices = [("0", _("as plugin in extended bar")),("1", _("with long OK press")), ("2", _("with exit button")),("3", _("as plugin in pluginmenu"))])
config.plugins.virtualzap.usepip = ConfigYesNo(default = True)

def autostart(reason, **kwargs):
	if config.plugins.virtualzap.mode.value != "0":
		# overide InfoBarShowHide
		global InfoBarShowHideINIT
		if InfoBarShowHideINIT is None:
			InfoBarShowHideINIT = InfoBarShowHide.__init__
		InfoBarShowHide.__init__ = InfoBarShowHide__init__
		# new method
		InfoBarShowHide.showVZ = showVZ
		if config.plugins.virtualzap.mode.value == "2":
			InfoBarShowHide.newHide = newHide

def InfoBarShowHide__init__(self):
	# initialize InfoBarShowHide with original __init__
	InfoBarShowHideINIT(self)
	if config.plugins.virtualzap.mode.value == "1":
		# delete current key map --> we have to use "ok" with b-flag
		del self["ShowHideActions"]
		# initialize own actionmap with ok = b and longOK = l
		self["myactions"] = ActionMap( ["myShowHideActions"] ,
		{
			"toggleShow": self.toggleShow,
			"longOK": self.showVZ,
			"hide": self.hide,
		}, 1)
	elif config.plugins.virtualzap.mode.value == "2":
		# overide hide 
		self["ShowHideActions"] = ActionMap( ["InfobarShowHideActions"] ,
		{
			"toggleShow": self.toggleShow,
			"hide": self.newHide,
		}, 1)


def showVZ(self):
	from  Screens.InfoBarGenerics import InfoBarEPG, InfoBarPiP
	# check for InfoBarEPG --> only start if true
	if isinstance(self, InfoBarEPG):
		# check for PiP
		if isinstance(self, InfoBarPiP):
			# check if PiP is already shown
			if self.pipShown():
				# it is... close it!
				self.showPiP()
		if InfoBar and InfoBar.instance:
			InfoBar.instance.session.open(VirtualZap, InfoBar.instance.servicelist)

def newHide(self):
	# remember if infobar is shown
	visible = self.shown
	self.hide()
	if not visible:
		# infobar was not shown, start VZ
		self.showVZ()

def Plugins(**kwargs):
 	plist =  [PluginDescriptor(name="Virtual Zap Setup", description=_("Virtual Zap Setup"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "plugin.png", fnc = setup)]
	if config.plugins.virtualzap.mode.value == "0":
		plist.append(PluginDescriptor(name="Virtual Zap", description=_("Virtual (PiP) Zap"), where = [PluginDescriptor.WHERE_EXTENSIONSMENU],icon = "plugin.png", fnc = main))
	elif config.plugins.virtualzap.mode.value == "1" or config.plugins.virtualzap.mode.value == "2":
		plist.append(PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART],fnc = autostart))
	elif config.plugins.virtualzap.mode.value == "3":
		plist.append(PluginDescriptor(name="Virtual Zap", description=_("Virtual (PiP) Zap"), where = [PluginDescriptor.WHERE_PLUGINMENU],icon = "plugin.png", fnc = main))
	return plist

def setup(session,**kwargs):
	session.open(VirtualZapConfig)

def main(session,**kwargs):
	if InfoBar and InfoBar.instance:
		session.open(VirtualZap, InfoBar.instance.servicelist)

class VirtualZap(Screen):
	sz_w = getDesktop(0).size().width()

	#
	# VirtualZap or VirtualZapNoPiP
	#

	if SystemInfo.get("NumVideoDecoders", 1) > 1 and config.plugins.virtualzap.usepip.value:
		# the video widget position is odd for 1280 and 1024... but it seems that the video position is calculated wrong with res <> 720
		if sz_w == 1280:
			skin = """
				<screen name="VirtualZap" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="transparent">
					<widget name="NowChannel" position="350,555" size="740,25" zPosition="2" font="Regular;22" />
					<widget name="NowEPG" position="350,580" size="620,25" zPosition="2" font="Regular;22" foregroundColor="#fcc000" />
					<widget name="NextEPG" position="350,605" size="620,25" zPosition="2" font="Regular;22" />
					<widget name="NowTime" position="970,580" size="120,25" zPosition="2" font="Regular;22" halign="right" foregroundColor="#fcc000"/>
					<widget name="NextTime" position="970,605" size="120,25" zPosition="2" font="Regular;22" halign="right"/>
					<widget name="video" position="70,420" size="120,96" backgroundColor="transparent" />
				</screen>"""

		elif sz_w == 1024:

			skin = """
				<screen name="VirtualZap" position="0,440" size="1024,96" flags="wfNoBorder" backgroundColor="transparent">
					<widget name="NowChannel" position="280,10" size="675,25" zPosition="2" font="Regular;22" />
					<widget name="NowEPG" position="280,35" size="555,25" zPosition="2" font="Regular;22" foregroundColor="#fcc000" />
					<widget name="NextEPG" position="280,60" size="555,25" zPosition="2" font="Regular;22" />
					<widget name="NowTime" position="835,35" size="120,25" zPosition="2" font="Regular;22" halign="right" foregroundColor="#fcc000"/>
					<widget name="NextTime" position="835,60" size="120,25" zPosition="2" font="Regular;22" halign="right"/>
					<widget name="video" position="70,0" size="120,96" backgroundColor="transparent" />
				</screen>"""

		else:

			skin = """
				<screen name="VirtualZap" position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="transparent">
					<widget name="NowChannel" position="170,450" size="510,25" zPosition="2" font="Regular;22" />
					<widget name="NowEPG" position="170,475" size="390,25" zPosition="2" font="Regular;22" foregroundColor="#fcc000"/>
					<widget name="NextEPG" position="170,500" size="390,25" zPosition="2" font="Regular;22" />
					<widget name="NowTime" position="560,475" size="120,25" zPosition="2" font="Regular;22" halign="right" foregroundColor="#fcc000"/>
					<widget name="NextTime" position="560,500" size="120,25" zPosition="2" font="Regular;22" halign="right"/>
					<widget name="video" position="40,440" size="120,96" backgroundColor="transparent" />
				</screen>"""
	else:
		if sz_w == 1280:
			skin = """
				<screen name="VirtualZapNoPiP" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="transparent">
					<widget name="NowChannel" position="270,555" size="740,25" zPosition="2" font="Regular;22" />
					<widget name="NowEPG" position="270,580" size="620,25" zPosition="2" font="Regular;22" foregroundColor="#fcc000" />
					<widget name="NextEPG" position="270,605" size="620,25" zPosition="2" font="Regular;22" />
					<widget name="NowTime" position="890,580" size="120,25" zPosition="2" font="Regular;22" halign="right" foregroundColor="#fcc000"/>
					<widget name="NextTime" position="890,605" size="120,25" zPosition="2" font="Regular;22" halign="right"/>
				</screen>"""

		elif sz_w == 1024:

			skin = """
				<screen name="VirtualZapNoPiP" position="0,440" size="1024,96" flags="wfNoBorder" backgroundColor="transparent">
					<widget name="NowChannel" position="167,10" size="690,25" zPosition="2" font="Regular;22" />
					<widget name="NowEPG" position="167,35" size="570,25" zPosition="2" font="Regular;22" foregroundColor="#fcc000" />
					<widget name="NextEPG" position="167,60" size="570,25" zPosition="2" font="Regular;22" />
					<widget name="NowTime" position="737,35" size="120,25" zPosition="2" font="Regular;22" halign="right" foregroundColor="#fcc000"/>
					<widget name="NextTime" position="737,60" size="120,25" zPosition="2" font="Regular;22" halign="right"/>
				</screen>"""

		else:

			skin = """
				<screen name="VirtualZapNoPiP" position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="transparent">
					<widget name="NowChannel" position="80,450" size="560,25" zPosition="2" font="Regular;22" />
					<widget name="NowEPG" position="80,475" size="440,25" zPosition="2" font="Regular;22" foregroundColor="#fcc000"/>
					<widget name="NextEPG" position="80,500" size="440,25" zPosition="2" font="Regular;22" />
					<widget name="NowTime" position="520,475" size="120,25" zPosition="2" font="Regular;22" halign="right" foregroundColor="#fcc000"/>
					<widget name="NextTime" position="520,500" size="120,25" zPosition="2" font="Regular;22" halign="right"/>
				</screen>"""


	def __init__(self, session, servicelist = None):
		Screen.__init__(self, session)
		self.session = session
		self.pipAvailable = False
		if SystemInfo.get("NumVideoDecoders", 1) > 1 and config.plugins.virtualzap.usepip.value:
			self.skinName = "VirtualZap"
			self.pipAvailable = True
		else:
			self.skinName = "VirtualZapNoPiP"
		self.epgcache = eEPGCache.getInstance()
		self.CheckForEPG = eTimer()
		self.CheckForEPG.callback.append(self.CheckItNow)
		self["NowChannel"] = Label()
		self["NowEPG"] = Label()
		self["NextEPG"] = Label()
		self["NowTime"] = Label()
		self["NextTime"] = Label()
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"], 
		{
			"ok": self.ok, 
			"cancel": self.closing,
			"right": self.prgPlus,
			"left": self.prgMinus,
		},-2)
		self["actions2"] = NumberActionMap(["NumberActions"],
		{
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
		}, -1)
		self.onLayoutFinish.append(self.onLayoutReady)
		# PiP
		if self.pipAvailable:
			# activate PiP support
			self["video"] = VideoWindow()
			self.pip = None
			self.currentPiP = ""
		# this is the servicelist from ChannelSelectionBase
		self.servicelist = servicelist
		self.newServicePlayed  =  False
		# needed, because if we won't zap, we habe to go back to the current bouquet and service
		self.curRef = ServiceReference(self.servicelist.getCurrentSelection())
		self.curBouquet = self.servicelist.getRoot()

	def onLayoutReady(self):
		self.updateInfos()

	def prgPlus(self):
		# get next service
		self.servicelist.moveDown()
		if self.isPlayable():
			self.updateInfos()
		else:
			# service is not playable, try next one
			self.prgPlus()

	def prgMinus(self):
		# get previous service
		self.servicelist.moveUp()
		if self.isPlayable():
			self.updateInfos()
		else:
			# service is not playable, try next one
			self.prgMinus()

	def isPlayable(self):
		# check if service is playable
		current = ServiceReference(self.servicelist.getCurrentSelection())
		return not (current.ref.flags & (eServiceReference.isMarker|eServiceReference.isDirectory))

	def updateInfos(self):
		# update data
		current = ServiceReference(self.servicelist.getCurrentSelection())
		self["NowChannel"].setText(current.getServiceName())
		nowepg, nowtimedisplay = self.getEPGNowNext(current.ref,0)
		nextepg, nexttimedisplay = self.getEPGNowNext(current.ref,1)
		self["NowEPG"].setText(nowepg)
		self["NextEPG"].setText(nextepg)
		self["NowTime"].setText(nowtimedisplay)
		self["NextTime"].setText(nexttimedisplay)
		if not nowepg:
			# no epg found --> let's try it again, but only if PiP is activated
			if self.pipAvailable:
				self.CheckForEPG.start(3000, True)
		if self.pipAvailable:
			# play in videowindow
			self.playService(current.ref)

	def getEPGNowNext(self,ref, modus):
		# get now || next event
		if self.epgcache is not None:
			event = self.epgcache.lookupEvent(['IBDCTSERNX', (ref.toString(), modus, -1)])
			if event:
				if event[0][4]:
					t = localtime(event[0][1])
					duration = event[0][2]
					if modus == 0:
						timedisplay = "+%d min" % (((event[0][1] + duration) - time()) / 60)
					elif modus == 1:
						timedisplay = "%d min" %  (duration / 60)
					return "%02d:%02d %s" % (t[3],t[4], event[0][4]), timedisplay
				else:
					return "", ""
		return "", ""

	def closing(self):
		if self.pipAvailable:
			self.pipservice = None
		if not self.newServicePlayed:
			# we need to select the old service with bouquet
			if self.curBouquet != self.servicelist.getRoot():
				self.servicelist.clearPath()
				if self.servicelist.bouquet_root != self.curBouquet:
					self.servicelist.enterPath(self.servicelist.bouquet_root)
				self.servicelist.enterPath(self.curBouquet)
			self.servicelist.setCurrentSelection(self.curRef.ref)
		self.close()
			
	def ok(self):
		# we have to close PiP first, otherwise the service-display is freezed
		if self.pipAvailable:
			self.pipservice = None
		# play selected service and close virtualzap
		self.newServicePlayed = True
		self.servicelist.zap()
		self.close()

	def CheckItNow(self):
		self.CheckForEPG.stop()
		self.updateInfos()

	# if available play service in PiP 
	def playService(self, service):
		if service and (service.flags & eServiceReference.isGroup):
			ref = getBestPlayableServiceReference(service, eServiceReference())
		else:
			ref = service
		if ref and ref.toString() != self.currentPiP:
			self.pipservice = eServiceCenter.getInstance().play(ref)
			if self.pipservice and not self.pipservice.setTarget(1):
				self.pipservice.start()
				self.currentPiP = ref.toString()
			else:
				self.pipservice = None
				self.currentPiP = ""


	# switch with numbers
	def keyNumberGlobal(self, number):
		self.session.openWithCallback(self.numberEntered, NumberZap, number)

	def numberEntered(self, retval):
		if retval > 0:
			self.zapToNumber(retval)

	def searchNumberHelper(self, serviceHandler, num, bouquet):
		servicelist = serviceHandler.list(bouquet)
		if not servicelist is None:
			while num:
				serviceIterator = servicelist.getNext()
				if not serviceIterator.valid(): #check end of list
					break
				playable = not (serviceIterator.flags & (eServiceReference.isMarker|eServiceReference.isDirectory))
				if playable:
					num -= 1;
			if not num: #found service with searched number ?
				return serviceIterator, 0
		return None, num

	def zapToNumber(self, number):
		bouquet = self.servicelist.bouquet_root
		service = None
		serviceHandler = eServiceCenter.getInstance()
		bouquetlist = serviceHandler.list(bouquet)
		if not bouquetlist is None:
			while number:
				bouquet = bouquetlist.getNext()
				if not bouquet.valid(): #check end of list
					break
				if bouquet.flags & eServiceReference.isDirectory:
					service, number = self.searchNumberHelper(serviceHandler, number, bouquet)
		if not service is None:
			if self.servicelist.getRoot() != bouquet: #already in correct bouquet?
				self.servicelist.clearPath()
				if self.servicelist.bouquet_root != bouquet:
					self.servicelist.enterPath(self.servicelist.bouquet_root)
				self.servicelist.enterPath(bouquet)
			self.servicelist.setCurrentSelection(service) #select the service in servicelist
		# update infos, no matter if service is none or not
		self.updateInfos()



class VirtualZapConfig(Screen, ConfigListScreen):

	skin = """
		<screen position="center,center" size="560,110" title="Virtual Zap Config" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="20,50" size="520,330" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self.list = [ ]
		self.list.append(getConfigListEntry(_("Usage"), config.plugins.virtualzap.mode))
		if SystemInfo.get("NumVideoDecoders", 1) > 1:
			self.list.append(getConfigListEntry(_("Show with PiP"), config.plugins.virtualzap.usepip))
		ConfigListScreen.__init__(self, self.list, session)
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyClose,
		}, -2)

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("GUI needs a restart to apply the new settings.\nDo you want to Restart the GUI now?"), MessageBox.TYPE_YESNO)
		restartbox.setTitle(_("Restart GUI now?"))
		

	def keyClose(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def restartGUI(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()

