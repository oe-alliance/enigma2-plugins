from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSelection, ConfigSubsection, ConfigYesNo
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from enigma import iPlayableService, iServiceInformation, eTimer
from ServiceReference import ServiceReference
from Plugins.Plugin import PluginDescriptor
import string
# depends on Videomode Plugin
from Plugins.SystemPlugins.Videomode.VideoHardware import video_hw

session = [ ]

preferedmodes = [mode[0] for mode in video_hw.getModeList(config.av.videoport.value)]
default = config.av.videomode[config.av.videoport.value].value
config.plugins.autoresolution = ConfigSubsection()
config.plugins.autoresolution.enable = ConfigYesNo(default = False)
config.plugins.autoresolution.i1080 = ConfigSelection(default = default, choices = preferedmodes)
#config.plugins.autoresolution.p1080 = ConfigSelection(default = default, choices = preferedmodes)
config.plugins.autoresolution.i576 = ConfigSelection(default = default, choices = preferedmodes)
config.plugins.autoresolution.p576 = ConfigSelection(default = default, choices = preferedmodes)
#config.plugins.autoresolution.i720 = ConfigSelection(default = default, choices = preferedmodes)
config.plugins.autoresolution.p720 = ConfigSelection(default = default, choices = preferedmodes)
config.plugins.autoresolution.i480 = ConfigSelection(default = default, choices = preferedmodes)
config.plugins.autoresolution.p480 = ConfigSelection(default = default, choices = preferedmodes)
config.plugins.autoresolution.showinfo = ConfigYesNo(default = True)
config.plugins.autoresolution.testmode = ConfigYesNo(default = False)
config.plugins.autoresolution.deinterlacer = ConfigSelection(default = "auto", choices =
		[("auto", _("auto")), ("off", _("off")), ("on", _("on"))])
def setDeinterlacer(configElement):
	mode = config.plugins.autoresolution.deinterlacer.value
	print "[AutoRes] switch deinterlacer mode to %s" % mode
	f = open('/proc/stb/vmpeg/deinterlace' , "w")
	f.write("%s\n" % mode)
	f.close()
config.plugins.autoresolution.deinterlacer.addNotifier(setDeinterlacer)

def build_switchdic():
	dic = { '1080i': config.plugins.autoresolution.i1080.value, \
#		'1080p': config.plugins.autoresolution.p1080.value, \
		'576i':config.plugins.autoresolution.i576.value, \
		'576p':config.plugins.autoresolution.p576.value, \
		'480i':config.plugins.autoresolution.i480.value, \
		'480p':config.plugins.autoresolution.p480.value, \
#		'720i':config.plugins.autoresolution.i720.value, \
		'720p':config.plugins.autoresolution.p720.value}
	return dic
switchdic = build_switchdic()


class AutoResSetupMenu(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "Setup"
		self.setup_title = "Autoresolution Videomode Setup"

		self.onChangedEntry = [ ]
		self.list = [ ]
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)

		self["actions"] = ActionMap(["SetupActions"], 
			{
				"cancel": self.keyCancel,
				"save": self.apply,
			}, -2)

		self["title"] = Label(_("Autoresolution Settings"))

		self["oktext"] = Label(_("OK"))
		self["canceltext"] = Label(_("Cancel"))

		self["ok"] = Pixmap()
		self["cancel"] = Pixmap()
		
		self.createSetup()
		
	def createSetup(self):
		self.list = []
		self.list.append(getConfigListEntry(_("Enable Autoresolution"), config.plugins.autoresolution.enable))
		if config.plugins.autoresolution.enable.value:
			self.list.append(getConfigListEntry(_("%s Content" % "1080i"), config.plugins.autoresolution.i1080))
#			self.list.append(getConfigListEntry(_("%s Content" % "1080p"), config.plugins.autoresolution.p1080))
#			self.list.append(getConfigListEntry(_("%s Content" % "720i"), config.plugins.autoresolution.i720))
			self.list.append(getConfigListEntry(_("720p Content"), config.plugins.autoresolution.p720))
			self.list.append(getConfigListEntry(_("576i Content"), config.plugins.autoresolution.i576))
			self.list.append(getConfigListEntry(_("576p Content"), config.plugins.autoresolution.p576))
			self.list.append(getConfigListEntry(_("480p Content"), config.plugins.autoresolution.p480))
			self.list.append(getConfigListEntry(_("480i Content"), config.plugins.autoresolution.i480))
			self.list.append(getConfigListEntry(_("Show Info Screen"), config.plugins.autoresolution.showinfo))
			self.list.append(getConfigListEntry(_("Running in Testmode"), config.plugins.autoresolution.testmode))
		self.list.append(getConfigListEntry(_("Deinterlacer Mode"), config.plugins.autoresolution.deinterlacer))
		self["config"].list = self.list
		self["config"].setList(self.list)
	
	def apply(self):
		for x in self["config"].list:
			x[1].save()
			global switchdic
			switchdic = build_switchdic()
		self.close()
	
	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()
	
	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary
	

