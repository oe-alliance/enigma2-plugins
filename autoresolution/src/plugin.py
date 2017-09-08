from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Screens.MessageBox import MessageBox
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import config, configfile, getConfigListEntry, ConfigSelection, ConfigSubsection, ConfigYesNo, ConfigSubDict, ConfigNothing
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from enigma import iPlayableService, iServiceInformation, eTimer
from Plugins.Plugin import PluginDescriptor
import os

from boxbranding import getImageDistro, getBoxType

try:
	from Components.AVSwitch import iAVSwitch as video_hw
except:
	from Plugins.SystemPlugins.Videomode.VideoHardware import video_hw # depends on Videomode Plugin

# modes_available used to be a member variable, but that was removed and
# the value can now only be accessed using an accessor function.
# Need to cater for either...
#
if hasattr(video_hw, "modes_available"):
	modes_available = video_hw.modes_available
else:
	modes_available = video_hw.readAvailableModes()


# for localized messages
from . import _

usable = False
preferedmodes = None
default = None
port = None
videoresolution_dictionary = {}
resolutionlabel = None

# Added p720_50
resolutions = ( \
	('sd_i_50',        _("SD 25/50HZ Interlace Mode")), \
	('sd_i_60',        _("SD 30/60HZ Interlace Mode")), \
	('sd_p_24',        _("SD 24HZ Progressive mode")), \
	('sd_p_50',        _("SD 25/50HZ Progressive Mode")), \
	('sd_p_60',        _("SD 30/60HZ Progressive Mode")), \
	('hd_i',           _("HD Interlace Mode")), \
	('hd_p',           _("HD Progressive Mode")), \
	('p720_24',        _("Enable 720p24 Mode")), \
	('p720_50',        _("Enable 720p50 Mode")), \
	('p1080_24',       _("Enable 1080p24 Mode")), \
	('p1080_25',       _("Enable 1080p25 Mode")), \
	('p1080_30',       _("Enable 1080p30 Mode")), \
)

# from OpenPLi
have_2160p = config.av.videorate.get("2160p", False)

if have_2160p:				        
	resolutions += (
		('uhd_i',    _("UHD Interlace Mode")),
		('uhd_p',    _("UHD Progressive Mode")),
		('p2160_24', _("Enable 2160p24 Mode")),
		('p2160_25', _("Enable 2160p25 Mode")),
		('p2160_30', _("Enable 2160p30 Mode")), # Trailing , is NEEDED!
)

config.plugins.autoresolution = ConfigSubsection()
config.plugins.autoresolution.enable = ConfigYesNo(default = False)
config.plugins.autoresolution.showinfo = ConfigYesNo(default = True)
config.plugins.autoresolution.testmode = ConfigYesNo(default = False)
config.plugins.autoresolution.deinterlacer = ConfigSelection(default = "auto", choices =
		[("off", _("off")), ("auto", _("auto")), ("on", _("on")), ("bob", _("bob"))])
config.plugins.autoresolution.deinterlacer_progressive = ConfigSelection(default = "auto", choices =
		[("off", _("off")), ("auto", _("auto")), ("on", _("on")), ("bob", _("bob"))])
config.plugins.autoresolution.delay_switch_mode = ConfigSelection(default = "1000", choices = [
		("0", "0 " + _("seconds")),("50", "0.05 " + _("seconds")), ("500", "0.5 " + _("seconds")),
		("1000", "1 " + _("second")), ("2000", "2 " + _("seconds")), ("3000", "3 " + _("seconds")),
		("4000", "4 " + _("seconds")), ("5000", "5 " + _("seconds")), ("6000", "6 " + _("seconds")), ("7000", "7 " + _("seconds")),
		("8000", "8 " + _("seconds")), ("9000", "9 " + _("seconds")), ("10000", "10 " + _("seconds")),("60000", "60 " + _("seconds"))])
config.plugins.autoresolution.mode = ConfigSelection(default = "manual", choices = [("manual", _("manual")), ("auto", _("Auto frame rate (refresh need 'multi')"))])
config.plugins.autoresolution.lock_timeout = ConfigSelection(default = "60", choices = [("30", "30 " + _("seconds")), ("60", "60 " + _("seconds"))])

