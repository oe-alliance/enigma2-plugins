# -*- coding: UTF-8 -*-
# for localized messages
from . import _

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Screens.ChannelSelection import SimpleChannelSelection
from Screens.EpgSelection import EPGSelection
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button

# Configuration
from Components.config import getConfigListEntry, ConfigEnableDisable, \
	ConfigYesNo, ConfigText, ConfigClock, ConfigNumber, ConfigSelection, \
	config, NoSave

# Timer
from RecordTimer import AFTEREVENT

# Needed to convert our timestamp back and forth
from time import localtime, mktime

# Show ServiceName instead of ServiceReference
from ServiceReference import ServiceReference

# addAutotimerFromService, AutoTimerChannelSelection
from enigma import eServiceCenter, eServiceReference, iServiceInformation

# Default Record Directory
from Tools import Directories

# Tags
from Screens.MovieSelection import getPreferredTagEditor

weekdays = [
	("0", _("Monday")),
	("1", _("Tuesday")),
	("2", _("Wednesday")),
	("3", _("Thursday")),
	("4", _("Friday")),
	("5", _("Saturday")),
	("6", _("Sunday")),
	("weekend", _("Weekend")),
	("weekday", _("Weekday"))
]

class ExtendedConfigText(ConfigText):
	def __init__(self, default = "", fixed_size = True, visible_width = False):
		ConfigText.__init__(self, default = default, fixed_size = fixed_size, visible_width = visible_width)

		# Workaround some characters currently not "typeable" using NumericalTextInput
		mapping = self.mapping
		if mapping:
			if "&" not in mapping[0]:
				mapping[0] += "&"
			if ";" not in mapping[0]:
				mapping[0] += ";"
			if "%" not in mapping[0]:
				mapping[0] += "%"

class SimpleBouquetSelection(SimpleChannelSelection):
	def __init__(self, session, title):
		SimpleChannelSelection.__init__(self, session, title)
		self.skinName = "SimpleChannelSelection"

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.close(ref)
		else:
			# We return the currently active path here
			# Asking the user if this is what he wants might be better though
			self.close(self.servicePath[-1])

class AutoTimerChannelSelection(SimpleChannelSelection):
	def __init__(self, session, autotimer):
		SimpleChannelSelection.__init__(self, session, _("Channel Selection"))
		self.skinName = "SimpleChannelSelection"
		self.autotimer = autotimer

		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"],
			{
				"showEPGList": self.channelSelected
			}
		)

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.enterPath(ref)
		elif not (ref.flags & eServiceReference.isMarker):
			self.session.open(
				AutoTimerEPGSelection,
				ref
			)

class AutoTimerEPGSelection(EPGSelection):
	def __init__(self, *args):
		EPGSelection.__init__(self, *args)
		self.skinName = "EPGSelection"

	def infoKeyPressed(self):
		self.timerAdd()

	def timerAdd(self):
		cur = self["list"].getCurrent()
		evt = cur[0]
		sref = cur[1]
		if not evt:
			return

		addAutotimerFromEvent(self.session, evt = evt, service = sref)

	def onSelectionChanged(self):
		pass