class AutoRes(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
			{
				iPlayableService.evVideoSizeChanged: self.__evVideoSizeChanged,
				iPlayableService.evVideoProgressiveChanged: self.__evVideoProgressiveChanged,
			})
		
		self.height, self.progressive = '','i'
		
	def __evVideoSizeChanged(self):
		print "[AutoRes] got event evVideoSizeChanged"
		if config.plugins.autoresolution.enable.value:
			service = self.session.nav.getCurrentService()
			info = service and service.info()
			height = info and info.getInfo(iServiceInformation.sVideoHeight)
			if height != self.height:
				self.height = height
				self.changeVideomode()
	
	def __evVideoProgressiveChanged(self):
		print "[AutoRes] got event evVideoProgressiveChanged"
		prog = 'i'
		if config.plugins.autoresolution.enable.value:
			service = self.session.nav.getCurrentService()
			info = service and service.info()
			progressive = info and info.getInfo(iServiceInformation.sProgressive)
			if progressive == 1:
				prog = 'p'
			if prog != self.progressive:
				self.progressive = prog
				self.changeVideomode()
					       
	def changeVideomode(self):
		content_mode = "%s%s" %(self.height, self.progressive)
		print "[AutoRes] new content is %s%s" %(self.height, self.progressive)
		if switchdic.has_key(content_mode):
			if switchdic[content_mode] in preferedmodes:
				port = config.av.videoport.value
				mode = switchdic[content_mode]
				rate = config.av.videorate[mode].value
				print "[AutoRes] switching to %s %s %s" % (port, mode, rate)
				if config.plugins.autoresolution.showinfo.value:
					resolutionlabel["restxt"].setText("%s %s %s" % (port, mode, rate))
					resolutionlabel.show()
		
				video_hw.setMode(port, mode, rate)
						
				if config.plugins.autoresolution.testmode.value:
					from Screens.MessageBox import MessageBox
					self.session.openWithCallback(
							self.confirm, MessageBox, _("Autoresolution Plugin Testmode:\nIs %s %s %s videomode ok?" % ((port, mode, rate))), MessageBox.TYPE_YESNO, timeout = 15, default = False)
			else:
				print '[AutoRes] TV dont support %s' % switchdic[self.height]

	def confirm(self, confirmed):
		if not confirmed:
			port = config.av.videoport.value
			mode = config.av.videomode[port].value
			rate = config.av.videorate[mode].value
			if config.plugins.autoresolution.showinfo.value:
				resolutionlabel["restxt"].setText("%s %s %s" % (port, mode, rate))
				resolutionlabel.show()
			video_hw.setMode(port, mode, rate)


class ResolutionLabel(Screen):
	skin = """
		<screen position="50,30" size="140,20" flags="wfNoBorder" >
			<widget name="restxt" position="0,0" size="140,20" font="Regular;18" />
		</screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)
		
		from Components.Label import Label
		self["restxt"] = Label()
		
		self.hideTimer = eTimer()
		self.hideTimer.callback.append(self.hide)
		
		self.onShow.append(self.hide_me)
	
	def hide_me(self):
		self.hideTimer.start(config.usage.infobar_timeout.index * 1000, True)

	
def autostart(reason, **kwargs):
	global session, resolutionlabel
	if "session" in kwargs:
		session = kwargs["session"]
		resolutionlabel = session.instantiateDialog(ResolutionLabel)
		AutoRes(session)

def startSetup(menuid):
	if menuid != "system": 
		return [ ]
	return [(_("Autoresolution") + "...", autoresSetup, "autores_setup", 45)]

def autoresSetup(session, **kwargs):
	session.open(AutoResSetupMenu)

def Plugins(path, **kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart), \
		PluginDescriptor(name=_("Autoresolution"), description=_("Autoresolution Switch"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup) ]