def setDeinterlacer(mode):
	try:
		f = open('/proc/stb/vmpeg/deinterlace' , "w")
		f.write("%s\n" % mode)
		f.close()
		print "[AutoRes] switch deinterlacer mode to %s" % mode
	except:
		print "[AutoRes] failed switch deinterlacer mode to %s" % mode

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
		global modes_available
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
		self.extra_mode1080p50 = '1080p50' in modes_available
		self.extra_mode1080p60 = '1080p60' in modes_available
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
		if "1080p" in config.av.videorate:
			config.av.videorate["1080p"].addNotifier(self.__videorate_1080p_changed, initial_call = False, immediate_feedback = False)
		if "2160p" in config.av.videorate:
			config.av.videorate["2160p"].addNotifier(self.__videorate_2160p_changed, initial_call = False, immediate_feedback = False)

	def __videorate_720p_changed(self, configEntry):
		if self.lastmode == "720p":
			self.changeVideomode()

	def __videorate_1080i_changed(self, configEntry):
		if self.lastmode == "1080i":
			self.changeVideomode()

	def __videorate_1080p_changed(self, configEntry):
		if self.lastmode == "1080p":
			self.changeVideomode()

	def __videorate_2160p_changed(self, configEntry):
		if self.lastmode == "2160p":
			self.changeVideomode()

	def __evStart(self):
		self.newService = True

	def __evUpdatedInfo(self):
		if self.newService and config.plugins.autoresolution.mode.value == "manual":
			print "[AutoRes] service changed"
			self.after_switch_delay = False
			if int(config.plugins.autoresolution.delay_switch_mode.value) > 0:
				resolutionlabel.hide()
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
			print "[AutoRes] port changed to", configEntry.value
			if port:
				config.av.videomode[port].notifiers.remove(self.defaultModeChanged)
			port = config.av.videoport.value
			if port in config.av.videomode:
				config.av.videomode[port].addNotifier(self.defaultModeChanged)
			usable = config.plugins.autoresolution.enable.value and not port in ('DVI-PC', 'Scart')
		else: # videomode changed in normal av setup
			global videoresolution_dictionary
			print "[AutoRes] mode changed to", configEntry.value
			default = (configEntry.value, _("default"))
			preferedmodes = [mode[0] for mode in video_hw.getModeList(port) if mode[0] != default[0]]
			preferedmodes.append(default)
			print "[AutoRes] default", default
			print "[AutoRes] preferedmodes", preferedmodes
			videoresolution_dictionary = {}
			config.plugins.autoresolution.videoresolution = ConfigSubDict()
			default_choices = ['1080p24', '1080p25', '1080p30']
			if self.extra_mode1080p50:
				default_choices.append('1080p50')
			if self.extra_mode1080p60:
				default_choices.append('1080p60')
			for mode in resolutions:
# from OpenPLi
				if have_2160p:
					if mode[0].startswith('p2160'):
						choices = ['2160p24', '2160p25', '2160p30'] + preferedmodes
					elif mode[0].startswith('p1080_24'):
						choices = ['1080p24', '2160p24'] + preferedmodes
					elif mode[0].startswith('p1080'):
						choices = ['1080p24', '1080p25', '1080p30'] + preferedmodes
					elif mode[0] == 'p720_24':
						choices = ['720p24', '1080p24', '2160p24'] + preferedmodes
# Added p720_50
					elif mode[0] == 'p720_50':
						choices = ['720p50', '1080p25', '2160p25'] + preferedmodes
					else:
						choices = default_choices + preferedmodes
				else:
					if mode[0].startswith('p1080'):
						choices = ['1080p24', '1080p25', '1080p30'] + preferedmodes
					elif mode[0] == 'p720_24':
						choices = ['720p24', '1080p24'] + preferedmodes
# Added p720_50
					elif mode[0] == 'p720_50':
						choices = ['720p50', '1080p25'] + preferedmodes
					else:
						choices = default_choices + preferedmodes
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
		if config.plugins.autoresolution.mode.value != "manual":
			return
		print "[AutoRes] determineContent"
		self.timer.stop()
		resolutionlabel.hide()
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
# from OpenPLi
				if have_2160p and (height >= 2100 or width >= 3200): # 2160 content
					if frate in ('24', '25', '30') and prog == 'p':
						new_mode = 'p2160_%s' % frate
					elif frate in ('50', '60') and prog == 'p':
						new_mode = 'uhd_p'
					else:
						new_mode = 'uhd_i' # 2160i content - senseless ???
				elif frate in ('24'): # always 1080p24 content ???
					new_mode = 'p1080_24'
				elif (height >= 900 or width >= 1600) and frate in ('24', '25', '30') and prog == 'p': # 1080p content
					new_mode = 'p1080_%s' % frate
				elif (height > 576 or width > 720) and frate == '24' and prog == 'p': # 720p24 detection
					new_mode = 'p720_24'
