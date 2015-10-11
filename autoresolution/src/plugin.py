from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Screens.MessageBox import MessageBox
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import config, configfile, getConfigListEntry, ConfigSelection, ConfigSubsection, ConfigYesNo, ConfigSubDict, ConfigNothing
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap,MultiPixmap
from Screens.VirtualKeyBoard import VirtualKeyBoard
from enigma import iPlayableService, iServiceInformation, eTimer
from Plugins.Plugin import PluginDescriptor
try:
	from Components.AVSwitch import iAVSwitch as video_hw
except:
	from Plugins.SystemPlugins.Videomode.VideoHardware import video_hw # depends on Videomode Plugin
from Components.Sources.Boolean import Boolean

from boxbranding import getImageDistro

# for localized messages
from . import _

usable = False
preferedmodes = None
default = None
port = None
videoresolution_dictionary = {}
resolutionlabel = None

resolutions = (('sd_i_50', (_("SD 25/50HZ Interlace Mode"))), ('sd_i_60', (_("SD 30/60HZ Interlace Mode"))), \
			('sd_p_24', (_("SD 24HZ Progressive mode"))), \
			('sd_p_50', (_("SD 25/50HZ Progressive Mode"))), ('sd_p_60', (_("SD 30/60HZ Progressive Mode"))), \
			('hd_i', (_("HD Interlace Mode"))), ('hd_p', (_("HD Progressive Mode"))), \
			('p720_24', (_("Enable 720p24 Mode"))), ('p1080_24', (_("Enable 1080p24 Mode"))), \
			('p1080_25', (_("Enable 1080p25 Mode"))), ('p1080_30', (_("Enable 1080p30 Mode"))))

config.plugins.autoresolution = ConfigSubsection()
config.plugins.autoresolution.enable = ConfigYesNo(default = False)
config.plugins.autoresolution.showinfo = ConfigYesNo(default = True)
config.plugins.autoresolution.testmode = ConfigYesNo(default = False)
config.plugins.autoresolution.deinterlacer = ConfigSelection(default = "auto", choices =
		[("off", _("off")), ("auto", _("auto")), ("on", _("on")), ("bob", _("bob"))])
config.plugins.autoresolution.deinterlacer_progressive = ConfigSelection(default = "auto", choices =
		[("off", _("off")), ("auto", _("auto")), ("on", _("on")), ("bob", _("bob"))])
config.plugins.autoresolution.delay_switch_mode = ConfigSelection(default = "1000", choices = [
		("50", "0.05 " + _("seconds")), ("500", "0.5 " + _("seconds")),
		("1000", "1 " + _("second")), ("2000", "2 " + _("seconds")), ("3000", "3 " + _("seconds")),
		("4000", "4 " + _("seconds")), ("5000", "5 " + _("seconds")), ("6000", "6 " + _("seconds")), ("7000", "7 " + _("seconds")),
		("8000", "8 " + _("seconds")), ("9000", "9 " + _("seconds")), ("10000", "10 " + _("seconds")),("60000", "60 " + _("seconds"))])

def setDeinterlacer(mode):
	print "[AutoRes] switch deinterlacer mode to %s" % mode
	try:
		f = open('/proc/stb/vmpeg/deinterlace' , "w")
		f.write("%s\n" % mode)
		f.close()
	except:
		pass

frqdic = { 23976: '24', \
		24000: '24', \
		25000: '25', \
		29970: '30', \
		30000: '30', \
		50000: '50', \
		59940: '60', \
		60000: '60'}

