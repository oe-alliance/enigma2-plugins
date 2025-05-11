#######################################################################
#
#    EasyInfo for Dreambox-Enigma2
#    Coded by Vali (c)2011
#
#  This plugin is licensed under the Creative Commons
#  Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#  To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#
#######################################################################


from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InfoBarGenerics import InfoBarPlugins
from Screens.ChoiceBox import ChoiceBox
from Screens.TimerEdit import TimerEditList
from Screens.EpgSelection import EPGSelection
from Screens.EventView import EventViewSimple, EventViewBase
from Screens.ServiceInfo import ServiceInfo
from Screens.ChannelSelection import BouquetSelector
from Screens.TimeDateInput import TimeDateInput
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from Components.EpgList import EPGList, EPG_TYPE_MULTI
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigClock
from Components.Sources.StaticText import StaticText
from Tools.Directories import fileExists, pathExists
from Tools.LoadPixmap import LoadPixmap
from ServiceReference import ServiceReference
from enigma import eListboxPythonMultiContent, gFont, getDesktop, eTimer, eServiceReference, RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_WRAP, RT_HALIGN_RIGHT, RT_VALIGN_TOP
from time import localtime, time, mktime


EINbaseInfoBarPlugins__init__ = None
EINStartOnlyOneTime = False
EINsession = None
EINposition = 0
InfoBar_instance = None
mepg_config_initialized = False
sz_w = getDesktop(0).size().width()
if sz_w == 1280:
	SKINTYPE = 3
elif sz_w == 1024:
	SKINTYPE = 2
else:
	SKINTYPE = 1


CHOICELIST = [("no", _("Disabled")),
			("eventinfo", _("Event info")),
			("singleepg", _("Single EPG")),
			("multiepg", _("Multi EPG")),
			("easypg", _("Easy-PG")),
			("easysel", _("Easy-Selection")),
			("graphepg", _("Graphik multi-EPG")),
			("merlinepg", _("Merlin EPG")),
			("cooltv", _("Cool-TV")),
			("timers", _("Timerlist")),
			("epgsearch", _("EPG search")),
			("autotimer", _("Autotimer")),
			("channelinfo", _("Channel info")),
			("imdbinfo", _("IMDB info")),
			("primetime", _("Prime Time Manager")),
			("epgrefresh", _("EPG refresh")),
			("sysinfo", _("Sherlock"))
			]
config.plugins.EasyInfo = ConfigSubsection()
config.plugins.EasyInfo.pos1 = ConfigSelection(default="eventinfo", choices=CHOICELIST)
config.plugins.EasyInfo.pos2 = ConfigSelection(default="singleepg", choices=CHOICELIST)
config.plugins.EasyInfo.pos3 = ConfigSelection(default="merlinepg", choices=CHOICELIST)
config.plugins.EasyInfo.pos4 = ConfigSelection(default="timers", choices=CHOICELIST)
config.plugins.EasyInfo.pos5 = ConfigSelection(default="channelinfo", choices=CHOICELIST)
config.plugins.EasyInfo.pos6 = ConfigSelection(default="no", choices=CHOICELIST)
config.plugins.EasyInfo.pos7 = ConfigSelection(default="no", choices=CHOICELIST)
config.plugins.EasyInfo.pos8 = ConfigSelection(default="no", choices=CHOICELIST)
config.plugins.EasyInfo.pos9 = ConfigSelection(default="no", choices=CHOICELIST)
config.plugins.EasyInfo.pos10 = ConfigSelection(default="no", choices=CHOICELIST)
config.plugins.EasyInfo.pos11 = ConfigSelection(default="no", choices=CHOICELIST)
config.plugins.EasyInfo.EvInStart = ConfigSelection(default="yes", choices=[("no", _("Disabled")), ("yes", _("Enabled"))])
config.plugins.EasyInfo.bEvInYellow = ConfigSelection(default="singleepg", choices=[("singleepg", _("Single EPG")), ("multiepg", _("Multi EPG")), ("easypg", _("Easy-PG")), ("graphepg", _("Graphik multi-EPG")), ("merlinepg", _("Merlin EPG")), ("cooltv", _("Cool-TV")), ("imdbinfo", _("IMDB info"))])
config.plugins.EasyInfo.bEvInBlue = ConfigSelection(default="multiepg", choices=[("singleepg", _("Single EPG")), ("multiepg", _("Multi EPG")), ("easypg", _("Easy-PG")), ("graphepg", _("Graphik multi-EPG")), ("merlinepg", _("Merlin EPG")), ("cooltv", _("Cool-TV")), ("imdbinfo", _("IMDB info"))])
config.plugins.EasyInfo.myPicons = ConfigSelection(default="/media/usb/epgpicon/", choices=[("/media/usb/epgpicon/", "/media/usb/epgpicon/"), ("/media/cf/epgpicon/", "/media/cf/epgpicon/"), ("/media/hdd/epgpicon/", "/media/hdd/epgpicon/"), ("/usr/share/enigma2/epgpicon/", "/usr/share/enigma2/epgpicon/")])
config.plugins.EasyInfo.epgOKFunc = ConfigSelection(default="info", choices=[("info", _("Event info")), ("zap", _("Just zap")), ("exitzap", _("Zap and Exit"))])
config.plugins.EasyInfo.Primetime1 = ConfigClock(default=63000)
config.plugins.EasyInfo.Primetime2 = ConfigClock(default=69300)
config.plugins.EasyInfo.Primetime3 = ConfigClock(default=75600)
config.plugins.EasyInfo.buttTV = ConfigSelection(default="easysel", choices=[("no", _("Disabled")), ("easysel", _("Easy-Selection")), ("easypg", _("Easy-PG"))])


def Plugins(**kwargs):
	return [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=EasyInfoAutostart)]


def EasyInfoAutostart(reason, **kwargs):
	global EINbaseInfoBarPlugins__init__
	if "session" in kwargs:
		global EINsession
		EINsession = kwargs["session"]
		if EINbaseInfoBarPlugins__init__ is None:
			EINbaseInfoBarPlugins__init__ = InfoBarPlugins.__init__
		InfoBarPlugins.__init__ = InfoBarPlugins__init__
		InfoBarPlugins.info = info
		if config.plugins.EasyInfo.buttTV.value != "no":
			InfoBarPlugins.tvbut = tvbut


def InfoBarPlugins__init__(self):
	global EINStartOnlyOneTime
	if not EINStartOnlyOneTime:
		EINStartOnlyOneTime = True
		global InfoBar_instance
		InfoBar_instance = self
		if config.plugins.EasyInfo.buttTV.value != "no":
			self["EasyInfoActions"] = ActionMap(["EasyInfoActions"],
				{"info_but": self.info, "tv_but": self.tvbut}, -1)
		else:
			self["EasyInfoActions"] = ActionMap(["EasyInfoActionsALT"],
				{"info_but": self.info}, -1)
	else:
		InfoBarPlugins.__init__ = InfoBarPlugins.__init__
		InfoBarPlugins.info = None
		if config.plugins.EasyInfo.buttTV.value != "no":
			InfoBarPlugins.tvbut = None
	EINbaseInfoBarPlugins__init__(self)


def info(self):
	if config.plugins.EasyInfo.EvInStart.value == "yes":
		epglist = []
		self.epglist = epglist
		service = self.session.nav.getCurrentService()
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		info = service.info()
		ptr = info.getEvent(0)
		if ptr:
			epglist.append(ptr)
		ptr = info.getEvent(1)
		if ptr:
			epglist.append(ptr)
		if epglist:
			self.session.open(EasyEvent, epglist[0], ServiceReference(ref))
		else:
			self.session.open(EasyInfo)
	else:
		self.session.open(EasyInfo)