# Added p720_50
				elif (height > 576 or width > 720) and frate == '50' and prog == 'p': # 720p50 detection
					new_mode = 'p720_50'
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
					resolutionlabel["content"].setText(_("Videocontent: %sx%s%s %sHZ") % (width, height, prog, frate))
					if self.lastmode != new_mode:
						self.lastmode = new_mode
						self.changeVideomode()
					elif old != resolutionlabel["content"].getText() and config.plugins.autoresolution.showinfo.value:
						resolutionlabel.show()

	def changeVideomode(self):
		if config.plugins.autoresolution.mode.value != "manual":
			return
		if usable:
			mode = self.lastmode
			if mode.find("p24") != -1 or mode.find("p25") != -1 or mode.find("p30") != -1 or (self.extra_mode1080p50 and mode.find("p50") != -1) or (self.extra_mode1080p60 and mode.find("p60") != -1):
				try:
					v = open('/proc/stb/video/videomode' , "w")
					v.write("%s\n" % mode)
					v.close()
					print "[AutoRes] switching to", mode
				except:
					print "[AutoRes] failed switching to", mode
				resolutionlabel["restxt"].setText(_("Videomode: %s") % mode)
				if config.plugins.autoresolution.showinfo.value:
					resolutionlabel.show()
			else:
				self.setMode(mode)
			if config.plugins.autoresolution.testmode.value and default[0] != mode:
				resolutionlabeltxt = _("Videomode: %s") % mode
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
		if config.plugins.autoresolution.mode.value != "manual":
			return
		rate = config.av.videorate[mode].value
		resolutionlabel["restxt"].setText(_("Videomode: %s %s %s") % (port, mode, rate))
		if set:
			print "[AutoRes] switching to %s %s %s" % (port, mode, rate)
			if config.plugins.autoresolution.showinfo.value:
				resolutionlabel.show()
			try:
				video_hw.setMode(port, mode, rate)
			except:
				print "[AutoRes] Videomode: failed switching to", mode
				return
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
				self.list.append(getConfigListEntry(_("Mode"), config.plugins.autoresolution.mode))
				if config.plugins.autoresolution.mode.value == "manual":
					for mode, label in resolutions:
						self.list.append(getConfigListEntry(label, videoresolution_dictionary[mode]))
					if "720p" in config.av.videorate:
						self.list.append(getConfigListEntry(_("Refresh Rate")+" 720p", config.av.videorate["720p"]))
					if "1080i" in config.av.videorate:
						self.list.append(getConfigListEntry(_("Refresh Rate")+" 1080i", config.av.videorate["1080i"]))
					if "1080p" in config.av.videorate:
						self.list.append(getConfigListEntry(_("Refresh Rate")+" 1080p", config.av.videorate["1080p"]))
					if "2160p" in config.av.videorate:
						self.list.append(getConfigListEntry(_("Refresh Rate")+" 2160p", config.av.videorate["2160p"]))
					self.list.extend((
						getConfigListEntry(_("Show info screen"), config.plugins.autoresolution.showinfo),
						getConfigListEntry(_("Delay x seconds after service started"), config.plugins.autoresolution.delay_switch_mode),
						getConfigListEntry(_("Running in testmode"), config.plugins.autoresolution.testmode),
						getConfigListEntry(_("Deinterlacer mode for interlaced content"), config.plugins.autoresolution.deinterlacer),
						getConfigListEntry(_("Deinterlacer mode for progressive content"), config.plugins.autoresolution.deinterlacer_progressive)
					))
				else:
					self.list.append(getConfigListEntry(_("Lock timeout"), config.plugins.autoresolution.lock_timeout))
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
		if self["config"].getCurrent() and len(self["config"].getCurrent()) > 0:
			if self["config"].getCurrent()[1] in (config.plugins.autoresolution.enable, config.plugins.autoresolution.mode):
				self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		if self["config"].getCurrent() and len(self["config"].getCurrent()) > 0:
			if self["config"].getCurrent()[1] in (config.plugins.autoresolution.enable, config.plugins.autoresolution.mode):
				self.createSetup()

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent() and self["config"].getCurrent()[0] or ""

	def getCurrentValue(self):
		if self["config"].getCurrent() and len(self["config"].getCurrent()) > 0:
			return str(self["config"].getCurrent()[1].getText())
		return ""

	def createSummary(self):
		return SetupSummary