class AutoTimerEditorBase:
	""" Base Class for all Editors """
	def __init__(self, timer, editingDefaults = False):
		# Keep Timer
		self.timer = timer
		self.editingDefaults = editingDefaults

		# See if we are filtering some strings
		excludes = (
			timer.getExcludedTitle(),
			timer.getExcludedShort(),
			timer.getExcludedDescription(),
			timer.getExcludedDays()
		)
		includes = (
			timer.getIncludedTitle(),
			timer.getIncludedShort(),
			timer.getIncludedDescription(),
			timer.getIncludedDays()
		)
		if excludes[0] or excludes[1] \
				or excludes[2] or excludes[3] \
				or includes[0] or includes[1] \
				or includes[2] or includes[3]:
			self.filterSet = True
		else:
			self.filterSet = False
		self.excludes = excludes
		self.includes = includes

		# See if services are restricted
		self.services = timer.services
		self.bouquets = timer.bouquets
		if self.services or self.bouquets:
			self.serviceRestriction = True
		else:
			self.serviceRestriction = False

		self.createSetup(timer)

	def createSetup(self, timer):
		# Name
		self.name = NoSave(ExtendedConfigText(default = timer.name, fixed_size = False))

		# Match
		self.match = NoSave(ExtendedConfigText(default = timer.match, fixed_size = False))

		# Encoding
		default = timer.encoding
		selection = ['UTF-8', 'ISO8859-15']
		if default not in selection:
			selection.append(default)
		self.encoding = NoSave(ConfigSelection(choices = selection, default = default))

		# ...
		self.searchType = NoSave(ConfigSelection(choices = [("partial", _("partial match")), ("exact", _("exact match"))], default = timer.searchType))
		self.searchCase = NoSave(ConfigSelection(choices = [("sensitive", _("case-sensitive search")), ("insensitive", _("case-insensitive search"))], default = timer.searchCase))

		# Justplay
		self.justplay = NoSave(ConfigSelection(choices = [("zap", _("zap")), ("record", _("record"))], default = {0: "record", 1: "zap"}[int(timer.justplay)]))

		# Timespan
		now = [x for x in localtime()]
		if timer.hasTimespan():
			default = True
			now[3] = timer.timespan[0][0]
			now[4] = timer.timespan[0][1]
			begin = mktime(now)
			now[3] = timer.timespan[1][0]
			now[4] = timer.timespan[1][1]
			end = mktime(now)
		else:
			default = False
			now[3] = 20
			now[4] = 15
			begin = mktime(now)
			now[3] = 23
			now[4] = 15
			end = mktime(now)
		self.timespan = NoSave(ConfigEnableDisable(default = default))
		self.timespanbegin = NoSave(ConfigClock(default = begin))
		self.timespanend = NoSave(ConfigClock(default = end))

		# Services have their own Screen

		# Offset
		if timer.hasOffset():
			default = True
			begin = timer.getOffsetBegin()
			end = timer.getOffsetEnd()
		else:
			default = False
			begin = 5
			end = 5
		self.offset = NoSave(ConfigEnableDisable(default = default))
		self.offsetbegin = NoSave(ConfigNumber(default = begin))
		self.offsetend = NoSave(ConfigNumber(default = end))

		# AfterEvent
		if timer.hasAfterEvent():
			default = {
				None: "default",
				AFTEREVENT.NONE: "nothing",
				AFTEREVENT.DEEPSTANDBY: "deepstandby",
				AFTEREVENT.STANDBY: "standby",
				AFTEREVENT.AUTO: "auto"
			}[timer.afterevent[0][0]]
		else:
			default = "default"
		self.afterevent = NoSave(ConfigSelection(choices = [
			("default", _("standard")), ("nothing", _("do nothing")),
			("standby", _("go to standby")),
			("deepstandby", _("go to deep standby")),
			("auto", _("auto"))], default = default))

		# AfterEvent (Timespan)
		if timer.hasAfterEvent() and timer.afterevent[0][1][0] is not None:
			default = True
			now[3] = timer.afterevent[0][1][0][0]
			now[4] = timer.afterevent[0][1][0][1]
			begin = mktime(now)
			now[3] = timer.afterevent[0][1][1][0]
			now[4] = timer.afterevent[0][1][1][1]
			end = mktime(now)
		else:
			default = False
			now[3] = 23
			now[4] = 15
			begin = mktime(now)
			now[3] = 7
			now[4] = 0
			end = mktime(now)
		self.afterevent_timespan = NoSave(ConfigEnableDisable(default = default))
		self.afterevent_timespanbegin = NoSave(ConfigClock(default = begin))
		self.afterevent_timespanend = NoSave(ConfigClock(default = end))

		# Enabled
		self.enabled = NoSave(ConfigYesNo(default = timer.enabled))

		# Maxduration
		if timer.hasDuration():
			default = True
			duration = timer.getDuration()
		else:
			default = False
			duration =70
		self.duration = NoSave(ConfigEnableDisable(default = default))
		self.durationlength = NoSave(ConfigNumber(default = duration))

		# Counter
		if timer.hasCounter():
			default = timer.matchCount
		else:
			default = 0
		self.counter = NoSave(ConfigNumber(default = default))
		self.counterLeft = NoSave(ConfigNumber(default = timer.matchLeft))
		default = timer.getCounterFormatString()
		selection = [("", _("Never")), ("%m", _("Monthly")), ("%U", _("Weekly (Sunday)")), ("%W", _("Weekly (Monday)"))]
		if default not in ('', '%m', '%U', '%W'):
			selection.append((default, _("Custom (%s)") % (default)))
		self.counterFormatString = NoSave(ConfigSelection(selection, default = default))

		# Avoid Duplicate Description
		self.avoidDuplicateDescription = NoSave(ConfigSelection([
				("0", _("No")),
				("1", _("On same service")),
				("2", _("On any service")),
			],
			default = str(timer.getAvoidDuplicateDescription())
		))

		# Custom Location
		if timer.hasDestination():
			default = True
		else:
			default = False

		self.useDestination = NoSave(ConfigYesNo(default = default))

		default = timer.destination or Directories.resolveFilename(Directories.SCOPE_HDD)
		choices = config.movielist.videodirs.value

		if default not in choices:
			choices.append(default)
		self.destination = NoSave(ConfigSelection(default = default, choices = choices))

		# Tags
		self.timerentry_tags = timer.tags
		self.tags = NoSave(ConfigSelection(choices = [len(self.timerentry_tags) == 0 and _("None") or ' '.join(self.timerentry_tags)]))

	def pathSelected(self, res):
		if res is not None:
			# I'm pretty sure this will always fail
			if config.movielist.videodirs.value != self.destination.choices:
					self.destination.setChoices(config.movielist.videodirs.value, default = res)
			self.destination.value = res

	def chooseDestination(self):
		from Screens.LocationBox import MovieLocationBox

		self.session.openWithCallback(
			self.pathSelected,
			MovieLocationBox,
			_("Choose target folder"),
			self.destination.value,
			minFree = 100 # Same requirement as in Screens.TimerEntry
		)

	def tagEditFinished(self, ret):
		if ret is not None:
			self.timerentry_tags = ret
			self.tags.setChoices([len(ret) == 0 and _("None") or ' '.join(ret)])

	def chooseTags(self):
		preferredTagEditor = getPreferredTagEditor()
		if preferredTagEditor:
			self.session.openWithCallback(
				self.tagEditFinished,
				preferredTagEditor,
				self.timerentry_tags
			)

