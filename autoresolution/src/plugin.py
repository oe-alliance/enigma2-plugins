from __future__ import print_function
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.Setup import SetupSummary
from Screens.MessageBox import MessageBox
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import config, configfile, getConfigListEntry, ConfigSelection, ConfigSubsection, ConfigYesNo, ConfigSubDict, ConfigNothing
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from enigma import iPlayableService, iServiceInformation, eTimer, getDesktop
from Plugins.Plugin import PluginDescriptor
from Tools import Notifications
from . import _
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

usable = False
preferedmodes = None
default = None
port = None
videoresolution_dictionary = {}
resolutionlabel = None
manualResolution = None

resolutions = (
	('sd_i_50', _("SD 25/50HZ Interlace Mode")),
	('sd_i_60', _("SD 30/60HZ Interlace Mode")),
	('sd_p_24', _("SD 24HZ Progressive mode")),
	('sd_p_50', _("SD 25/50HZ Progressive Mode")),
	('sd_p_60', _("SD 30/60HZ Progressive Mode")),
	('hd_i', _("HD Interlace Mode")),
	('hd_p', _("HD Progressive Mode")),
	('p720_24', _("Enable 720p24 Mode")),
	('p720_50', _("Enable 720p50 Mode")),
	('p1080_24', _("Enable 1080p24 Mode")),
	('p1080_25', _("Enable 1080p25 Mode")),
	('p1080_30', _("Enable 1080p30 Mode")),
)

have_1080p = config.av.videorate.get("1080p", False)
if have_1080p:
	resolutions += (
		('fhd_p', _("FHD 50/60HZ Progressive Mode")),
	)

have_2160p = config.av.videorate.get("2160p", False)
if have_2160p:
	resolutions += (
		('uhd_i', _("UHD Interlace Mode")),
		('uhd_p', _("UHD Progressive Mode")),
		('p2160_24', _("Enable 2160p24 Mode")),
		('p2160_25', _("Enable 2160p25 Mode")),
		('p2160_30', _("Enable 2160p30 Mode")),
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
		("0", "0 " + _("seconds")), ("50", "0.05 " + _("seconds")), ("500", "0.5 " + _("seconds")),
		("1000", "1 " + _("second")), ("2000", "2 " + _("seconds")), ("3000", "3 " + _("seconds")),
		("4000", "4 " + _("seconds")), ("5000", "5 " + _("seconds")), ("6000", "6 " + _("seconds")), ("7000", "7 " + _("seconds")),
		("8000", "8 " + _("seconds")), ("9000", "9 " + _("seconds")), ("10000", "10 " + _("seconds")), ("60000", "60 " + _("seconds"))])
config.plugins.autoresolution.mode = ConfigSelection(default = "manual", choices = [("manual", _("manual")), ("auto", _("Auto frame rate (refresh need 'multi')"))])
config.plugins.autoresolution.lock_timeout = ConfigSelection(default = "60", choices = [("30", "30 " + _("seconds")), ("60", "60 " + _("seconds"))])
config.plugins.autoresolution.ask_apply_mode = ConfigYesNo(default = False)
config.plugins.autoresolution.auto_30_60 = ConfigYesNo(default = True)
config.plugins.autoresolution.auto_24_30_alternative = ConfigYesNo(default = True)
config.plugins.autoresolution.ask_timeout = ConfigSelection(default = "20", choices = [("5", "5 " + _("seconds")), ("10", "10 " + _("seconds")), ("15", "15 " + _("seconds")), ("20", "20 " + _("seconds"))])
config.plugins.autoresolution.manual_resolution_ext_menu = ConfigYesNo(default = False)
config.plugins.autoresolution.manual_resolution_ask = ConfigYesNo(default = True)

