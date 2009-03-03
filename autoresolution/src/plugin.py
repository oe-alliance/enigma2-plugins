from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSelection, ConfigSubsection, ConfigYesNo
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from enigma import iPlayableService, iServiceInformation, eTimer
from Plugins.Plugin import PluginDescriptor

# depends on Videomode Plugin
from Plugins.SystemPlugins.Videomode.VideoHardware import video_hw

session = [ ]

default = (config.av.videomode[config.av.videoport.value].value, _("default"))
preferedmodes = [mode[0] for mode in video_hw.getModeList(config.av.videoport.value) if mode[0] != default[0]]
preferedmodes.append(default)

config.plugins.autoresolution = ConfigSubsection()
config.plugins.autoresolution.enable = ConfigYesNo(default = False)
config.plugins.autoresolution.sd_i = ConfigSelection(default = default[0], choices = preferedmodes)
config.plugins.autoresolution.sd_p = ConfigSelection(default = default[0], choices = preferedmodes)
config.plugins.autoresolution.hd_i = ConfigSelection(default = default[0], choices = preferedmodes)
config.plugins.autoresolution.hd_p = ConfigSelection(default = default[0], choices = preferedmodes)
config.plugins.autoresolution.p1080_24 = ConfigSelection(default = default[0], choices = ['1080p24'] + preferedmodes)
config.plugins.autoresolution.p1080_25 = ConfigSelection(default = default[0], choices = ['1080p25'] + preferedmodes)
config.plugins.autoresolution.p1080_30 = ConfigSelection(default = default[0], choices = ['1080p30'] + preferedmodes)
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
	dic = { '1080p24': config.plugins.autoresolution.p1080_24.value, \
		'1080p25': config.plugins.autoresolution.p1080_25.value, \
		'1080p30': config.plugins.autoresolution.p1080_30.value, \
		'sd_i':config.plugins.autoresolution.sd_i.value, \
		'sd_p':config.plugins.autoresolution.sd_p.value, \
		'hd_i':config.plugins.autoresolution.hd_i.value, \
		'hd_p':config.plugins.autoresolution.hd_p.value }
	return dic

switchdic = build_switchdic()

frqdic = { 23976: '24', \
	   24000: '24', \
	   25000: '25', \
	   29970: '30', \
	   30000: '30', \
	   50000: '50', \
	   59940: '60', \
	   60000: '60'}

progrdic = { 0: 'i', 1: 'p'}

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
			self.list.append(getConfigListEntry(_("SD Interlace Mode"), config.plugins.autoresolution.sd_i))
			self.list.append(getConfigListEntry(_("SD Progressive Mode"), config.plugins.autoresolution.sd_p))
			self.list.append(getConfigListEntry(_("HD Interlace Mode"), config.plugins.autoresolution.hd_i))
			self.list.append(getConfigListEntry(_("HD Progressive Mode"), config.plugins.autoresolution.hd_p))
			self.list.append(getConfigListEntry(_("Enable 1080p24 Mode"), config.plugins.autoresolution.p1080_24))
			self.list.append(getConfigListEntry(_("Enable 1080p25 Mode"), config.plugins.autoresolution.p1080_25))
			self.list.append(getConfigListEntry(_("Enable 1080p30 Mode"), config.plugins.autoresolution.p1080_30))
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
				iPlayableService.evVideoFramerateChanged: self.__evVideoFramerateChanged
			})
		self.timer = eTimer()
		self.timer.callback.append(self.determineContent)
		self.delayval = 250
		self.lastmode = config.av.videomode[config.av.videoport.value].value

	def __evVideoFramerateChanged(self):
		print "[AutoRes] got event evFramerateChanged"
		if self.timer.isActive():
			self.timer.stop()
		if config.plugins.autoresolution.enable.value:
			self.timer.start(self.delayval)

	def __evVideoSizeChanged(self):
		print "[AutoRes] got event evVideoSizeChanged"
		if self.timer.isActive():
			self.timer.stop()
		if config.plugins.autoresolution.enable.value:
			self.timer.start(self.delayval)
	
	def __evVideoProgressiveChanged(self):
		print "[AutoRes] got event evVideoProgressiveChanged"
		if self.timer.isActive():
			self.timer.stop()
		if config.plugins.autoresolution.enable.value:
			self.timer.start(self.delayval)
			
	def determineContent(self):
		self.timer.stop()
		service = session.nav.getCurrentService()
		info = service and service.info()
		height = info and info.getInfo(iServiceInformation.sVideoHeight)
		width = info and info.getInfo(iServiceInformation.sVideoWidth)
		framerate = info and info.getInfo(iServiceInformation.sFrameRate)
		frate = str(framerate)[:2] #fallback?
		if frqdic.has_key(framerate):
			frate = frqdic[framerate]
		progressive = info and info.getInfo(iServiceInformation.sProgressive)
		if progrdic.has_key(progressive):
			prog = progrdic[progressive]
		else:
			prog = 'i'
		print "[AutoRes] new content is %sx%s%s%s" %(width, height, prog, frate)
		self.determineVideoMode(width, height, prog, frate)
	
	def determineVideoMode(self, width, height, prog, frate):
		if (height >= 900 or width >= 1600) and frate in ('24', '25', '30') and prog == 'p':
			new_mode = '1080p%s' % frate
		elif height > 576 or width > 720: #asume that, higher then 576 or greater then 720 is hd content
			new_mode = 'hd_%s' % prog
		else:
			new_mode = 'sd_%s' % prog
		if switchdic.has_key(new_mode):
			new_mode = switchdic[new_mode]
			print '[AutoRes] determined VideoMode', new_mode
			if new_mode != self.lastmode:
				self.lastmode = new_mode
				self.changeVideomode(new_mode)
		
	def changeVideomode(self, mode):
		if mode.find("1080p") != -1:
			print "[AutoRes] switching to", mode
			v = open('/proc/stb/video/videomode' , "w")
			v.write("%s\n" % mode)
			v.close()
			resolutionlabeltxt = mode
		else:
			port = config.av.videoport.value
			rate = config.av.videorate[mode].value
			print "[AutoRes] switching to %s %s %s" % (port, mode, rate)
			video_hw.setMode(port, mode, rate)
			resolutionlabeltxt = '%s %s %s' % (port, mode, rate)
		if config.plugins.autoresolution.showinfo.value:
			resolutionlabel["restxt"].setText(resolutionlabeltxt)
			resolutionlabel.show()
		if config.plugins.autoresolution.testmode.value:
			from Screens.MessageBox import MessageBox
			self.session.openWithCallback(
				self.confirm, MessageBox, _("Autoresolution Plugin Testmode:\nIs %s videomode ok?" % (resolutionlabeltxt)), MessageBox.TYPE_YESNO, timeout = 15, default = False)
		
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
	return [("Autoresolution...", autoresSetup, "autores_setup", 45)]

def autoresSetup(session, **kwargs):
	session.open(AutoResSetupMenu)

def Plugins(path, **kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart), \
		PluginDescriptor(name="Autoresolution", description=_("Autoresolution Switch"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup) ]