class AutoRes(Screen):
	def __init__(self, session):
		global port
		Screen.__init__(self, session)
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
			{
				iPlayableService.evVideoSizeChanged: self.__evVideoSizeChanged,
				iPlayableService.evVideoProgressiveChanged: self.__evVideoProgressiveChanged,
				iPlayableService.evVideoFramerateChanged: self.__evVideoFramerateChanged,
				iPlayableService.evUpdatedInfo: self.__evUpdatedInfo,
				iPlayableService.evStart: self.__evStart
			})
		self.timer = eTimer()
		self.timer.callback.append(self.determineContent)
		if config.av.videoport.value in config.av.videomode:
			self.lastmode = config.av.videomode[config.av.videoport.value].value
		config.av.videoport.addNotifier(self.defaultModeChanged)
		config.plugins.autoresolution.enable.addNotifier(self.enableChanged, initial_call = False)
		config.plugins.autoresolution.deinterlacer.addNotifier(self.enableChanged, initial_call = False)
		config.plugins.autoresolution.deinterlacer_progressive.addNotifier(self.enableChanged, initial_call = False)
		if default:
			self.setMode(default[0], False)
		self.after_switch_delay = False
		self.newService = False
		if "720p" in config.av.videorate:
			config.av.videorate["720p"].addNotifier(self.__videorate_720p_changed, initial_call = False, immediate_feedback = False)
		if "1080i" in config.av.videorate:
			config.av.videorate["1080i"].addNotifier(self.__videorate_1080i_changed, initial_call = False, immediate_feedback = False)

	def __videorate_720p_changed(self, configEntry):
		if self.lastmode == "720p":
			self.changeVideomode()

	def __videorate_1080i_changed(self, configEntry):
		if self.lastmode == "1080i":
			self.changeVideomode()

	def __evStart(self):
		self.newService = True

	def __evUpdatedInfo(self):
		if self.newService:
			print "[AutoRes] service changed"
			self.after_switch_delay = False
			if int(config.plugins.autoresolution.delay_switch_mode.value) > 0:
				self.timer.start(int(config.plugins.autoresolution.delay_switch_mode.value))
			else:
				self.determineContent()
			self.newService = False

	def defaultModeChanged(self, configEntry):
		global preferedmodes
		global port
		global default
		global usable
		port_changed = configEntry == config.av.videoport
		if port_changed:
			print "port changed to", configEntry.value
			if port:
				config.av.videomode[port].notifiers.remove(self.defaultModeChanged)
			port = config.av.videoport.value
			if port in config.av.videomode:
				config.av.videomode[port].addNotifier(self.defaultModeChanged)
			usable = config.plugins.autoresolution.enable.value and not port in ('DVI-PC', 'Scart')
		else: # videomode changed in normal av setup
			global videoresolution_dictionary
			print "mode changed to", configEntry.value
			default = (configEntry.value, _("default"))
			preferedmodes = [mode[0] for mode in video_hw.getModeList(port) if mode[0] != default[0]]
			preferedmodes.append(default)
			print "default", default
			print "preferedmodes", preferedmodes
			videoresolution_dictionary = {}
			config.plugins.autoresolution.videoresolution = ConfigSubDict()
			for mode in resolutions:
				choices = ['1080p24', '1080p25', '1080p30'] + preferedmodes
				config.plugins.autoresolution.videoresolution[mode[0]] = ConfigSelection(default = default[0], choices = choices)
				config.plugins.autoresolution.videoresolution[mode[0]].addNotifier(self.modeConfigChanged, initial_call = False, immediate_feedback = False)
				videoresolution_dictionary[mode[0]] = (config.plugins.autoresolution.videoresolution[mode[0]])

	def modeConfigChanged(self, configElement):
		self.determineContent()

	def enableChanged(self, configElement):
		global usable
		if configElement.value:
			usable = not port in ('DVI-PC', 'Scart')
			self.determineContent()
		else:
			usable = False
			self.changeVideomode()

	def __evVideoFramerateChanged(self):
		print "[AutoRes] got event evFramerateChanged"
		if not self.timer.isActive() or self.after_switch_delay:
			self.timer.start(100) # give other pending events a chance..

	def __evVideoSizeChanged(self):
		print "[AutoRes] got event evVideoSizeChanged"
		if not self.timer.isActive() or self.after_switch_delay:
			self.timer.start(100) # give other pending events a chance..

	def __evVideoProgressiveChanged(self):
		print "[AutoRes] got event evVideoProgressiveChanged"
		if not self.timer.isActive() or self.after_switch_delay:
			self.timer.start(100) # give other pending events a chance..

	def determineContent(self):
		print "[AutoRes] determineContent"
		self.timer.stop()
		self.after_switch_delay = True
		if usable:
			service = self.session.nav.getCurrentService()
			info = service and service.info()
			height = info and info.getInfo(iServiceInformation.sVideoHeight)
			width = info and info.getInfo(iServiceInformation.sVideoWidth)
			framerate = info and info.getInfo(iServiceInformation.sFrameRate)
			if height != -1 and width != -1 and framerate != -1:
				frate = str(framerate)[:2] #fallback?
				if frqdic.has_key(framerate):
					frate = frqdic[framerate]
				progressive = info and info.getInfo(iServiceInformation.sProgressive)

				prog = progressive == 1 and 'p' or 'i'

				if frate in ('24'):	# 1080p24 content
					new_mode = 'p1080_24'
				elif (height >= 900 or width >= 1600) and frate in ('24', '25', '30') and prog == 'p': 	# 1080p content
					new_mode = 'p1080_%s' % frate
				elif (height > 576 or width > 720) and frate == '24' and prog == 'p': 		# 720p24 detection
					new_mode = 'p720_24'
				elif (height <= 576) and (width <= 720) and frate in ('25', '50'):
					new_mode = 'sd_%s_50' % prog
				elif (height <= 480) and (width <= 720) and frate in ('24', '30', '60'):
					new_mode = 'sd_%s_60' % prog
				else:
					new_mode = 'hd_%s' % prog

				if progressive == 1:
					setDeinterlacer(config.plugins.autoresolution.deinterlacer_progressive.value)
				else:
					setDeinterlacer(config.plugins.autoresolution.deinterlacer.value)

				print "[AutoRes] new content is %sx%s%s%s" %(width, height, prog, frate)

				if videoresolution_dictionary.has_key(new_mode):
					new_mode = videoresolution_dictionary[new_mode].value
					print '[AutoRes] determined videomode', new_mode
					old = resolutionlabel["content"].getText()
					resolutionlabel["content"].setText("Videocontent: %sx%s%s %sHZ" % (width, height, prog, frate))
					if self.lastmode != new_mode:
						self.lastmode = new_mode
						self.changeVideomode()
					elif old != resolutionlabel["content"].getText() and config.plugins.autoresolution.showinfo.value:
						resolutionlabel.show()

	def changeVideomode(self):
		if usable:
			mode = self.lastmode
			if mode.find("p24") != -1 or mode.find("p25") != -1 or mode.find("p30") != -1:
				print "[AutoRes] switching to", mode
				try:
					v = open('/proc/stb/video/videomode' , "w")
					v.write("%s\n" % mode)
					v.close()
				except:
					pass
				resolutionlabel["restxt"].setText("Videomode: %s" % mode)
				if config.plugins.autoresolution.showinfo.value:
					resolutionlabel.show()
			else:
				self.setMode(mode)
			if config.plugins.autoresolution.testmode.value and default[0] != mode:
				resolutionlabeltxt = "Videomode: %s" % mode
				self.session.openWithCallback(
					self.confirm,
					MessageBox,
					_("Autoresolution Plugin Testmode:\nIs %s OK?") % (resolutionlabeltxt),
					MessageBox.TYPE_YESNO,
					timeout = 15,
					default = False
				)
		else:
			setDeinterlacer("auto")
			if self.lastmode != default[0]:
				self.setMode(default[0])

	def confirm(self, confirmed):
		if not confirmed:
			self.setMode(default[0])

	def setMode(self, mode, set=True):
		rate = config.av.videorate[mode].value
		resolutionlabel["restxt"].setText("Videomode: %s %s %s" % (port, mode, rate))
		if set:
			print "[AutoRes] switching to %s %s %s" % (port, mode, rate)
			if config.plugins.autoresolution.showinfo.value:
				resolutionlabel.show()
			video_hw.setMode(port, mode, rate)
		self.lastmode = mode