def setDeinterlacer(mode):
	try:
		f = open('/proc/stb/vmpeg/deinterlace', "w")
		f.write("%s\n" % mode)
		f.close()
		print("[AutoRes] switch deinterlacer mode to %s" % mode)
	except:
		print("[AutoRes] failed switch deinterlacer mode to %s" % mode)

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
				iPlayableService.evStart: self.__evStart,
				iPlayableService.evEnd: self.__evEnd
			})
		self.timer = eTimer()
		self.timer.callback.append(self.determineContent)
		self.extra_mode720p60 = '720p60' in modes_available
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

	def __evEnd(self):
		self.newService = False

	def __evUpdatedInfo(self):
		if self.newService and config.plugins.autoresolution.mode.value == "manual":
			print("[AutoRes] service changed")
			self.after_switch_delay = False
			if int(config.plugins.autoresolution.delay_switch_mode.value) > 0:
				resolutionlabel.hide()
				self.timer.start(int(config.plugins.autoresolution.delay_switch_mode.value), True)
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
			print("[AutoRes] port changed to", configEntry.value)
			if port:
				config.av.videomode[port].notifiers.remove(self.defaultModeChanged)
			port = config.av.videoport.value
			if port in config.av.videomode:
				config.av.videomode[port].addNotifier(self.defaultModeChanged)
			usable = config.plugins.autoresolution.enable.value and not port in ('DVI-PC', 'Scart')
		else: # videomode changed in normal av setup
			global videoresolution_dictionary
			print("[AutoRes] mode changed to", configEntry.value)
			default = (configEntry.value, _("default"))
			preferedmodes = [mode[0] for mode in video_hw.getModeList(port) if mode[0] != default[0]]
			preferedmodes.append(default)
			print("[AutoRes] default", default)
			print("[AutoRes] preferedmodes", preferedmodes)
			videoresolution_dictionary = {}
			config.plugins.autoresolution.videoresolution = ConfigSubDict()
			if self.extra_mode720p60 and '720p60' not in preferedmodes:
				preferedmodes.append('720p60')
			if self.extra_mode1080p50 and '1080p50' not in preferedmodes:
				preferedmodes.append('1080p50')
			if self.extra_mode1080p60 and '1080p60' not in preferedmodes:
				preferedmodes.append('1080p60')
			for mode in resolutions:
				if have_2160p:
					if mode[0].startswith('p2160'):
						choices = ['2160p24', '2160p25', '2160p30', '1080p24', '1080p25', '1080p30'] + preferedmodes
					elif mode[0].startswith('p1080_24'):
						choices = ['1080p24', '2160p24'] + preferedmodes
					elif mode[0].startswith('p1080'):
						choices = ['1080p24', '1080p25', '1080p30'] + preferedmodes
					elif mode[0] == 'p720_24':
						choices = ['720p24', '1080p24', '2160p24'] + preferedmodes
					elif mode[0] == 'p720_50':
						choices = ['720p50', '1080p25', '2160p25'] + preferedmodes
					else:
						choices = preferedmodes
				else:
					if mode[0].startswith('p1080'):
						choices = ['1080p24', '1080p25', '1080p30'] + preferedmodes
					elif mode[0] == 'p720_24':
						choices = ['720p24', '1080p24'] + preferedmodes
					elif mode[0] == 'p720_50':
						choices = ['720p50', '1080p25'] + preferedmodes
					else:
						choices = preferedmodes
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
		print("[AutoRes] got event evFramerateChanged")
		if not self.timer.isActive() or self.after_switch_delay:
			self.timer.start(200, True) # give other pending events a chance..

	def __evVideoSizeChanged(self):
		print("[AutoRes] got event evVideoSizeChanged")
		if not self.timer.isActive() or self.after_switch_delay:
			self.timer.start(200, True) # give other pending events a chance..

	def __evVideoProgressiveChanged(self):
		print("[AutoRes] got event evVideoProgressiveChanged")
		if not self.timer.isActive() or self.after_switch_delay:
			self.timer.start(200, True) # give other pending events a chance..

	def determineContent(self):
		if config.plugins.autoresolution.mode.value != "manual":
			return
		print("[AutoRes] determineContent")
		self.timer.stop()
		resolutionlabel.hide()
		self.after_switch_delay = True
		if usable:
			service = self.session.nav.getCurrentService()
			info = service and service.info()
			height = info and info.getInfo(iServiceInformation.sVideoHeight)
			width = info and info.getInfo(iServiceInformation.sVideoWidth)
			framerate = info and info.getInfo(iServiceInformation.sFrameRate)

			if info and height != -1 and width != -1 and framerate != -1:
				videocodec = ("MPEG2", "AVC", "MPEG1", "MPEG4-VC", "VC1", "VC1-SM", "HEVC", "N/A")[info.getInfo(iServiceInformation.sVideoType)]
				frate = str(framerate)[:2] #fallback?
				if framerate in frqdic:
					frate = frqdic[framerate]

				prog = ("i", "p", "")[info.getInfo(iServiceInformation.sProgressive)]

				if have_2160p and (height >= 2100 or width >= 3200): # 2160 content
					if frate in ('24', '25', '30') and prog == 'p':
						new_mode = 'p2160_%s' % frate
					elif frate in ('50', '60') and prog == 'p':
						new_mode = 'uhd_p'
					else:
						new_mode = 'uhd_i' # 2160i content
				elif (height >= 900 or width >= 1600) and frate in ('24', '25', '30') and prog == 'p': # 1080p content
					new_mode = 'p1080_%s' % frate
				elif (576 < height < 900 or 720 < width < 1600) and frate == '24' and prog == 'p': # 720p24 content
					new_mode = 'p720_24'
				elif frate in ('24'): # always 1080p24 content
					new_mode = 'p1080_24'
				elif (576 < height < 900 or 720 < width < 1600) and frate == '50' and prog == 'p': # 720p50 content
					new_mode = 'p720_50'
				elif (height <= 576) and (width <= 720) and frate in ('25', '50'):
					new_mode = 'sd_%s_50' % prog
				elif (height <= 480) and (width <= 720) and frate in ('24', '30', '60'):
					new_mode = 'sd_%s_60' % prog
				elif have_1080p and (height >= 900 or width >= 1600) and frate in ('50', '60') and prog == 'p': # 1080p50/60 content
					new_mode = 'fhd_p'
				else:
					new_mode = 'hd_%s' % prog

				if prog == 'p':
					setDeinterlacer(config.plugins.autoresolution.deinterlacer_progressive.value)
				elif prog == 'i':
					setDeinterlacer(config.plugins.autoresolution.deinterlacer.value)
				else:
					setDeinterlacer("auto")

				print("[AutoRes] new content is %sx%s%s%s" %(width, height, prog, frate))

				if new_mode in videoresolution_dictionary:
					new_mode = videoresolution_dictionary[new_mode].value
					print('[AutoRes] determined videomode', new_mode)
					old = resolutionlabel["content"].getText()
					codec_info = "%s %s" % (videocodec, width)
					resolutionlabel["content"].setText(_("Videocontent: %sx%s%s %sHZ") % (codec_info, height, prog, frate))
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
			if "p24" in mode or "p25" in mode or "p30" in mode or (self.extra_mode1080p50 and "1080p50" in mode) or (self.extra_mode1080p60 and "1080p60" in mode) or (self.extra_mode720p60 and "720p60" in mode) or "720p50" in mode:
				try:
					v = open('/proc/stb/video/videomode', "w")
					v.write("%s\n" % mode)
					v.close()
					print("[AutoRes] switching to", mode)
				except:
					print("[AutoRes] failed switching to", mode)
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
		port_txt = "HDMI" if port == "DVI" else port
		resolutionlabel["restxt"].setText(_("Videomode: %s %s %s") % (port_txt, mode, rate))
		if set:
			print("[AutoRes] switching to %s %s %s" % (port_txt, mode, rate))
			if config.plugins.autoresolution.showinfo.value:
				resolutionlabel.show()
			try:
				video_hw.setMode(port, mode, rate)
			except:
				print("[AutoRes] Videomode: failed switching to", mode)
				return
		self.lastmode = mode