def tvbut(self):
	myService = self.session.nav.getCurrentService()
	myTS = myService and myService.timeshift()
	if myTS is not None:
		if myTS.isTimeshiftActive():
			InfoBar_instance.stopTimeshift()
			return
	if InfoBar_instance.servicelist.mode == 1:
		InfoBar_instance.showTv()
		return
	bouquets = InfoBar_instance.servicelist.getBouquetList()
	if bouquets is None:
		cnt = 0
	else:
		cnt = len(bouquets)
		IBservices = InfoBar_instance.getBouquetServices(InfoBar_instance.servicelist.getRoot())
	if cnt > 1:
		if config.plugins.EasyInfo.buttTV.value == "easysel":
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasySelection, IBservices, EINzapTo, None, EINchangeBouquetCB))
		elif config.plugins.EasyInfo.buttTV.value == "easypg":
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasyPG, IBservices, EINzapTo, None, EINchangeBouquetCB))
	elif cnt == 1:
		if config.plugins.EasyInfo.buttTV.value == "easysel":
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasySelection, IBservices, EINzapTo, None, None))
		if config.plugins.EasyInfo.buttTV.value == "easypg":
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasyPG, IBservices, EINzapTo, None, EINchangeBouquetCB))


def getPluginByName(sstr):
	sret = " "
	for xs in CHOICELIST:
		if sstr == xs[0]:
			sret = xs[1]
			break
	return sret


def EINPanelEntryComponent(key, text):
	res = [text]
	bpng = LoadPixmap(EasyInfo.EINiconspath + "key-" + text[0] + ".png")
	if bpng is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 5, 5, 50, bpng))
	png = LoadPixmap(EasyInfo.EINiconspath + key + ".png")
	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 5, 5, 100, 50, png))
	if config.plugins.EasyInfo.EvInStart.value == "yes" or SKINTYPE == 1:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 115, 17, 300, 35, 0, RT_HALIGN_LEFT, getPluginByName(text[1])))
	return res