class AutoFrameRate(Screen):
	def __init__(self, session):
		global modes_available
		Screen.__init__(self, session)
		self.lockTimer = eTimer()
		self.lockTimer.callback.append(self.unlockFramerateChange)
		self.framerate_change_is_locked = False
		self.lastService = None
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap = {iPlayableService.evVideoFramerateChanged: self.AutoVideoFramerateChanged})
		self.need_reset = getBoxType() in ('solo4k')
		self.replace_mode = '30'
		if '1080p60' in modes_available:
			self.replace_mode = '60'

	def AutoVideoFramerateChanged(self):
		if usable and config.plugins.autoresolution.mode.value == "auto":
			if config.av.videoport.value in config.av.videomode:
				if config.av.videomode[config.av.videoport.value].value in config.av.videorate:
					service = self.session.nav.getCurrentService()
					ref = self.session.nav.getCurrentlyPlayingServiceReference()
					if not ref or not service: return
					cur_service_str = ref.toString()
					if not (cur_service_str and self.lastService):
						self.lastService = cur_service_str
					if cur_service_str != self.lastService:
						self.lockTimer.stop()
						self.lastService = cur_service_str
						self.framerate_change_is_locked = False
					info = service and service.info()
					framerate = info and info.getInfo(iServiceInformation.sFrameRate)
					if config.av.videorate[config.av.videomode[config.av.videoport.value].value].value == "multi":
						if framerate in (59940, 60000):
							self.setVideoFrameRate('60')
						elif framerate in (23976, 24000):
							self.setVideoFrameRate('24')
						elif framerate in (29970, 30000):
							self.setVideoFrameRate(self.replace_mode)
						else:
							self.setVideoFrameRate('50')

	def setVideoFrameRate(self, rate):
		if self.framerate_change_is_locked:
			return
		try:
			f = open("/proc/stb/video/videomode", "r")
			videomode = f.read()
			f.close()
			f = open("/proc/stb/video/videomode_choices", "r")
			videomode_choices = f.read()
			f.close()
			videomode_choices = videomode_choices.split()
			if rate in ('24', '30'):
				multi_videomode = videomode
				if not videomode.endswith(rate):
					resolutions = ('1080', '2160', '720')
					for resolution in resolutions:
						if videomode.startswith(resolution):
							new_mode = resolution + 'p' + rate
							if new_mode in videomode_choices:
								multi_videomode = new_mode
								break
							else:
								for alternative_resolution in resolutions:
									if alternative_resolution != resolution:
										new_mode = alternative_resolution + 'p' + rate
										if new_mode in videomode_choices:
											multi_videomode = new_mode
											break
			else:
				f = open("/proc/stb/video/videomode_%shz" % rate, "r")
				multi_videomode = f.read()
				f.close()
			if videomode != multi_videomode:
				f = open("/proc/stb/video/videomode", "w")
				f.write(multi_videomode)
				f.close()
				self.framerate_change_is_locked = True
				self.lockTimer.startLongTimer(int(config.plugins.autoresolution.lock_timeout.value))
				if self.need_reset:
					self.doSeekRelative(2 * 9000)
		except IOError:
			print "error at reading/writing /proc/stb/video.. files"

	def unlockFramerateChange(self):
		self.lockTimer.stop()
		self.framerate_change_is_locked = False

	def getSeek(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None
		seek = service.seek()
		if seek is None or not seek.isCurrentlySeekable():
			return None
		return seek

	def doSeekRelative(self, pts):
		seekable = self.getSeek()
		if seekable is None:
			return
 		seekable.seekRelative(pts < 0 and -1 or 1, abs(pts))

def autostart(reason, **kwargs):
	global resolutionlabel
	if reason == 0 and "session" in kwargs and resolutionlabel is None:
		session = kwargs["session"]
		resolutionlabel = session.instantiateDialog(ResolutionLabel)
		AutoFrameRate(session)
		AutoRes(session)

def startSetup(menuid):
	if getImageDistro() in ('teamblue', 'openhdf'):
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
		PluginDescriptor(name="Autoresolution", description=_("Autoresolution Switch"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup)]