class AutoTimerEditor(Screen, ConfigListScreen, AutoTimerEditorBase):
	"""Edit AutoTimer"""

	skin = """<screen name="AutoTimerEdit" title="Edit AutoTimer" position="75,155" size="565,280">
		<widget name="config" position="5,5" size="555,225" scrollbarMode="showOnDemand" />
		<ePixmap position="0,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="280,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="420,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, timer, editingDefaults = False):
		Screen.__init__(self, session)

		AutoTimerEditorBase.__init__(self, timer, editingDefaults)

		# Summary
		self.setup_title = _("AutoTimer Editor")
		self.onChangedEntry = []

		# We might need to change shown items, so add some notifiers
		self.timespan.addNotifier(self.reloadList, initial_call = False)
		self.offset.addNotifier(self.reloadList, initial_call = False)
		self.duration.addNotifier(self.reloadList, initial_call = False)
		self.afterevent.addNotifier(self.reloadList, initial_call = False)
		self.afterevent_timespan.addNotifier(self.reloadList, initial_call = False)
		self.counter.addNotifier(self.reloadList, initial_call = False)
		self.useDestination.addNotifier(self.reloadList, initial_call = False)

		self.refresh()

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button()
 		self["key_blue"] = Button()

		# Set Button texts
		self.renameServiceButton()
		self.renameFilterButton()

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.maybeSave,
				"ok": self.ok,
				"yellow": self.editFilter,
				"blue": self.editServices
			}, -2
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Edit AutoTimer"))

	def renameFilterButton(self):
		if self.filterSet:
			self["key_yellow"].setText(_("Edit Filters"))
		else:
			self["key_yellow"].setText(_("Add Filters"))

	def renameServiceButton(self):
		if self.serviceRestriction:
			self["key_blue"].setText(_("Edit Services"))
		else:
			self["key_blue"].setText(_("Add Services"))

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def refresh(self):
		# First three entries are only showed when not editing defaults
		list = []
		if not self.editingDefaults:
			list.extend((
				getConfigListEntry(_("Enabled"), self.enabled),
				getConfigListEntry(_("Description"), self.name),
				getConfigListEntry(_("Match Title"), self.match),
			))

		list.extend((
			getConfigListEntry(_("EPG Encoding"), self.encoding),
			getConfigListEntry(_("Search Type"), self.searchType),
			getConfigListEntry(_("Search strictness"), self.searchCase),
			getConfigListEntry(_("Timer Type"), self.justplay),
			getConfigListEntry(_("Only match during Timespan"), self.timespan)
		))

		# Only allow editing timespan when it's enabled
		if self.timespan.value:
			list.extend((
				getConfigListEntry(_("Begin of Timespan"), self.timespanbegin),
				getConfigListEntry(_("End of Timespan"), self.timespanend)
			))

		list.append(getConfigListEntry(_("Custom offset"), self.offset))

		# Only allow editing offsets when it's enabled
		if self.offset.value:
			list.extend((
				getConfigListEntry(_("Offset before recording (in m)"), self.offsetbegin),
				getConfigListEntry(_("Offset after recording (in m)"), self.offsetend)
			))

		list.append(getConfigListEntry(_("Set maximum Duration"), self.duration))

		# Only allow editing maxduration when it's enabled
		if self.duration.value:
			list.append(getConfigListEntry(_("Maximum Duration (in m)"), self.durationlength))

		list.append(getConfigListEntry(_("After event"), self.afterevent))

		# Only allow setting afterevent timespan when afterevent is active
		if self.afterevent.value != "default":
			list.append(getConfigListEntry(_("Execute after Event during Timespan"), self.afterevent_timespan))

			# Only allow editing timespan when it's enabled
			if self.afterevent_timespan.value:
				list.extend((
					getConfigListEntry(_("Begin of after Event Timespan"), self.afterevent_timespanbegin),
					getConfigListEntry(_("End of after Event Timespan"), self.afterevent_timespanend)
				))

		list.append(getConfigListEntry(_("Record a maximum of x times"), self.counter))

		# Only allow setting matchLeft when counting hits
		if self.counter.value:
			if not self.editingDefaults:
				list.append(getConfigListEntry(_("Ammount of recordings left"), self.counterLeft))
			list.append(getConfigListEntry(_("Reset Count"), self.counterFormatString))

		list.append(getConfigListEntry(_("Require Description to be unique"), self.avoidDuplicateDescription))

		# We always add this option though its expert only in enigma2
		list.append(getConfigListEntry(_("Use a custom location"), self.useDestination))
		if self.useDestination.value:
			list.append(getConfigListEntry(_("Custom Location"), self.destination))

		list.append(getConfigListEntry(_("Tags"), self.tags))

		self.list = list

	def reloadList(self, value):
		self.refresh()
		self["config"].setList(self.list)

	def editFilter(self):
		self.session.openWithCallback(
			self.editFilterCallback,
			AutoTimerFilterEditor,
			self.filterSet,
			self.excludes,
			self.includes
		)

	def editFilterCallback(self, ret):
		if ret:
			self.filterSet = ret[0]
			self.excludes = ret[1]
			self.includes = ret[2]
			self.renameFilterButton()

	def editServices(self):
		self.session.openWithCallback(
			self.editServicesCallback,
			AutoTimerServiceEditor,
			self.serviceRestriction,
			self.services,
			self.bouquets
		)

	def editServicesCallback(self, ret):
		if ret:
			self.serviceRestriction = ret[0]
			self.services = ret[1][0]
			self.bouquets = ret[1][1]
			self.renameServiceButton()

	def ok(self):
		cur = self["config"].getCurrent()
		cur = cur and cur[1]
		if cur == self.destination:
			self.chooseDestination()
		elif cur == self.tags:
			self.chooseTags()
		else:
			ConfigListScreen.keyOK(self)

	def cancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving settings?")
			)
		else:
			self.close(None)

	def cancelConfirm(self, ret):
		if ret:
			self.close(None)

	def maybeSave(self):
		if self.editingDefaults:
			self.save()
			return
		# Check if any match is set
		if not self.match.value.strip():
			self.session.open(
					MessageBox,
					_("The match attribute is mandatory."),
					type = MessageBox.TYPE_ERROR,
					timeout = 5
			)
		# Check if we have a trailing whitespace
		elif self.match.value[-1:] == " ":
			self.session.openWithCallback(
				self.saveCallback,
				MessageBox,
				_('You entered "%s" as Text to match.\nDo you want to remove trailing whitespaces?') % (self.match.value)
			)
		# Just save else
		else:
			self.save()

	def saveCallback(self, ret):
		if ret is not None:
			if ret:
				self.match.value = self.match.value.rstrip()
			self.save()
		# Don't to anything if MessageBox was canceled!

	def save(self):
		# Match
		self.timer.match = self.match.value

		# Name
		self.timer.name = self.name.value.strip() or self.timer.match

		# Encoding
		self.timer.encoding = self.encoding.value

		# ...
		self.timer.searchType = self.searchType.value
		self.timer.searchCase = self.searchCase.value

		# Enabled
		self.timer.enabled = self.enabled.value

		# Justplay
		self.timer.justplay = self.justplay.value == "zap"

		# Timespan
		if self.timespan.value:
			start = self.timespanbegin.value
			end = self.timespanend.value
			self.timer.timespan = (start, end)
		else:
			self.timer.timespan = None

		# Services
		if self.serviceRestriction:
			self.timer.services = self.services
			self.timer.bouquets = self.bouquets
		else:
			self.timer.services = None
			self.timer.bouquets = None

		# Offset
		if self.offset.value:
			self.timer.offset = (self.offsetbegin.value*60, self.offsetend.value*60)
		else:
			self.timer.offset = None

		# AfterEvent
		if self.afterevent.value == "default":
			self.timer.afterevent = []
		else:
			afterevent = {
				"nothing": AFTEREVENT.NONE,
				"deepstandby": AFTEREVENT.DEEPSTANDBY,
				"standby": AFTEREVENT.STANDBY,
				"auto": AFTEREVENT.AUTO
			}[self.afterevent.value]
			# AfterEvent Timespan
			if self.afterevent_timespan.value:
				start = self.afterevent_timespanbegin.value
				end = self.afterevent_timespanend.value
				self.timer.afterevent = [(afterevent, (start, end))]
			else:
				self.timer.afterevent = [(afterevent, None)]

		# Maxduration
		if self.duration.value:
			self.timer.maxduration = self.durationlength.value*60
		else:
			self.timer.maxduration = None

		# Ex-&Includes
		if self.filterSet:
			self.timer.exclude = self.excludes
			self.timer.include = self.includes
		else:
			self.timer.exclude = None
			self.timer.include = None

		# Counter
		if self.counter.value:
			self.timer.matchCount = self.counter.value
			if self.counterLeft.value <= self.counter.value:
				self.timer.matchLeft = self.counterLeft.value
			else:
				self.timer.matchLeft = self.counter.value
			if self.counterFormatString.value:
				self.timer.matchFormatString = self.counterFormatString.value
			else:
				self.timer.matchFormatString = ''
		else:
			self.timer.matchCount = 0
			self.timer.matchLeft = 0
			self.timer.matchFormatString = ''

		self.timer.avoidDuplicateDescription = int(self.avoidDuplicateDescription.value)

		if self.useDestination.value:
			self.timer.destination = self.destination.value
		else:
			self.timer.destination = None

		self.timer.tags = self.timerentry_tags

		# Close
		self.close(self.timer)

class AutoTimerFilterEditor(Screen, ConfigListScreen):
	"""Edit AutoTimer Filter"""

	skin = """<screen name="AutoFilterEditor" title="Edit AutoTimer Filters" position="75,150" size="565,245">
		<widget name="config" position="5,5" size="555,200" scrollbarMode="showOnDemand" />
		<ePixmap position="5,205" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="145,205" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="285,205" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="425,205" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="5,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="145,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="285,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="425,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, filterset, excludes, includes):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = _("AutoTimer Filters")
		self.onChangedEntry = []

		self.typeSelection = NoSave(ConfigSelection(choices = [
			("title", _("in Title")),
			("short", _("in Shortdescription")),
			("desc", _("in Description")),
			("day", _("on Weekday"))]
		))
		self.typeSelection.addNotifier(self.refresh, initial_call = False)

		self.enabled = NoSave(ConfigEnableDisable(default = filterset))

		self.excludes = excludes
		self.includes = includes

		self.reloadList()

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_("delete"))
		self["key_blue"] = Button(_("New"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.remove,
				"blue": self.new
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Edit AutoTimer Filters"))


	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def saveCurrent(self):
		del self.excludes[self.idx][:]
		del self.includes[self.idx][:]

		# Warning, accessing a ConfigListEntry directly might be considered evil!

		idx = -1
		for item in self["config"].getList()[:]:
			idx += 1
			# Skip empty entries (and those which are no filters)
			if item[1].value == "" or idx < 2:
				continue
			elif idx < self.lenExcludes:
				self.excludes[self.idx].append(item[1].value.encode("UTF-8"))
			else:
				self.includes[self.idx].append(item[1].value.encode("UTF-8"))

	def refresh(self, *args, **kwargs):
		self.saveCurrent()

		self.reloadList()
		self["config"].setList(self.list)

	def reloadList(self):
		self.list = [
			getConfigListEntry(_("Enable Filtering"), self.enabled),
			getConfigListEntry(_("Filter"), self.typeSelection)
		]

		if self.typeSelection.value == "day":
			self.idx = 3

			# Weekdays are presented as ConfigSelection
			self.list.extend([
				getConfigListEntry(_("Exclude"), NoSave(ConfigSelection(choices = weekdays, default = x)))
					for x in self.excludes[3]
			])
			self.lenExcludes = len(self.list)
			self.list.extend([
				getConfigListEntry(_("Include"), NoSave(ConfigSelection(choices = weekdays, default = x)))
					for x in self.includes[3]
			])
			return
		elif self.typeSelection.value == "title":
			self.idx = 0
		elif self.typeSelection.value == "short":
			self.idx = 1
		else: # self.typeSelection.value == "desc":
			self.idx = 2

		self.list.extend([
			getConfigListEntry(_("Exclude"), NoSave(ExtendedConfigText(default = x, fixed_size = False)))
				for x in self.excludes[self.idx]
		])
		self.lenExcludes = len(self.list)
		self.list.extend([
			getConfigListEntry(_("Include"), NoSave(ExtendedConfigText(default = x, fixed_size = False)))
				for x in self.includes[self.idx]
		])

	def remove(self):
		idx = self["config"].getCurrentIndex()
		if idx and idx > 1:
			if idx < self.lenExcludes:
				self.lenExcludes -= 1

			list = self["config"].getList()
			list.remove(self["config"].getCurrent())
			self["config"].setList(list)

	def new(self):
		self.session.openWithCallback(
			self.typeSelected,
			ChoiceBox,
			_("Select type of Filter"),
			[
				(_("Exclude"), 0),
				(_("Include"), 1),
			]
		)

	def typeSelected(self, ret):
		if ret is not None:
			list = self["config"].getList()

			if ret[1] == 0:
				pos = self.lenExcludes
				self.lenExcludes += 1
				text = ret[0]
			else:
				pos = len(self.list)
				text = ret[0]

			if self.typeSelection.value == "day":
				entry = getConfigListEntry(text, NoSave(ConfigSelection(choices = weekdays)))
			else:
				entry = getConfigListEntry(text, NoSave(ExtendedConfigText(fixed_size = False)))

			list.insert(pos, entry)
			self["config"].setList(list)

	def cancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving settings?")
			)
		else:
			self.close(None)

	def cancelConfirm(self, ret):
		if ret:
			self.close(None)

	def save(self):
		self.refresh()

		self.close((
			self.enabled.value,
			self.excludes,
			self.includes
		))

class AutoTimerServiceEditor(Screen, ConfigListScreen):
	"""Edit allowed Services of a AutoTimer"""

	skin = """<screen name="AutoTimerServiceEditor" title="Edit AutoTimer Services" position="75,150" size="565,245">
		<widget name="config" position="5,5" size="555,200" scrollbarMode="showOnDemand" />
		<ePixmap position="5,205" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="145,205" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="285,205" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="425,205" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="5,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="145,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="285,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="425,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, servicerestriction, servicelist, bouquetlist):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = _("AutoTimer Services")
		self.onChangedEntry = []

		self.services = (
			servicelist[:],
			bouquetlist[:]
		)

		self.enabled = NoSave(ConfigEnableDisable(default = servicerestriction))
		self.typeSelection = NoSave(ConfigSelection(choices = [
			("channels", _("Channels")),
			("bouquets", _("Bouquets"))]
		))
		self.typeSelection.addNotifier(self.refresh, initial_call = False)

		self.reloadList()

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button(_("delete"))
		self["key_blue"] = Button(_("New"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.remove,
				"blue": self.new
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Edit AutoTimer Services"))

	def saveCurrent(self):
		del self.services[self.idx][:]

		# Warning, accessing a ConfigListEntry directly might be considered evil!

		myl = self["config"].getList()[:]
		myl.pop(0) # Enabled
		myl.pop(0) # Type
		for item in myl:
			self.services[self.idx].append(item[1].value)

	def refresh(self, *args, **kwargs):
		self.saveCurrent()

		self.reloadList()
		self["config"].setList(self.list)

	def reloadList(self):
		self.list = [
			getConfigListEntry(_("Enable Service Restriction"), self.enabled),
			getConfigListEntry(_("Editing"), self.typeSelection)
		]

		if self.typeSelection.value == "channels":
			self.idx = 0
		else: # self.typeSelection.value == "bouquets":
			self.idx = 1

		self.list.extend([
			getConfigListEntry(_("Record on"), NoSave(ConfigSelection(choices = [(str(x), ServiceReference(str(x)).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''))])))
				for x in self.services[self.idx]
		])

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def remove(self):
		if self["config"].getCurrentIndex() != 0:
			list = self["config"].getList()
			list.remove(self["config"].getCurrent())
			self["config"].setList(list)

	def new(self):
		if self.typeSelection.value == "channels":
			self.session.openWithCallback(
				self.finishedServiceSelection,
				SimpleChannelSelection,
				_("Select channel to record on")
			)
		else: # self.typeSelection.value == "bouquets":
			self.session.openWithCallback(
				self.finishedServiceSelection,
				SimpleBouquetSelection,
				_("Select bouquet to record on")
			)

	def finishedServiceSelection(self, *args):
		if args:
			list = self["config"].getList()
			sname = args[0].toString()

			if self.typeSelection.value == "channels":
				# strip all after last : when adding a channel
				pos = sname.rfind(':')
				if pos != -1:
					sname = sname[:pos+1]

			list.append(getConfigListEntry(_("Record on"), NoSave(ConfigSelection(choices = [(sname, ServiceReference(args[0]).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''))]))))
			self["config"].setList(list)

	def cancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving settings?")
			)
		else:
			self.close(None)

	def cancelConfirm(self, ret):
		if ret:
			self.close(None)

	def save(self):
		self.refresh()

		self.close((
			self.enabled.value,
			self.services
		))

def addAutotimerFromSearchString(session, match):
	from AutoTimerComponent import AutoTimerComponent
	from AutoTimerImporter import AutoTimerImporter
	from plugin import autotimer

	# Create instance if needed
	if autotimer is None:
		from AutoTimer import AutoTimer
		autotimer = AutoTimer()
		autotimer.readXml()

	session.openWithCallback(
		importerCallback,
		AutoTimerImporter,
		AutoTimerComponent(
			autotimer.getUniqueId(),
			match,
			'',		# Match
			True	# Enabled
		),
		match,		# Proposed Match
		None,		# Proposed Begin
		None,		# Proposed End
		None,		# Proposed Disabled
		None,		# Proposed ServiceReference
		None,		# Proposed afterEvent
		None,		# Proposed justplay
		None,		# Proposed dirname, can we get anything useful here?
		[]			# Proposed tags
	)

def addAutotimerFromEvent(session, evt = None, service = None):
	from AutoTimerComponent import AutoTimerComponent
	from AutoTimerImporter import AutoTimerImporter
	from plugin import autotimer

	# Create instance if needed
	if autotimer is None:
		from AutoTimer import AutoTimer
		autotimer = AutoTimer()
		autotimer.readXml()

	match = evt and evt.getEventName() or ""
	name = match or "New AutoTimer"
	sref = None
	if service is not None:
		service = str(service)
		# strip all after last :
		pos = service.rfind(':')
		if pos != -1:
			service = service[:pos+1]

		sref = ServiceReference(service)
	if evt:
		# timespan defaults to +- 1h
		begin = evt.getBeginTime()-3600
		end = begin + evt.getDuration()+7200
	else:
		begin = end = 0

	# XXX: we might want to make sure that we actually collected any data because the importer does not do so :-)

	session.openWithCallback(
		importerCallback,
		AutoTimerImporter,
		AutoTimerComponent(
			autotimer.getUniqueId(),
			name,
			'',		# Match
			True	# Enabled
		),
		match,		# Proposed Match
		begin,		# Proposed Begin
		end,		# Proposed End
		None,		# Proposed Disabled
		sref,		# Proposed ServiceReference
		None,		# Proposed afterEvent
		None,		# Proposed justplay
		None,		# Proposed dirname, can we get anything useful here?
		[]			# Proposed tags
	)

def addAutotimerFromService(session, service = None):
	from AutoTimerComponent import AutoTimerComponent
	from AutoTimerImporter import AutoTimerImporter
	from plugin import autotimer

	# Create instance if needed
	if autotimer is None:
		from AutoTimer import AutoTimer
		autotimer = AutoTimer()
		autotimer.readXml()

	serviceHandler = eServiceCenter.getInstance()
	info = serviceHandler.info(service)

	match = info and info.getName(service) or ""
	name = match or "New AutoTimer"
	sref = info and info.getInfoString(service, iServiceInformation.sServiceref)
	if sref:
		# strip all after last :
		pos = sref.rfind(':')
		if pos != -1:
			sref = sref[:pos+1]

		sref = ServiceReference(sref)
	if info:
		begin = info.getInfo(service, iServiceInformation.sTimeCreate)
		end = begin + info.getLength(service)
	else:
		begin = end = 0

	from os.path import dirname
	path = dirname(service.getPath())
	if not path == '/':
		path += '/'

	tags = info.getInfoString(service, iServiceInformation.sTags)
	tags = tags and tags.split(' ') or []

	# XXX: we might want to make sure that we actually collected any data because the importer does not do so :-)

	session.openWithCallback(
		importerCallback,
		AutoTimerImporter,
		AutoTimerComponent(
			autotimer.getUniqueId(),
			name,
			'',		# Match
			True	# Enabled
		),
		match,		# Proposed Match
		begin,		# Proposed Begin
		end,		# Proposed End
		None,		# Proposed Disabled
		sref,		# Proposed ServiceReference
		None,		# Proposed afterEvent
		None,		# Proposed justplay
		path,		# Proposed dirname
		tags		# Proposed tags
	)

def importerCallback(ret):
	if ret:
		ret, session = ret

		session.openWithCallback(
			editorCallback,
			AutoTimerEditor,
			ret
		)
	else:
		# Remove instance if not running in background
		if not config.plugins.autotimer.autopoll.value:
			from plugin import autotimer
			autotimer = None

def editorCallback(ret):
	if ret:
		from plugin import autotimer

		# Create instance if needed (should have been created by addAutotimerFrom* above though)
		if autotimer is None:
			from AutoTimer import AutoTimer
			autotimer = AutoTimer()
			autotimer.readXml()

		autotimer.add(ret)

		# Save modified xml
		autotimer.writeXml()

	# Remove instance if not running in background
	if not config.plugins.autotimer.autopoll.value:
		autotimer = None