class EINPanelList(MenuList):
	def __init__(self, list, selection=0, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setItemHeight(60)
		self.selection = selection

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		self.moveToIndex(self.selection)


class ConfigEasyInfo(ConfigListScreen, Screen):
	skin = """
		<screen name="ConfigEasyInfo" position="center,center" size="600,410" title="EasyInfo settings...">
			<widget name="config" position="5,5" scrollbarMode="showOnDemand" size="590,375"/>
			<eLabel font="Regular;20" foregroundColor="#00ff4A3C" halign="center" position="20,385" size="140,26" text="Cancel"/>
			<eLabel font="Regular;20" foregroundColor="#0056C856" halign="center" position="165,385" size="140,26" text="Save"/>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("EasyInfo settings..."))
		self.session = session
		self.oldsetting = [config.plugins.EasyInfo.EvInStart.value, config.plugins.EasyInfo.buttTV.value]
		list = []
		list.append(getConfigListEntry(_("Start first EventInfo:"), config.plugins.EasyInfo.EvInStart))
		list.append(getConfigListEntry(_("Replace TV-button function:"), config.plugins.EasyInfo.buttTV))
		list.append(getConfigListEntry(_("EventInfo yellow button:"), config.plugins.EasyInfo.bEvInYellow))
		list.append(getConfigListEntry(_("EventInfo blue button:"), config.plugins.EasyInfo.bEvInBlue))
		list.append(getConfigListEntry(_("OK function in Easy-PG:"), config.plugins.EasyInfo.epgOKFunc))
		list.append(getConfigListEntry(_("Easy-PG picons path:"), config.plugins.EasyInfo.myPicons))
		list.append(getConfigListEntry(_("Easy-PG Primetime 1:"), config.plugins.EasyInfo.Primetime1))
		list.append(getConfigListEntry(_("Easy-PG Primetime 2 (main):"), config.plugins.EasyInfo.Primetime2))
		list.append(getConfigListEntry(_("Easy-PG Primetime 3:"), config.plugins.EasyInfo.Primetime3))
		list.append(getConfigListEntry(_("Position 1 (info button):"), config.plugins.EasyInfo.pos1))
		list.append(getConfigListEntry(_("Position 2 (red button):"), config.plugins.EasyInfo.pos2))
		list.append(getConfigListEntry(_("Position 3 (green button):"), config.plugins.EasyInfo.pos3))
		list.append(getConfigListEntry(_("Position 4 (yellow button):"), config.plugins.EasyInfo.pos4))
		list.append(getConfigListEntry(_("Position 5 (blue button):"), config.plugins.EasyInfo.pos5))
		list.append(getConfigListEntry(_("Position 6:"), config.plugins.EasyInfo.pos6))
		list.append(getConfigListEntry(_("Position 7:"), config.plugins.EasyInfo.pos7))
		list.append(getConfigListEntry(_("Position 8:"), config.plugins.EasyInfo.pos8))
		list.append(getConfigListEntry(_("Position 9:"), config.plugins.EasyInfo.pos9))
		list.append(getConfigListEntry(_("Position 10:"), config.plugins.EasyInfo.pos10))
		list.append(getConfigListEntry(_("Position 11:"), config.plugins.EasyInfo.pos11))
		ConfigListScreen.__init__(self, list)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {"green": self.save, "red": self.exit, "cancel": self.exit, "yellow": self.exit}, -1)

	def save(self):
		for x in self["config"].list:
			x[1].save()
		if self.oldsetting != [config.plugins.EasyInfo.EvInStart.value, config.plugins.EasyInfo.buttTV.value]:
			self.session.open(MessageBox, text=_('You need GUI-restart to load the new settings!'), type=MessageBox.TYPE_INFO)
		self.close()

	def exit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()


class EasyInfo(Screen):
	if SKINTYPE == 3:
		if config.plugins.EasyInfo.EvInStart.value == "yes":
			skin = """
			<screen flags="wfNoBorder" position="0,0" size="450,720" title="Easy Info">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/bg.png" position="0,0" size="450,576"/>
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/bg.png" position="0,576" size="450,145"/>
				<widget name="list" position="60,30" size="350,660" scrollbarMode="showNever" transparent="1" zPosition="2"/>
			</screen>"""
		else:
			skin = """
			<screen backgroundColor="background" flags="wfNoBorder" position="0,0" size="1280,720" title="Easy Info">
				<widget name="list" position="55,30" size="110,660" scrollbarMode="showNever" transparent="1" zPosition="2"/>
				<eLabel backgroundColor="#666666" position="250,359" size="1280,2"/>
				<widget font="Regular;24" foregroundColor="#fcc000" position="630,50" render="Label" size="600,30" source="session.CurrentService" transparent="1" zPosition="1">
					<convert type="ServiceName">Name</convert>
				</widget>
				<widget font="Regular;24" position="250,50" render="Label" size="100,30" source="session.Event_Now" transparent="1" zPosition="1">
					<convert type="EventTime">StartTime</convert>
					<convert type="ClockToText">Default</convert>
				</widget>
				<widget font="Regular;24" noWrap="1" position="250,90" render="Label" size="900,30" source="session.Event_Now" transparent="1" zPosition="1">
					<convert type="EventName">Name</convert>
				</widget>
				<widget font="Regular;22" foregroundColor="#fcc000" position="350,50" halign="right" render="Label" size="130,30" source="session.Event_Now" transparent="1" zPosition="1">
					<convert type="EventTime">Remaining</convert>
					<convert type="RemainingToText">InMinutes</convert>
				</widget>
				<widget font="Regular;24" position="250,400" render="Label" size="100,30" source="session.Event_Next" transparent="1" zPosition="1">
					<convert type="EventTime">StartTime</convert>
					<convert type="ClockToText">Default</convert>
				</widget>
				<widget font="Regular;24" foregroundColor="#aaaaaa" noWrap="1" position="250,370" render="Label" size="900,30" source="session.Event_Next" transparent="1" zPosition="1">
					<convert type="EventName">Name</convert>
				</widget>
				<widget font="Regular;24" foregroundColor="#aaaaaa" position="350,400" render="Label" size="130,30" source="session.Event_Next" transparent="1" zPosition="1">
					<convert type="EventTime">Duration</convert>
					<convert type="ClockToText">InMinutes</convert>
				</widget>
				<widget backgroundColor="#555555" borderColor="#555555" borderWidth="4" position="490,57" render="Progress" size="120,14" source="session.Event_Now" zPosition="2">
					<convert type="EventTime">Progress</convert>
				</widget>
				<widget font="Regular;22" position="250,127" render="Label" size="950,225" source="session.Event_Now" transparent="1" valign="top" zPosition="5">
					<convert type="EventName">ExtendedDescription</convert>
				</widget>
				<widget font="Regular;22" foregroundColor="#aaaaaa" position="250,437" render="Label" size="950,225" source="session.Event_Next" transparent="1" valign="top" zPosition="5">
					<convert type="EventName">ExtendedDescription</convert>
				</widget>
			</screen>"""
	elif SKINTYPE == 2:
		if config.plugins.EasyInfo.EvInStart.value == "yes":
			skin = """
			<screen flags="wfNoBorder" position="-20,0" size="450,576" title="Easy Info">
				<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/bg.png" position="0,0" size="450,576"/>
				<widget name="list" position="70,48" size="320,480" scrollbarMode="showNever" transparent="1" zPosition="2"/>
			</screen>"""
		else:
			skin = """
			<screen backgroundColor="background" flags="wfNoBorder" position="0,0" size="1024,720" title="Easy Info">
				<widget name="list" position="40,48" scrollbarMode="showNever" size="110,480" transparent="1" zPosition="2"/>
				<eLabel backgroundColor="#666666" position="210,289" size="1000,2"/>
				<widget font="Regular;20" foregroundColor="#fcc000" position="570,50" render="Label" size="377,30" source="session.CurrentService" transparent="1" zPosition="1">
					<convert type="ServiceName">Name</convert>
				</widget>
				<widget font="Regular;20" position="210,50" render="Label" size="70,30" source="session.Event_Now" transparent="1" zPosition="1">
					<convert type="EventTime">StartTime</convert>
					<convert type="ClockToText">Default</convert>
				</widget>
				<widget font="Regular;20" noWrap="1" position="210,85" render="Label" size="736,30" source="session.Event_Now" transparent="1" zPosition="1">
					<convert type="EventName">Name</convert>
				</widget>
				<widget font="Regular;20" foregroundColor="#fcc000" halign="right" position="290,50" render="Label" size="130,30" source="session.Event_Now" transparent="1" zPosition="1">
					<convert type="EventTime">Remaining</convert>
					<convert type="RemainingToText">InMinutes</convert>
				</widget>
				<widget font="Regular;20" position="210,333" render="Label" size="82,30" source="session.Event_Next" transparent="1" zPosition="1">
					<convert type="EventTime">StartTime</convert>
					<convert type="ClockToText">Default</convert>
				</widget>
				<widget font="Regular;20" foregroundColor="#aaaaaa" noWrap="1" position="210,300" render="Label" size="900,30" source="session.Event_Next" transparent="1" zPosition="1">
					<convert type="EventName">Name</convert>
				</widget>
				<widget font="Regular;20" foregroundColor="#aaaaaa" position="295,333" render="Label" size="130,30" source="session.Event_Next" transparent="1" zPosition="1">
					<convert type="EventTime">Duration</convert>
					<convert type="ClockToText">InMinutes</convert>
				</widget>
				<widget backgroundColor="#555555" borderColor="#555555" borderWidth="4" position="425,55" render="Progress" size="120,14" source="session.Event_Now" zPosition="2">
					<convert type="EventTime">Progress</convert>
				</widget>
				<widget font="Regular;18" position="210,115" render="Label" size="736,170" source="session.Event_Now" transparent="1" valign="top" zPosition="5">
					<convert type="EventName">ExtendedDescription</convert>
				</widget>
				<widget font="Regular;18" foregroundColor="#aaaaaa" position="210,362" render="Label" size="736,170" source="session.Event_Next" transparent="1" valign="top" zPosition="5">
					<convert type="EventName">ExtendedDescription</convert>
				</widget>
			</screen>"""
	else:
		skin = """
		<screen position="center,center" size="320,440" title="Easy Info">
			<widget name="list" position="10,10" size="300,420" scrollbarMode="showOnDemand" />
		</screen>"""
	if pathExists('/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/icons/'):
		EINiconspath = '/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/icons/'
	else:
		EINiconspath = '/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/'

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.list = []
		self.__keys = []
		MPaskList = []
		fertig = False
		self["key_info"] = StaticText(" ")
		self["key_yellow"] = StaticText(" ")
		self["key_green"] = StaticText(" ")
		self["key_red"] = StaticText(" ")
		self["key_blue"] = StaticText(" ")
		if True:
			if config.plugins.EasyInfo.pos1.value != "no":
				self.__keys.append(config.plugins.EasyInfo.pos1.value)
				MPaskList.append(("info", config.plugins.EasyInfo.pos1.value))
				self["key_info"].setText(_(getPluginByName(config.plugins.EasyInfo.pos1.value)))
			else:
				fertig = True
			if config.plugins.EasyInfo.pos2.value != "no" and not fertig:
				self.__keys.append(config.plugins.EasyInfo.pos2.value)
				MPaskList.append(("red", config.plugins.EasyInfo.pos2.value))
				self["key_red"].setText(_(getPluginByName(config.plugins.EasyInfo.pos2.value)))
			else:
				fertig = True
			if config.plugins.EasyInfo.pos3.value != "no" and not fertig:
				self.__keys.append(config.plugins.EasyInfo.pos3.value)
				MPaskList.append(("green", config.plugins.EasyInfo.pos3.value))
				self["key_green"].setText(_(getPluginByName(config.plugins.EasyInfo.pos3.value)))
			else:
				fertig = True
			if config.plugins.EasyInfo.pos4.value != "no" and not fertig:
				self.__keys.append(config.plugins.EasyInfo.pos4.value)
				MPaskList.append(("yellow", config.plugins.EasyInfo.pos4.value))
				self["key_yellow"].setText(_(getPluginByName(config.plugins.EasyInfo.pos4.value)))
			else:
				fertig = True
			if config.plugins.EasyInfo.pos5.value != "no" and not fertig:
				self.__keys.append(config.plugins.EasyInfo.pos5.value)
				MPaskList.append(("blue", config.plugins.EasyInfo.pos5.value))
				self["key_blue"].setText(_(getPluginByName(config.plugins.EasyInfo.pos5.value)))
			else:
				fertig = True
			if config.plugins.EasyInfo.pos6.value != "no" and not fertig:
				self.__keys.append(config.plugins.EasyInfo.pos6.value)
				MPaskList.append(("x", config.plugins.EasyInfo.pos6.value))
			else:
				fertig = True
			if config.plugins.EasyInfo.pos7.value != "no" and not fertig:
				self.__keys.append(config.plugins.EasyInfo.pos7.value)
				MPaskList.append(("x", config.plugins.EasyInfo.pos7.value))
			else:
				fertig = True
			if config.plugins.EasyInfo.pos8.value != "no" and not fertig:
				self.__keys.append(config.plugins.EasyInfo.pos8.value)
				MPaskList.append(("x", config.plugins.EasyInfo.pos8.value))
			else:
				fertig = True
			if config.plugins.EasyInfo.pos9.value != "no" and not fertig:
				self.__keys.append(config.plugins.EasyInfo.pos9.value)
				MPaskList.append(("x", config.plugins.EasyInfo.pos9.value))
			else:
				fertig = True
			if config.plugins.EasyInfo.pos10.value != "no" and not fertig:
				self.__keys.append(config.plugins.EasyInfo.pos10.value)
				MPaskList.append(("x", config.plugins.EasyInfo.pos10.value))
			else:
				fertig = True
			if config.plugins.EasyInfo.pos11.value != "no" and not fertig:
				self.__keys.append(config.plugins.EasyInfo.pos11.value)
				MPaskList.append(("x", config.plugins.EasyInfo.pos11.value))
		self.keymap = {}
		pos = 0
		for x in MPaskList:
			strpos = str(self.__keys[pos])
			self.list.append(EINPanelEntryComponent(key=strpos, text=x))
			if self.__keys[pos] != "":
				self.keymap[self.__keys[pos]] = MPaskList[pos]
			pos += 1
		self["list"] = EINPanelList(list=self.list, selection=0)
		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ColorActions", "EPGSelectActions"],
		{
			"ok": self.go,
			"back": self.cancel,
			"menu": self.emContextMenu,
			"green": self.shotgreen,
			"red": self.shotred,
			"blue": self.shotblue,
			"yellow": self.shotyellow,
			"info": self.shotinfo
		}, -1)

	def cancel(self):
		self.close(None)

	def go(self):
		cursel = self["list"].l.getCurrentSelection()
		if cursel:
			antw = cursel[0]
			antw = antw and antw[1]
			EINcallbackFunc(antw)

	def emContextMenu(self):
		self.session.open(ConfigEasyInfo)

	def shotinfo(self):
		self["list"].moveToIndex(0)
		self.go()

	def shotred(self):
		self["list"].moveToIndex(1)
		self.go()

	def shotgreen(self):
		self["list"].moveToIndex(2)
		self.go()

	def shotyellow(self):
		self["list"].moveToIndex(3)
		self.go()

	def shotblue(self):
		self["list"].moveToIndex(4)
		self.go()


def EINchangeBouquetCB(direction, epg):
	global EINposition
	IBbouquets = InfoBar_instance.servicelist.getBouquetList()
	if EINposition > 0 and direction < 0:
		EINposition = EINposition - 1
	elif EINposition == 0 and direction < 0:
		EINposition = len(IBbouquets) - 1
	elif EINposition < (len(IBbouquets) - 1) and direction > 0:
		EINposition = EINposition + 1
	elif EINposition == (len(IBbouquets) - 1) and direction > 0:
		EINposition = 0
	IBservices = InfoBar_instance.getBouquetServices(IBbouquets[EINposition][1])
	if IBservices:
		epg.setServices(IBservices)


def EINzapTo(NewService):
	IBbouquets = InfoBar_instance.servicelist.getBouquetList()
	NewBbouquet = IBbouquets[EINposition][1]
	InfoBar_instance.servicelist.clearPath()
	if InfoBar_instance.servicelist.bouquet_root != NewBbouquet:
		InfoBar_instance.servicelist.enterPath(InfoBar_instance.servicelist.bouquet_root)
	InfoBar_instance.servicelist.enterPath(NewBbouquet)
	InfoBar_instance.servicelist.setCurrentSelection(NewService)
	InfoBar_instance.servicelist.zap()


def EINcallbackFunc(answer):
	if answer is None:
		return
	if EINsession is None:
		return
	if not InfoBar_instance:
		return
	if answer == "singleepg":
		ref = InfoBar_instance.servicelist.getCurrentSelection()
		if ref:
			InfoBar_instance.servicelist.savedService = ref
			EINsession.openWithCallback(InfoBar_instance.servicelist.SingleServiceEPGClosed, EPGSelection, ref, serviceChangeCB=InfoBar_instance.servicelist.changeServiceCB)
	elif answer == "easypg":
		bouquets = InfoBar_instance.servicelist.getBouquetList()
		if bouquets is None:
			cnt = 0
		else:
			cnt = len(bouquets)
			IBservices = InfoBar_instance.getBouquetServices(InfoBar_instance.servicelist.getRoot())
		if cnt > 1:
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasyPG, IBservices, EINzapTo, None, EINchangeBouquetCB))
		elif cnt == 1:
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasyPG, IBservices, EINzapTo, None, None))
	elif answer == "easysel":
		bouquets = InfoBar_instance.servicelist.getBouquetList()
		if bouquets is None:
			cnt = 0
		else:
			cnt = len(bouquets)
			IBservices = InfoBar_instance.getBouquetServices(InfoBar_instance.servicelist.getRoot())
		if cnt > 1:
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasySelection, IBservices, EINzapTo, None, EINchangeBouquetCB))
		elif cnt == 1:
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasySelection, IBservices, EINzapTo, None, None))
	elif answer == "timers":
		EINsession.open(TimerEditList)
	elif answer == "multiepg":
		bouquets = InfoBar_instance.servicelist.getBouquetList()
		if bouquets is None:
			cnt = 0
		else:
			cnt = len(bouquets)
		if cnt > 1:
			InfoBar_instance.bouquetSel = EINsession.openWithCallback(InfoBar_instance.closed, BouquetSelector, bouquets, InfoBar_instance.openBouquetEPG, enableWrapAround=True)
			InfoBar_instance.dlg_stack.append(InfoBar_instance.bouquetSel)
		elif cnt == 1:
			InfoBar_instance.openBouquetEPG(bouquets[0][1], True)
	elif answer == "eventinfo":
		epglist = []
		InfoBar_instance.epglist = epglist
		service = EINsession.nav.getCurrentService()
		ref = EINsession.nav.getCurrentlyPlayingServiceReference()
		info = service.info()
		ptr = info.getEvent(0)
		if ptr:
			epglist.append(ptr)
		ptr = info.getEvent(1)
		if ptr:
			epglist.append(ptr)
		if epglist:
			EINsession.open(EventViewSimple, epglist[0], ServiceReference(ref), InfoBar_instance.eventViewCallback)
	elif answer == "merlinepg":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MerlinEPG/plugin.pyo"):
			from Plugins.Extensions.MerlinEPG.plugin import Merlin_PGII, Merlin_PGd
			if config.plugins.MerlinEPG.Columns.value:
				EINsession.open(Merlin_PGII, InfoBar_instance.servicelist)
			else:
				EINsession.open(Merlin_PGd, InfoBar_instance.servicelist)
		else:
			EINsession.open(MessageBox, text=_('MerlinEPG is not installed!'), type=MessageBox.TYPE_INFO)
	elif answer == "autotimer":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/AutoTimer/AutoTimerEditor.pyo"):
			from Plugins.Extensions.AutoTimer.plugin import main as AutoTimerView
			AutoTimerView(EINsession)
		else:
			EINsession.open(MessageBox, text=_('Autotimer is not installed!'), type=MessageBox.TYPE_INFO)
	elif answer == "epgsearch":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/EPGSearch/plugin.pyo"):
			from Plugins.Extensions.EPGSearch.EPGSearch import EPGSearch
			service = EINsession.nav.getCurrentService()
			info = service.info()
			epg_event = info.getEvent(0)
			if epg_event:
				epg_name = epg_event and epg_event.getEventName() or ''
				EINsession.open(EPGSearch, epg_name, False)
		else:
			EINsession.open(MessageBox, text=_('EPGsearch is not installed!'), type=MessageBox.TYPE_INFO)
	elif answer == "channelinfo":
		EINsession.open(ServiceInfo, InfoBar_instance.servicelist.getCurrentSelection())
	elif answer == "imdbinfo":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo"):
			from Plugins.Extensions.IMDb.plugin import IMDB
			service = EINsession.nav.getCurrentService()
			info = service.info()
			epg_event = info.getEvent(0)
			if epg_event:
				IeventName = epg_event.getEventName()
				EINsession.open(IMDB, IeventName)
		else:
			EINsession.open(MessageBox, text=_('IMDB is not installed!'), type=MessageBox.TYPE_INFO)
	elif answer == "graphepg":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/GraphMultiEPG/plugin.pyo"):
			from Plugins.Extensions.GraphMultiEPG.plugin import main as gmepgmain
			gmepgmain(EINsession, InfoBar_instance.servicelist)
		else:
			EINsession.open(MessageBox, text=_('GraphMultiEPG is not installed!'), type=MessageBox.TYPE_INFO)
	elif answer == "primetime":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/PrimeTimeManager/plugin.pyo"):
			from Plugins.Extensions.PrimeTimeManager.plugin import main as ptmanmain
			ptmanmain(EINsession)
		else:
			EINsession.open(MessageBox, text=_('Prime Time Manager is not installed!'), type=MessageBox.TYPE_INFO)
	elif answer == "epgrefresh":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/EPGRefresh/plugin.pyo"):
			from Plugins.Extensions.EPGRefresh.plugin import main as epgrefmain
			epgrefmain(EINsession)
		else:
			EINsession.open(MessageBox, text=_('EPGRefresh is not installed!'), type=MessageBox.TYPE_INFO)
	elif answer == "cooltv":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/CoolTVGuide/plugin.pyo"):
			from Plugins.Extensions.CoolTVGuide.plugin import main as ctvmain
			ctvmain(EINsession, InfoBar_instance.servicelist)
		else:
			EINsession.open(MessageBox, text=_('CoolTVGuide is not installed!'), type=MessageBox.TYPE_INFO)
	elif answer == "sysinfo":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Sherlock/plugin.pyo"):
			from Plugins.Extensions.Sherlock.plugin import SherlockII
			EINsession.open(SherlockII)
		else:
			EINsession.open(MessageBox, text=_('Sherlock is not installed!'), type=MessageBox.TYPE_INFO)
	else:
		EINsession.open(MessageBox, text=_('This function is yet not available!'), type=MessageBox.TYPE_INFO)


class EasyEvent(Screen, EventViewBase):
	def __init__(self, session, Event, Ref, callback=None, singleEPGCB=None, multiEPGCB=None):
		Screen.__init__(self, session)
		self.session = session
		self.skinName = "EventView"
		EventViewBase.__init__(self, Event, Ref, callback=InfoBar_instance.eventViewCallback)
		self["key_yellow"].setText(_(getPluginByName(config.plugins.EasyInfo.bEvInYellow.value)))
		self["key_blue"].setText(_(getPluginByName(config.plugins.EasyInfo.bEvInBlue.value)))
		self["key_red"].setText(_("Similar"))
		self["epgactions"] = ActionMap(["EventViewEPGActions", "EPGSelectActions", "EventViewActions"],
			{
				"openSingleServiceEPG": self.singleEPGCB,
				"openMultiServiceEPG": self.multiEPGCB,
				"openSimilarList": self.openSimilarList,
				"info": self.newExit,
				"pageUp": self.pageUp,
				"pageDown": self.pageDown,
				"prevEvent": self.prevEvent,
				"nextEvent": self.nextEvent
			}, -1)

	def openSimilarList(self):
		self.hide()
		EINcallbackFunc("epgsearch")
		self.close()

	def singleEPGCB(self):
		self.hide()
		EINcallbackFunc(config.plugins.EasyInfo.bEvInYellow.value)
		self.close()

	def multiEPGCB(self):
		self.hide()
		EINcallbackFunc(config.plugins.EasyInfo.bEvInBlue.value)
		self.close()

	def setEvent(self, event):
		self.event = event
		if event is None:
			return
		text = event.getEventName()
		short = event.getShortDescription()
		ext = event.getExtendedDescription()
		if short and short != text:
			text += '\n\n' + short
		if ext:
			if text:
				text += '\n\n'
			text += ext
		self.setTitle(event.getEventName())
		self["epg_description"].setText(text)
		self["datetime"].setText(event.getBeginTimeString())
		self["duration"].setText(_("%d min") % (event.getDuration() / 60))
		self["key_red"].setText(_("Similar"))
		serviceref = self.currentService
		eventid = self.event.getEventId()
		refstr = serviceref.ref.toString()
		isRecordEvent = False
		for timer in self.session.nav.RecordTimer.timer_list:
			if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
				isRecordEvent = True
				break
		if isRecordEvent and self.key_green_choice != self.REMOVE_TIMER:
			self["key_green"].setText(_("Remove timer"))
			self.key_green_choice = self.REMOVE_TIMER
		elif not isRecordEvent and self.key_green_choice != self.ADD_TIMER:
			self["key_green"].setText(_("Add timer"))
			self.key_green_choice = self.ADD_TIMER

	def newExit(self):
		self.hide()
		self.session.open(EasyInfo)
		self.close()


class EvNewList(EPGList):
	def __init__(self, type=EPG_TYPE_MULTI, selChangedCB=None, timer=None):
		EPGList.__init__(self, type, selChangedCB, timer)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setItemHeight(50)
		self.l.setBuildFunc(self.buildMultiEntry)
		self.breite = 200
		MyPiconPath = "/"

	def recalcEntrySize(self):
		esize = self.l.getItemSize()
		self.breite = esize.width() - 200

	def buildMultiEntry(self, changecount, service, eventId, beginTime, duration, EventName, nowTime, service_name):
		(clock_pic, rec) = self.getPixmapForEntry(service, eventId, beginTime, duration)
		res = [None]
		sref = str(service)[:-1].replace(':', '_')
		Spixmap = LoadPixmap(path=(config.plugins.EasyInfo.myPicons.value + sref + '.png'))
		if Spixmap is not None:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 5, 4, 70, 42, Spixmap))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 77, 50, 1, RT_HALIGN_CENTER | RT_VALIGN_CENTER | RT_WRAP, service_name))
		if rec:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 80, 16, 21, 21, clock_pic))
		if beginTime is not None and len(EventName) > 60:
			if nowTime < beginTime:
				begin = localtime(beginTime)
				end = localtime(beginTime + duration)
				res.extend((
					(eListboxPythonMultiContent.TYPE_TEXT, 100, 4, 10, 20, 1, RT_HALIGN_RIGHT, '>'),
					(eListboxPythonMultiContent.TYPE_TEXT, 110, 4, 70, 44, 1, RT_HALIGN_LEFT, "%02d.%02d\n%02d.%02d" % (begin[3], begin[4], end[3], end[4])),
					(eListboxPythonMultiContent.TYPE_TEXT, 180, 1, self.breite, 48, 0, RT_HALIGN_LEFT | RT_VALIGN_TOP | RT_WRAP, EventName)
				))
			else:
				percent = (nowTime - beginTime) * 100 / duration
				restzeit = ((beginTime + duration) - nowTime)
				res.extend((
					(eListboxPythonMultiContent.TYPE_PROGRESS, 110, 11, 40, 8, percent),
					(eListboxPythonMultiContent.TYPE_TEXT, 110, 25, 60, 22, 1, RT_HALIGN_LEFT, "+%d:%02d" % (restzeit / 3600, (restzeit / 60) - ((restzeit / 3600) * 60))),
					(eListboxPythonMultiContent.TYPE_TEXT, 180, 1, self.breite, 48, 0, RT_HALIGN_LEFT | RT_VALIGN_TOP | RT_WRAP, EventName)
				))
		elif beginTime is not None:
			if nowTime < beginTime:
				begin = localtime(beginTime)
				end = localtime(beginTime + duration)
				res.extend((
					(eListboxPythonMultiContent.TYPE_TEXT, 100, 4, 10, 20, 1, RT_HALIGN_RIGHT, '>'),
					(eListboxPythonMultiContent.TYPE_TEXT, 110, 4, 70, 44, 1, RT_HALIGN_LEFT, "%02d.%02d\n%02d.%02d" % (begin[3], begin[4], end[3], end[4])),
					(eListboxPythonMultiContent.TYPE_TEXT, 180, 1, self.breite, 48, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, EventName)
				))
			else:
				percent = (nowTime - beginTime) * 100 / duration
				restzeit = ((beginTime + duration) - nowTime)
				res.extend((
					(eListboxPythonMultiContent.TYPE_PROGRESS, 110, 11, 40, 8, percent),
					(eListboxPythonMultiContent.TYPE_TEXT, 110, 25, 60, 22, 1, RT_HALIGN_LEFT, "+%d:%02d" % (restzeit / 3600, (restzeit / 60) - ((restzeit / 3600) * 60))),
					(eListboxPythonMultiContent.TYPE_TEXT, 180, 1, self.breite, 48, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, EventName)
				))
		return res

	def moveToService(self, serviceref):
		if not serviceref:
			return
		index = 0
		refstr = serviceref.toString()
		for x in self.list:
			if x[1] == refstr:
				self.instance.moveSelectionTo(index)
				break
			index += 1
		if x[1] != refstr:
			self.instance.moveSelectionTo(0)


class EasyPG(EPGSelection, Screen):
	if SKINTYPE == 3:
		skin = """
		<screen name="EasyPG" backgroundColor="#101220" flags="wfNoBorder" position="0,0" size="1280,720" title="Easy PG">
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/lines.png" position="60,35" size="660,650" zPosition="-1"/>
			<widget font="Regular;20" position="785,30" render="Label" size="202,25" source="global.CurrentTime" transparent="1" zPosition="1">
				<convert type="ClockToText">Format:%a %d. %b   %H:%M</convert>
			</widget>
			<widget backgroundColor="#ff000000" position="755,125" render="Pig" size="497,280" source="session.VideoPicture" zPosition="1"/>
			<widget foregroundColor="#fcc000" font="Regular;20" name="date" position="755,415" size="100,25" transparent="1"/>
			<widget name="list" position="60,35" scrollbarMode="showNever" size="660,650" transparent="1"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-red.png" position="785,65" size="5,20"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-green.png" position="785,90" size="5,20"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-yellow.png" position="1005,65" size="5,20"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-blue.png" position="1005,90" size="5,20"/>
			<eLabel font="Regular;18" position="800,63" size="150,25" text="Similar" transparent="1"/>
			<eLabel font="Regular;18" position="800,90" size="150,25" text="Timer" transparent="1"/>
			<eLabel font="Regular;18" position="1015,63" size="150,25" text="Back" transparent="1"/>
			<eLabel font="Regular;18" position="1015,90" size="150,25" text="Next" transparent="1"/>
			<widget font="Regular;20" halign="right" position="870,415" render="Label" size="70,25" source="Event" transparent="1" zPosition="1">
				<convert type="EventTime">StartTime</convert>
				<convert type="ClockToText">Default</convert>
			</widget>
			<eLabel font="Regular;18" position="945,415" size="10,25" text="-" transparent="1"/>
			<widget font="Regular;20" position="955,415" render="Label" size="70,25" source="Event" transparent="1" zPosition="1">
				<convert type="EventTime">EndTime</convert>
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget font="Regular;20" position="1050,415" render="Label" size="171,25" source="Event" transparent="1" zPosition="1">
			<convert type="EventTime">Duration</convert>
				<convert type="ClockToText">InMinutes</convert>
			</widget>
			<widget font="Regular;20" position="755,445" render="Label" size="480,25" source="Event" transparent="1" zPosition="2" noWrap="1">
				<convert type="EventName">ShortDescription</convert>
			</widget>
			<widget font="Regular;18" position="755,475" render="Label" size="480,210" source="Event" transparent="1" zPosition="3">
				<convert type="EventName">ExtendedDescription</convert>
			</widget>
		</screen>"""
	elif SKINTYPE == 2:
		skin = """
		<screen name="EasyPG" backgroundColor="#0e1018" flags="wfNoBorder" position="0,0" size="1024,576" title="Easy PG">
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/lines.png" position="50,50" size="520,450" zPosition="-1"/>
			<eLabel backgroundColor="#666666" position="0,518" size="1024,1"/>
			<widget font="Regular;20" position="50,525" render="Label" size="186,25" source="global.CurrentTime" transparent="1" zPosition="1">
				<convert type="ClockToText">Format:%a %d. %b   %H:%M</convert>
			</widget>
			<widget backgroundColor="#ff000000" position="590,30" render="Pig" size="384,216" source="session.VideoPicture" zPosition="-1"/>
			<widget foregroundColor="#fcc000" font="Regular;20" name="date" position="590,255" size="100,25" transparent="1"/>
			<widget name="list" position="50,48" scrollbarMode="showNever" size="520,450" transparent="1"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-red.png" position="275,525" size="5,20"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-green.png" position="450,525" size="5,20"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-yellow.png" position="625,525" size="5,20"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-blue.png" position="800,525" size="5,20"/>
			<eLabel font="Regular;18" position="290,526" size="150,25" text="Similar" transparent="1"/>
			<eLabel font="Regular;18" position="465,526" size="150,25" text="Timer" transparent="1"/>
			<eLabel font="Regular;18" position="640,526" size="150,25" text="Back" transparent="1"/>
			<eLabel font="Regular;18" position="815,526" size="150,25" text="Next" transparent="1"/>
			<widget font="Regular;20" halign="right" position="695,255" render="Label" size="70,25" source="Event" transparent="1" zPosition="1">
				<convert type="EventTime">StartTime</convert>
				<convert type="ClockToText">Default</convert>
			</widget>
			<eLabel font="Regular;18" position="770,255" size="10,25" text="-" transparent="1"/>
			<widget font="Regular;20" position="780,255" render="Label" size="70,25" source="Event" transparent="1" zPosition="1">
				<convert type="EventTime">EndTime</convert>
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget font="Regular;20" position="855,255" render="Label" size="130,25" source="Event" transparent="1" zPosition="1">
			<convert type="EventTime">Duration</convert>
				<convert type="ClockToText">InMinutes</convert>
			</widget>
			<widget font="Regular;20" noWrap="1" position="590,285" render="Label" size="390,25" source="Event" transparent="1" zPosition="2">
				<convert type="EventName">ShortDescription</convert>
			</widget>
			<widget font="Regular;18" position="590,315" render="Label" size="390,190" source="Event" transparent="1" zPosition="3">
				<convert type="EventName">ExtendedDescription</convert>
			</widget>
		</screen>
		"""
	else:
		skin = """
		<screen name="EasyPG" backgroundColor="background" flags="wfNoBorder" position="0,0" size="720,576" title="Easy PG">
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/lines.png" position="50,48" size="620,450" zPosition="-1"/>
			<eLabel backgroundColor="#666666" position="0,522" size="756,1"/>
			<widget foregroundColor="#fcc000" font="Regular;20" name="date" position="50,525" size="100,25" transparent="1"/>
			<widget name="list" position="50,48" scrollbarMode="showOnDemand" size="620,450" transparent="1"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-red.png" position="175,525" size="5,20"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-yellow.png" position="350,525" size="5,20"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-blue.png" position="525,525" size="5,20"/>
			<eLabel font="Regular;18" position="190,526" size="150,25" text="Similar" transparent="1"/>
			<eLabel font="Regular;18" position="365,526" size="150,25" text="Back" transparent="1"/>
			<eLabel font="Regular;18" position="540,526" size="150,25" text="Next" transparent="1"/>
		</screen>
		"""

	def __init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None):
		Screen.__init__(self, session)
		EPGSelection.__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB)
		global EINposition
		EINposition = 0
		allbouq = InfoBar_instance.servicelist.getBouquetList()
		for newpos in range(0, len(allbouq)):
			if InfoBar_instance.servicelist.getRoot() == allbouq[newpos][1]:
				EINposition = newpos
				break
		self.PTinit = False
		self.session = session
		EPGSelection.skinName = "EasyPG"
		self.PThour = config.plugins.EasyInfo.Primetime2.value[0]
		self.PTmin = config.plugins.EasyInfo.Primetime2.value[1]
		self["list"] = EvNewList(type=EPG_TYPE_MULTI, selChangedCB=self.onSelectionChanged, timer=session.nav.RecordTimer)
		self.skinName = "EasyPG"
		self.RefrTimer = eTimer()
		self.RefrTimer.callback.append(self.RefreshEPG)
		self["actions"] = ActionMap(["EPGSelectActions", "OkCancelActions", "NumberActions", "InfobarActions"],
			{
				"cancel": self.closeScreen,
				"ok": self.newOKFunc,
				"timerAdd": self.timerAdd,
				"yellow": self.yellowButtonPressed,
				"blue": self.blueButtonPressed,
				"info": self.infoKeyPressed,
				"red": self.newRedFunc,
				"input_date_time": self.einContextMenu,
				"nextBouquet": self.nextBouquet,
				"prevBouquet": self.prevBouquet,
				"nextService": self.PTfor,
				"prevService": self.PTback,
				"showMovies": self.enterDateTime,
				"showTv": self.zapTo,
				"showRadio": self.zapForRefr,
				"0": self.GoFirst,
				"1": self.SetPT1,
				"2": self.SetPT2,
				"3": self.SetPT3
			}, -1)

	def closeScreen(self):
		self.close(True)

	def GoFirst(self):
		self["list"].fillMultiEPG(self.services, -1)
		self.PTinit = False

	def GoPrimetime(self):
		heute = localtime()
		pt = (heute[0], heute[1], heute[2], self.PThour, self.PTmin, 0, heute[6], heute[7], 0)
		self.ask_time = int(mktime(pt))
		self.PTinit = True
		if self.ask_time > int(mktime(heute)):
			self["list"].fillMultiEPG(self.services, self.ask_time)

	def newOKFunc(self):
		if config.plugins.EasyInfo.epgOKFunc.value == "exitzap":
			self.zapTo()
			self.close(True)
		elif config.plugins.EasyInfo.epgOKFunc.value == "zap":
			self.zapTo()
		else:
			self.infoKeyPressed()

	def newRedFunc(self):
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/EPGSearch/plugin.pyo"):
			from Plugins.Extensions.EPGSearch.EPGSearch import EPGSearch
			epg_event = self["list"].getCurrent()[0]
			if epg_event:
				epg_name = epg_event and epg_event.getEventName() or ''
				self.session.open(EPGSearch, epg_name, False)
		else:
			self.session.open(MessageBox, text=_('EPGsearch is not installed!'), type=MessageBox.TYPE_INFO)

	def PTfor(self):
		if not self["list"].getCurrent()[0]:
			return
		heute = localtime()
		if not self.PTinit:
			pt = (heute[0], heute[1], heute[2], self.PThour, self.PTmin, 0, heute[6], heute[7], 0)
			self.ask_time = int(mktime(pt))
			self.PTinit = True
			if self.ask_time < int(mktime(heute)):
				self.ask_time = self.ask_time + 86400
		else:
			self.ask_time = self.ask_time + 86400
		self["list"].fillMultiEPG(self.services, self.ask_time)

	def PTback(self):
		heute = localtime()
		if not self.PTinit:
			pt = (heute[0], heute[1], heute[2], self.PThour, self.PTmin, 0, heute[6], heute[7], 0)
			self.ask_time = int(mktime(pt))
			self.PTinit = True
		else:
			self.ask_time = self.ask_time - 86400
		if self.ask_time > int(mktime(heute)):
			self["list"].fillMultiEPG(self.services, self.ask_time)
		else:
			self["list"].fillMultiEPG(self.services, -1)
			self.PTinit = False

	def SetPT1(self):
		self.PThour = config.plugins.EasyInfo.Primetime1.value[0]
		self.PTmin = config.plugins.EasyInfo.Primetime1.value[1]
		self.GoPrimetime()

	def SetPT2(self):
		self.PThour = config.plugins.EasyInfo.Primetime2.value[0]
		self.PTmin = config.plugins.EasyInfo.Primetime2.value[1]
		self.GoPrimetime()

	def SetPT3(self):
		self.PThour = config.plugins.EasyInfo.Primetime3.value[0]
		self.PTmin = config.plugins.EasyInfo.Primetime3.value[1]
		self.GoPrimetime()

	def einContextMenu(self):
		self.session.open(ConfigEasyInfo)

	def zapForRefr(self):
		self.zapTo()
		self.RefrTimer.start(4000, True)

	def RefreshEPG(self):
		self.RefrTimer.stop()
		self.GoFirst()


class ESListNext(EPGList):
	def __init__(self, type=EPG_TYPE_MULTI, selChangedCB=None, timer=None):
		EPGList.__init__(self, type, selChangedCB, timer)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setItemHeight(50)
		self.l.setBuildFunc(self.buildMultiEntry)
		self.breite = 200
		MyPiconPath = "/"

	def recalcEntrySize(self):
		esize = self.l.getItemSize()
		self.breite = esize.width() - 100

	def buildMultiEntry(self, changecount, service, eventId, beginTime, duration, EventName, nowTime, service_name):
		(clock_pic, rec) = self.getPixmapForEntry(service, eventId, beginTime, duration)
		res = [None]
		if rec:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 58, 16, 21, 21, clock_pic))
		if beginTime is not None and len(EventName) > 60:
			if nowTime < beginTime:
				begin = localtime(beginTime)
				end = localtime(beginTime + duration)
				res.extend((
					(eListboxPythonMultiContent.TYPE_TEXT, 0, 4, 10, 20, 1, RT_HALIGN_RIGHT, '>'),
					(eListboxPythonMultiContent.TYPE_TEXT, 10, 4, 70, 44, 1, RT_HALIGN_LEFT, "%02d.%02d\n%02d.%02d" % (begin[3], begin[4], end[3], end[4])),
					(eListboxPythonMultiContent.TYPE_TEXT, 80, 1, self.breite, 48, 0, RT_HALIGN_LEFT | RT_VALIGN_TOP | RT_WRAP, EventName)
				))
			else:
				percent = (nowTime - beginTime) * 100 / duration
				restzeit = ((beginTime + duration) - nowTime)
				res.extend((
					(eListboxPythonMultiContent.TYPE_PROGRESS, 10, 11, 40, 8, percent),
					(eListboxPythonMultiContent.TYPE_TEXT, 10, 25, 60, 22, 1, RT_HALIGN_LEFT, "+%d:%02d" % (restzeit / 3600, (restzeit / 60) - ((restzeit / 3600) * 60))),
					(eListboxPythonMultiContent.TYPE_TEXT, 80, 1, self.breite, 48, 0, RT_HALIGN_LEFT | RT_VALIGN_TOP | RT_WRAP, EventName)
				))
		elif beginTime is not None:
			if nowTime < beginTime:
				begin = localtime(beginTime)
				end = localtime(beginTime + duration)
				res.extend((
					(eListboxPythonMultiContent.TYPE_TEXT, 0, 4, 10, 20, 1, RT_HALIGN_RIGHT, '>'),
					(eListboxPythonMultiContent.TYPE_TEXT, 10, 4, 70, 44, 1, RT_HALIGN_LEFT, "%02d.%02d\n%02d.%02d" % (begin[3], begin[4], end[3], end[4])),
					(eListboxPythonMultiContent.TYPE_TEXT, 80, 1, self.breite, 48, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, EventName)
				))
			else:
				percent = (nowTime - beginTime) * 100 / duration
				restzeit = ((beginTime + duration) - nowTime)
				res.extend((
					(eListboxPythonMultiContent.TYPE_PROGRESS, 10, 11, 40, 8, percent),
					(eListboxPythonMultiContent.TYPE_TEXT, 10, 25, 60, 22, 1, RT_HALIGN_LEFT, "+%d:%02d" % (restzeit / 3600, (restzeit / 60) - ((restzeit / 3600) * 60))),
					(eListboxPythonMultiContent.TYPE_TEXT, 80, 1, self.breite, 48, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, EventName)
				))
		return res

	def moveToService(self, serviceref):
		if not serviceref:
			return
		index = 0
		refstr = serviceref.toString()
		for x in self.list:
			if x[1] == refstr:
				self.instance.moveSelectionTo(index)
				break
			index += 1
		if x[1] != refstr:
			self.instance.moveSelectionTo(0)


class EasySelection(EPGSelection, Screen):
	if SKINTYPE == 3:
		skin = """
		<screen name="EasySelection" backgroundColor="background" flags="wfNoBorder" position="0,0" size="1280,720" title="Easy Selection">
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/lines.png" position="60,35" size="660,650" zPosition="-1"/>
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/lines.png" position="720,35" size="500,650" zPosition="-1"/>
			<widget name="list" position="60,35" scrollbarMode="showNever" size="660,650" transparent="1"/>
			<widget name="listN" position="720,35" scrollbarMode="showNever" size="500,650" transparent="1"/>
		</screen>"""
	elif SKINTYPE == 2:
		skin = """
		<screen name="EasySelection" backgroundColor="background" flags="wfNoBorder" position="0,0" size="1024,576" title="Easy Selection">
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/lines.png" position="40,38" size="660,500" zPosition="-1"/>
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/lines.png" position="700,38" size="284,500" zPosition="-1"/>
			<widget name="list" position="40,38" scrollbarMode="showNever" size="520,500" transparent="1"/>
			<widget name="listN" position="560,38" scrollbarMode="showNever" size="444,500" transparent="1"/>
		</screen>
		"""
	else:
		skin = """
		<screen name="EasySelection" backgroundColor="background" flags="wfNoBorder" position="0,0" size="720,576" title="Easy Selection">
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/lines.png" position="50,38" size="620,500" zPosition="-1"/>
			<widget name="list" position="50,38" scrollbarMode="showOnDemand" size="620,500" transparent="1"/>
		</screen>
		"""

	def __init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None):
		Screen.__init__(self, session)
		EPGSelection.__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB)
		global EINposition
		EINposition = 0
		allbouq = InfoBar_instance.servicelist.getBouquetList()
		for newpos in range(0, len(allbouq)):
			if InfoBar_instance.servicelist.getRoot() == allbouq[newpos][1]:
				EINposition = newpos
				break
		self.session = session
		EPGSelection.skinName = "EasySelection"
		self["list"] = EvNewList(type=EPG_TYPE_MULTI, selChangedCB=self.onSelectionChanged, timer=session.nav.RecordTimer)
		self["listN"] = ESListNext(type=EPG_TYPE_MULTI, selChangedCB=self.onSelectionChanged, timer=session.nav.RecordTimer)
		self.skinName = "EasySelection"
		self["actions"] = ActionMap(["EPGSelectActions", "OkCancelActions", "DirectionActions"],
			{
				"cancel": self.closeScreen,
				"ok": self.newOKFunc,
				"info": self.infoKeyPressed,
				"nextBouquet": self.nextBouquet,
				"prevBouquet": self.prevBouquet,
				"right": self.right,
				"rightRepeated": self.right,
				"left": self.left,
				"leftRepeated": self.left,
				"up": self.up,
				"upRepeated": self.up,
				"down": self.down,
				"downRepeated": self.down,
				"nextService": self.PrimeTimeLook,
				"prevService": self.NowNextLook
			}, -1)
		self.onLayoutFinish.append(self.byLayoutEnd)

	def byLayoutEnd(self):
		self["listN"].recalcEntrySize()
		self["listN"].fillMultiEPG(self.services, -1)
		self["listN"].moveToService(self.session.nav.getCurrentlyPlayingServiceReference())
		self["listN"].updateMultiEPG(1)

	def closeScreen(self):
		self.close(True)

	def newOKFunc(self):
		self.zapTo()
		self.close(True)

	def left(self):
		self["list"].instance.moveSelection(self["list"].instance.pageUp)
		self["listN"].instance.moveSelection(self["list"].instance.pageUp)

	def right(self):
		self["list"].instance.moveSelection(self["list"].instance.pageDown)
		self["listN"].instance.moveSelection(self["list"].instance.pageDown)

	def up(self):
		self["list"].moveUp()
		self["listN"].moveUp()

	def down(self):
		self["list"].moveDown()
		self["listN"].moveDown()

	def nextBouquet(self):
		if self.bouquetChangeCB:
			self.bouquetChangeCB(1, self)
			self.byLayoutEnd()

	def prevBouquet(self):
		if self.bouquetChangeCB:
			self.bouquetChangeCB(-1, self)
			self.byLayoutEnd()

	def PrimeTimeLook(self):
		heute = localtime()
		pt = (heute[0], heute[1], heute[2], config.plugins.EasyInfo.Primetime2.value[0], config.plugins.EasyInfo.Primetime2.value[1], 0, heute[6], heute[7], 0)
		ask_time = int(mktime(pt))
		if ask_time > int(mktime(heute)):
			self["list"].fillMultiEPG(self.services, ask_time)
			pt = (heute[0], heute[1], heute[2], config.plugins.EasyInfo.Primetime3.value[0], config.plugins.EasyInfo.Primetime3.value[1], 0, heute[6], heute[7], 0)
			ask_time = int(mktime(pt))
			self["listN"].fillMultiEPG(self.services, ask_time)

	def NowNextLook(self):
		self["list"].fillMultiEPG(self.services, -1)
		self["listN"].fillMultiEPG(self.services, -1)
		self["listN"].updateMultiEPG(1)

	def infoKeyPressed(self):
		cur = self["list"].getCurrent()
		service = cur[1].ref.toString()
		ref = eServiceReference(service)
		if ref:
			InfoBar_instance.servicelist.savedService = ref
			self.session.openWithCallback(InfoBar_instance.servicelist.SingleServiceEPGClosed, EPGSelection, ref, serviceChangeCB=InfoBar_instance.servicelist.changeServiceCB)