class ResolutionLabel(Screen):
	skin = """
		<screen position="50,40" size="250,36" flags="wfNoBorder" >
			<widget name="content" position="0,0" size="250,18" font="Regular;16" />
			<widget name="restxt" position="0,18" size="250,18" font="Regular;16" />
		</screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)

		self["content"] = Label()
		self["restxt"] = Label()

		self.hideTimer = eTimer()
		self.hideTimer.callback.append(self.hide)

		self.onShow.append(self.hide_me)

	def hide_me(self):
		self.hideTimer.start(config.usage.infobar_timeout.index * 2000, True)


class AutoResSetupMenu(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = [ "AutoResSetupMenu", "Setup" ]
		self.setup_title = _("Autoresolution videomode setup")
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)

		self.onChangedEntry = [ ]
		self.list = [ ]
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)

		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.apply,
			}, -2)

		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))

		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("Autoresolution settings"))

	def createSetup(self):
		self.list = [ getConfigListEntry(_("Enable Autoresolution"), config.plugins.autoresolution.enable) ]
		if config.plugins.autoresolution.enable.value:
			if usable:
				for mode, label in resolutions:
					self.list.append(getConfigListEntry(label, videoresolution_dictionary[mode]))
				self.list.extend((
					getConfigListEntry(_("Refresh Rate")+" 720p", config.av.videorate["720p"]),
					getConfigListEntry(_("Refresh Rate")+" 1080i", config.av.videorate["1080i"]),
					getConfigListEntry(_("Show info screen"), config.plugins.autoresolution.showinfo),
					getConfigListEntry(_("Delay x seconds after service started"), config.plugins.autoresolution.delay_switch_mode),
					getConfigListEntry(_("Running in testmode"), config.plugins.autoresolution.testmode),
					getConfigListEntry(_("Deinterlacer mode for interlaced content"), config.plugins.autoresolution.deinterlacer),
					getConfigListEntry(_("Deinterlacer mode for progressive content"), config.plugins.autoresolution.deinterlacer_progressive)
				))
			else:
				self.list.append(getConfigListEntry(_("Autoresolution is not working in Scart/DVI-PC Mode"), ConfigNothing()))

		self["config"].list = self.list
		self["config"].setList(self.list)

	def apply(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		self.close()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		if self["config"].getCurrent()[1] == config.plugins.autoresolution.enable:
			self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		if self["config"].getCurrent()[1] == config.plugins.autoresolution.enable:
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

def autostart(reason, **kwargs):
	if "session" in kwargs and resolutionlabel is None:
		global resolutionlabel
		session = kwargs["session"]
		resolutionlabel = session.instantiateDialog(ResolutionLabel)
		AutoRes(session)

def startSetup(menuid):
	if getImageDistro() in ('openmips'):
		if menuid != "video_menu":
			return [ ]
	elif getImageDistro() in ('openhdf'):
		if menuid != "video_menu":
			return [ ]
	else:
		if menuid != "system":
			return [ ]
	return [(_("Autoresolution"), autoresSetup, "autores_setup", 45)]

def autoresSetup(session, **kwargs):
	autostart(reason=0, session=session)
	session.open(AutoResSetupMenu)

def Plugins(path, **kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart), \
		PluginDescriptor(name="Autoresolution", description=_("Autoresolution Switch"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup) ]