class ResolutionLabel(Screen):
	height = getDesktop(0).size().height()
	if height >= 2100:
		skin = """
			<screen position="150,120" size="880,108" flags="wfNoBorder">
				<widget name="content" position="0,0" size="880,54" font="Regular;48" />
				<widget name="restxt" position="0,54" size="880,54" font="Regular;48" />
			</screen>"""
	elif height == 1080:
		skin = """
			<screen position="75,60" size="480,54" flags="wfNoBorder">
				<widget name="content" position="0,0" size="480,27" font="Regular;24" />
				<widget name="restxt" position="0,27" size="480,27" font="Regular;24" />
			</screen>"""
	else:
		skin = """
			<screen position="50,40" size="330,36" flags="wfNoBorder">
				<widget name="content" position="0,0" size="330,18" font="Regular;16" />
				<widget name="restxt" position="0,18" size="330,18" font="Regular;16" />
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
		self.setTitle(self.setup_title)
		self.onChangedEntry = [ ]
		self.list = [ ]
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)
		self.prev_manual_resolution_ext_menu = config.plugins.autoresolution.manual_resolution_ext_menu.value
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.apply,
			}, -2)

		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))

		self.createSetup()

	def createSetup(self):
		self.list = [getConfigListEntry(_("Enable Autoresolution"), config.plugins.autoresolution.enable)]
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
					self.list.append(getConfigListEntry(_("Ask before changing videomode"), config.plugins.autoresolution.ask_apply_mode))
					if config.plugins.autoresolution.ask_apply_mode.value:
						self.list.append(getConfigListEntry(_("Message timeout"), config.plugins.autoresolution.ask_timeout))
					self.list.append(getConfigListEntry(_("Use 60HZ instead 30HZ"), config.plugins.autoresolution.auto_30_60))
					self.list.append(getConfigListEntry(_("Alternative resolution when native not supported"), config.plugins.autoresolution.auto_24_30_alternative))
			else:
				self.list.append(getConfigListEntry(_("Autoresolution is not working in Scart/DVI-PC Mode"), ConfigNothing()))
		elif config.av.videoport.value not in ('DVI-PC', 'Scart'):
				self.list.append(getConfigListEntry(_("Show 'Manual resolution' in extensions menu"), config.plugins.autoresolution.manual_resolution_ext_menu))
				if config.plugins.autoresolution.manual_resolution_ext_menu.value:
					self.list.append(getConfigListEntry(_("Return back without confirmation after 10 sec."), config.plugins.autoresolution.ask_apply_mode))
		self["config"].list = self.list
		self["config"].setList(self.list)

	def apply(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		if self.prev_manual_resolution_ext_menu != config.plugins.autoresolution.manual_resolution_ext_menu.value:
			self.refreshPlugins()
		self.close()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		if self["config"].getCurrent() and len(self["config"].getCurrent()) > 0:
			if self["config"].getCurrent()[1] in (config.plugins.autoresolution.enable, config.plugins.autoresolution.mode, config.plugins.autoresolution.ask_apply_mode,  config.plugins.autoresolution.manual_resolution_ext_menu):
				self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		if self["config"].getCurrent() and len(self["config"].getCurrent()) > 0:
			if self["config"].getCurrent()[1] in (config.plugins.autoresolution.enable, config.plugins.autoresolution.mode, config.plugins.autoresolution.ask_apply_mode,  config.plugins.autoresolution.manual_resolution_ext_menu):
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

	def refreshPlugins(self):
		from Components.PluginComponent import plugins
		from Tools.Directories import SCOPE_PLUGINS, resolveFilename
		plugins.clearPluginList()
		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))

class AutoFrameRate(Screen):
	def __init__(self, session):
		global modes_available
		Screen.__init__(self, session)
		self.lockTimer = eTimer()
		self.lockTimer.callback.append(self.unlockFramerateChange)
		self.framerate_change_is_locked = False
		self.lastService = None
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap = {iPlayableService.evVideoFramerateChanged: self.AutoVideoFramerateChanged})
		self.init = False

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
					if "multi" in config.av.videorate[config.av.videomode[config.av.videoport.value].value].value:
						replace_mode = '30'
						if config.plugins.autoresolution.auto_30_60.value:
							replace_mode = '60'
						if framerate in (59940, 60000):
							self.setVideoFrameRate('60')
						elif framerate in (23976, 24000):
							self.setVideoFrameRate('24')
						elif framerate in (29970, 30000):
							self.setVideoFrameRate(replace_mode)
						else:
							self.setVideoFrameRate('50')

	def setVideoFrameRate(self, rate):
		if self.framerate_change_is_locked:
			return
		try:
			f = open("/proc/stb/video/videomode", "r")
			videomode = f.read()
			f.close()
			if rate in ('24', '30'):
				multi_videomode = videomode
				if not videomode.endswith(rate):
					resolutions = ('1080', '2160', '720')
					for resolution in resolutions:
						if videomode.startswith(resolution):
							new_mode = resolution + 'p' + rate
							if new_mode in modes_available:
								multi_videomode = new_mode
								break
							elif config.plugins.autoresolution.auto_24_30_alternative.value:
								for alternative_resolution in resolutions:
									if alternative_resolution != resolution:
										new_mode = alternative_resolution + 'p' + rate
										if new_mode in modes_available:
											multi_videomode = new_mode
											break
			else:
				f = open("/proc/stb/video/videomode_%shz" % rate, "r")
				multi_videomode = f.read()
				f.close()
			if videomode != multi_videomode:
				self.new_mode = multi_videomode
				self.cur_mode = videomode
				self.framerate_change_is_locked = True
				self.lockTimer.startLongTimer(int(config.plugins.autoresolution.lock_timeout.value))
				if config.plugins.autoresolution.ask_apply_mode.value and self.init:
					Notifications.AddNotificationWithCallback(self.changeFramerateCallback, MessageBox, _("Changing framerate for current service?\nCurrent framerate: %s\nNew framerate: %s\n") % (videomode, multi_videomode), MessageBox.TYPE_YESNO, timeout = int(config.plugins.autoresolution.ask_timeout.value))
				else:
					self.changeFramerateCallback(True)
			if not self.init:
				self.init = True
		except IOError:
			print("[AutoFrameRate] error at reading/writing /proc/stb/video.. files")

	def changeFramerateCallback(self, ret=True):
		if ret:
			f = open("/proc/stb/video/videomode", "w")
			f.write(self.new_mode)
			f.close()
			print("[AutoFramerate] set resolution/framerate: %s" % self.new_mode)
			service = self.session.nav.getCurrentlyPlayingServiceReference()
			if service:
				path = service.getPath()
				if path.find("://") == -1:
					self.doSeekRelative(2 * 9000)

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

class ManualResolution(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.choices = []
		self.init = False
		try:
			f = open("/proc/stb/video/videomode_choices")
			values = f.readline().replace("\n", "").replace("pal ", "").replace("ntsc ", "").replace("auto", "").replace("480i", "").replace("480p", "").replace("576i", "").replace("576p", "").replace("3d1080p24", "").replace("3d720p50", "").replace("3d720p", "").split(" ", -1)
			for x in values:
				if x:
					entry = x.replace('i50', 'i@50hz').replace('i60', 'i@60hz').replace('p23', 'p@23.976hz').replace('p24', 'p@24hz').replace('p25', 'p@25hz').replace('p29', 'p@29.970hz').replace('p30', 'p@30hz').replace('p50', 'p@50hz').replace('p60', 'p@60hz'), x
					self.choices.append(entry)
			f.close()
		except:
			print("[ManualResolution] Error open /proc/stb/video/videomode_choices")
		else:
			self.choices and self.choices.sort()

	def resolutionSelection(self):
		if not self.choices:
			return
		try:
			f = open("/proc/stb/vmpeg/0/xres", "r")
			xresString = f.read()
			f.close()
			f = open("/proc/stb/vmpeg/0/yres", "r")
			yresString = f.read()
			f.close()
			try:
				f = open("/proc/stb/vmpeg/0/framerate", "r")
				fpsString = f.read()
				f.close()
			except:
				print("[ManualResolution] Error open /proc/stb/vmpeg/0/framerate")
				fpsString = '50000'
			xres = int(xresString, 16)
			yres = int(yresString, 16)
			fps = int(fpsString)
			fpsFloat = float(fps)
			fpsFloat = fpsFloat/1000
		except:
			print("[ManualResolution] Error reading current mode!Stop!")
			return
		selection = 0
		tlist = []
		tlist.append((_("Exit"), "exit")) 
		tlist.append((_("Video: ") + str(xres) + "x" + str(yres) + "@" + str(fpsFloat) + "hz", ""))
		tlist.append(("--", ""))
		for x in self.choices:
			tlist.append(x)
		keys = ["green", "yellow", "blue", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
		self.old_mode = ""
		if self.init:
			try:
				self.old_mode = open("/proc/stb/video/videomode").read()[:-1]
			except:
				print("[ManualResolution] Error open /proc/stb/video/videomode")
		if self.old_mode:
			for x in range(len(tlist)):
				if tlist[x][1] == self.old_mode:
					selection = x
		self.session.openWithCallback(self.resolutionSelected, ChoiceBox, title=_("Please select a resolution..."), list=tlist, selection=selection, keys=keys, windowTitle= _("Manual resolution"))

	def resolutionSelected(self, res):
		res = res and res[1]
		if res and isinstance(res, str) and res != "exit":
			self.setResolution(res)
			if config.plugins.autoresolution.ask_apply_mode.value and self.init and self.old_mode != res:
				self.session.openWithCallback(self.confirmMode, MessageBox, _("This resolution is OK?"), MessageBox.TYPE_YESNO, timeout=10, default=False)
			if not self.init:
				self.init = True

	def confirmMode(self, answer):
		if not answer and self.old_mode:
			self.setResolution(self.old_mode)

	def setResolution(self, mode):
		try:
			f = open("/proc/stb/video/videomode", "w")
			f.write(mode)
			f.close()
		except:
			print("[ManualResolution] Error write /proc/stb/video/videomode")

def openManualResolution(session, **kwargs):
	if config.av.videoport.value not in ('DVI-PC', 'Scart'):
		global manualResolution
		if manualResolution is None:
			manualResolution = session.instantiateDialog(ManualResolution)
		manualResolution and manualResolution.resolutionSelection()
	else:
		config.plugins.autoresolution.manual_resolution_ext_menu.value = False
		config.plugins.autoresolution.manual_resolution_ext_menu.save()
		session.open(MessageBox, _("Manual resolution is not working in Scart/DVI-PC mode!"), MessageBox.TYPE_INFO, timeout=6)

def autostart(reason, **kwargs):
	global resolutionlabel
	if reason == 0 and "session" in kwargs and resolutionlabel is None:
		session = kwargs["session"]
		if session:
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
	return [(_("Autoresolution"), autoresSetup, "autores_setup", None)]

def autoresSetup(session, **kwargs):
	autostart(reason=0, session=session)
	session.open(AutoResSetupMenu)

def Plugins(path, **kwargs):
	lst = [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart),
		PluginDescriptor(name="Autoresolution", description=_("Autoresolution Switch"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup)]
	if not config.plugins.autoresolution.enable.value and config.plugins.autoresolution.manual_resolution_ext_menu.value:
		lst.append(PluginDescriptor(name = _("Manual resolution"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, needsRestart=False, fnc=openManualResolution))
	return lst
