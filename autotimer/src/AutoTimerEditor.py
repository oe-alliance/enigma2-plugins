# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Screens.ChannelSelection import SimpleChannelSelection
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
	config

# Timer
from RecordTimer import AFTEREVENT

# Needed to convert our timestamp back and forth
from time import localtime, mktime

# Show ServiceName instead of ServiceReference
from ServiceReference import ServiceReference

# addAutotimerFromService
from enigma import eServiceCenter, iServiceInformation

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

class SimpleBouquetSelection(SimpleChannelSelection):
	def __init__(self, session, title):
		SimpleChannelSelection.__init__(self, session, title)
		self.skinName = "SimpleChannelSelection"

	def channelSelected(self): # just return selected service
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.close(ref)
		else:
			# We return the currently active path here
			# Asking the user if this is what he wants might be better though
			self.close(self.servicePath[-1])

class AutoTimerEditor(Screen, ConfigListScreen):
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

		# Keep Timer
		self.timer = timer
		self.editingDefaults = editingDefaults

		# Summary
		self.setup_title = "AutoTimer Editor"
		self.onChangedEntry = []

		# See if we are filtering some strings
		self.excludes = (
			timer.getExcludedTitle(),
			timer.getExcludedShort(),
			timer.getExcludedDescription(),
			timer.getExcludedDays()
		)
		self.includes = (
			timer.getIncludedTitle(),
			timer.getIncludedShort(),
			timer.getIncludedDescription(),
			timer.getIncludedDays()
		)
		if len(self.excludes[0]) or len(self.excludes[1]) \
				or len(self.excludes[2]) or len(self.excludes[3]) \
				or len(self.includes[0]) or len(self.includes[1]) \
				or len(self.includes[2]) or len(self.includes[3]):
			self.filterSet = True
		else:
			self.filterSet = False

		# See if services are restricted
		self.services = timer.getServices()
		self.bouquets = timer.getBouquets()
		if len(self.services) or len(self.bouquets):
			self.serviceRestriction = True
		else:
			self.serviceRestriction = False

		self.createSetup(timer)

		# We might need to change shown items, so add some notifiers
		self.timespan.addNotifier(self.reloadList, initial_call = False)
		self.offset.addNotifier(self.reloadList, initial_call = False)
		self.duration.addNotifier(self.reloadList, initial_call = False)
		self.afterevent.addNotifier(self.reloadList, initial_call = False)
		self.afterevent_timespan.addNotifier(self.reloadList, initial_call = False)
		self.counter.addNotifier(self.reloadList, initial_call = False)

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
			except:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def createSetup(self, timer):
		# Name
		self.name = ConfigText(default = timer.name, fixed_size = False)

		# Match
		self.match = ConfigText(default = timer.match, fixed_size = False)
		self.match.setUseableChars('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789') # XXX: what exactly is useable? :-)

		# Justplay
		self.justplay = ConfigSelection(choices = [("zap", _("zap")), ("record", _("record"))], default = {0: "record", 1: "zap"}[int(timer.justplay)])

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
		self.timespan = ConfigEnableDisable(default = default)
		self.timespanbegin = ConfigClock(default = begin)
		self.timespanend = ConfigClock(default = end)

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
		self.offset = ConfigEnableDisable(default = default)
		self.offsetbegin = ConfigNumber(default = begin)
		self.offsetend = ConfigNumber(default = end)

		# AfterEvent
		if timer.hasAfterEvent():
			afterevent = { None: "default", AFTEREVENT.NONE: "nothing", AFTEREVENT.DEEPSTANDBY: "deepstandby", AFTEREVENT.STANDBY: "standby"}[timer.afterevent[0][0]]
		else:
			afterevent = "default"
		self.afterevent = ConfigSelection(choices = [("default", _("standard")), ("nothing", _("do nothing")), ("standby", _("go to standby")), ("deepstandby", _("go to deep standby"))], default = afterevent)

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
		self.afterevent_timespan = ConfigEnableDisable(default = default)
		self.afterevent_timespanbegin = ConfigClock(default = begin)
		self.afterevent_timespanend = ConfigClock(default = end)

		# Enabled
		self.enabled = ConfigYesNo(default = timer.enabled)

		# Maxduration
		if timer.hasDuration():
			default = True
			duration = timer.getDuration()
		else:
			default = False
			duration =70
		self.duration = ConfigEnableDisable(default = default)
		self.durationlength = ConfigNumber(default = duration)

		# Counter
		if timer.hasCounter():
			default = timer.matchCount
		else:
			default = 0
		self.counter = ConfigNumber(default = default)
		self.counterLeft = ConfigNumber(default = timer.matchLeft)
		selection = [("", _("Never")), ("%m", _("Monthly")), ("%U", _("Weekly (Sunday)")), ("%W", _("Weekly (Monday)"))]
		if timer.getCounterFormatString() not in ["", "%m", "%U", "%W"]:
			selection.append((timer.getCounterFormatString(), _("Custom (%s)") % (timer.getCounterFormatString())))
		self.counterFormatString = ConfigSelection(selection, default = timer.getCounterFormatString())

		# Avoid Duplicate Description
		self.avoidDuplicateDescription = ConfigEnableDisable(default = timer.getAvoidDuplicateDescription())

		# Custom Location
		self.destination = ConfigSelection(choices = [timer.destination or "/hdd/movie/"])

	def refresh(self):
		# First three entries are only showed when not editing defaults
		self.list = []
		if not self.editingDefaults:
			self.list.extend([
				getConfigListEntry(_("Enabled"), self.enabled),
				getConfigListEntry(_("Description"), self.name),
				getConfigListEntry(_("Match Title"), self.match),
			])

		self.list.extend([
			getConfigListEntry(_("Timer Type"), self.justplay),
			getConfigListEntry(_("Only match during Timespan"), self.timespan)
		])

		# Only allow editing timespan when it's enabled
		if self.timespan.value:
			self.list.extend([
				getConfigListEntry(_("Begin of Timespan"), self.timespanbegin),
				getConfigListEntry(_("End of Timespan"), self.timespanend)
			])

		self.list.append(getConfigListEntry(_("Custom offset"), self.offset))

		# Only allow editing offsets when it's enabled
		if self.offset.value:
			self.list.extend([
				getConfigListEntry(_("Offset before recording (in m)"), self.offsetbegin),
				getConfigListEntry(_("Offset after recording (in m)"), self.offsetend)
			])

		self.list.append(getConfigListEntry(_("Set maximum Duration"), self.duration))

		# Only allow editing maxduration when it's enabled
		if self.duration.value:
			self.list.extend([
				getConfigListEntry(_("Maximum Duration (in m)"), self.durationlength)
			])

		self.list.append(getConfigListEntry(_("After event"), self.afterevent))

		# Only allow setting afterevent timespan when afterevent is active
		if self.afterevent.value != "default":
			self.list.append(getConfigListEntry(_("Execute after Event during Timespan"), self.afterevent_timespan))

			# Only allow editing timespan when it's enabled
			if self.afterevent_timespan.value:
				self.list.extend([
					getConfigListEntry(_("Begin of after Event Timespan"), self.afterevent_timespanbegin),
					getConfigListEntry(_("End of after Event Timespan"), self.afterevent_timespanend)
				])

		self.list.append(getConfigListEntry(_("Record a maximum of x times"), self.counter))

		# Only allow setting matchLeft when counting hits
		if self.counter.value:
			if not self.editingDefaults:
				self.list.append(getConfigListEntry(_("Ammount of recordings left"), self.counterLeft))
			self.list.append(getConfigListEntry(_("Reset Count"), self.counterFormatString))

		self.list.append(getConfigListEntry(_("Require Description to be unique"), self.avoidDuplicateDescription))

		# We always add this option though its actually expert only
		self.list.append(getConfigListEntry(_("Custom Location"), self.destination))

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
			from Screens.LocationBox import LocationBox

			self.session.openWithCallback(
				self.pathSelected,
				LocationBox,
				text = _("Choose target folder"),
				filename = "",
				currDir = self.destination.value
			)
		else:
			ConfigListScreen.keyOK(self)

	def pathSelected(self, res):
		if res is not None:
			self.destination.choices.append(res)
			self.destination.description[res] = res
			self.destination.value = res

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
		# Check if we have a trailing whitespace
		if self.match.value[-1:] == " ":
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
		self.timer.name = self.name.value or self.timer.match

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
			afterevent = {"nothing": AFTEREVENT.NONE, "deepstandby": AFTEREVENT.DEEPSTANDBY, "standby": AFTEREVENT.STANDBY}[self.afterevent.value]
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

		self.timer.avoidDuplicateDescription = self.avoidDuplicateDescription.value

		if self.destination.value == "/hdd/movie/":
			self.timer.destination = None
		else:
			self.timer.destination = self.destination.value

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
		self.setup_title = "AutoTimer Filters"
		self.onChangedEntry = []

		self.typeSelection = ConfigSelection(choices = [("title", _("in Title")), ("short", _("in Shortdescription")), ("desc", _("in Description")), ("day", _("on Weekday"))])
		self.typeSelection.addNotifier(self.refresh, initial_call = False)

		self.enabled = ConfigEnableDisable(default = filterset)

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

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except:
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
		for item in self["config"].getList():
			idx += 1
			# Skip empty entries (and those which are no filters)
			if item[1].value == "" or idx < 2:
				continue
			elif idx < self.lenExcludes:
				self.excludes[self.idx].append(item[1].value.encode("UTF-8"))
			else:
				self.includes[self.idx].append(item[1].value.encode("UTF-8"))

	def refresh(self, value):
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
				getConfigListEntry(_("Exclude"), ConfigSelection(choices = weekdays, default = x))
					for x in self.excludes[3]
			])
			self.lenExcludes = len(self.list)
			self.list.extend([
				getConfigListEntry(_("Include"), ConfigSelection(choices = weekdays, default = x))
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
			getConfigListEntry(_("Exclude"), ConfigText(default = x, fixed_size = False))
				for x in self.excludes[self.idx]
		])
		self.lenExcludes = len(self.list)
		self.list.extend([
			getConfigListEntry(_("Include"), ConfigText(default = x, fixed_size = False))
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
				entry = getConfigListEntry(text, ConfigSelection(choices = weekdays))
			else:
				entry = getConfigListEntry(text, ConfigText(fixed_size = False))

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
		self.saveCurrent()

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
		self.setup_title = "AutoTimer Services"
		self.onChangedEntry = []

		self.services = (
			servicelist[:],
			bouquetlist[:]
		)

		self.enabled = ConfigEnableDisable(default = servicerestriction)
		self.typeSelection = ConfigSelection(choices = [("channels", _("Channels")), ("bouquets", _("Bouquets"))])
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

	
	def saveCurrent(self):
		del self.services[self.idx][:]
		
		# Warning, accessing a ConfigListEntry directly might be considered evil!

		myl = self["config"].getList()
		myl.pop(0) # Enabled
		myl.pop(0) # Type
		for item in myl:
			self.services[self.idx].append(item[1].value)

	def refresh(self, value):
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
			getConfigListEntry(_("Record on"), ConfigSelection(choices = [(str(x), ServiceReference(str(x)).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''))]))
				for x in self.services[self.idx]
		])

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except:
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
		if len(args):
			list = self["config"].getList()
			sname = args[0].toString()

			if self.typeSelection.value == "channels":
				# strip all after last : when adding a channel
				pos = sname.rfind(':')
				if pos != -1:
					sname = sname[:pos+1]

			list.append(getConfigListEntry(_("Record on"), ConfigSelection(choices = [(sname, ServiceReference(args[0]).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''))])))
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
		self.saveCurrent()

		self.close((
			self.enabled.value,
			self.services
		))

def addAutotimerFromEvent(session, evt = None, service = None):
	from AutoTimerComponent import AutoTimerComponent
	from AutoTimerImporter import AutoTimerImporter
	from plugin import autotimer
		
	# Create instance if needed
	if autotimer is None:
		from AutoTimer import AutoTimer
		autotimer = AutoTimer()

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
			autotimer.getUniqueId(),	  	# Id
			name,	   						# Name
			"",								# Match
			True							# Enabled
		),
		match,  	   	   # Proposed Match
		begin,  	   	   # Proposed Begin
		end,	   	   	   # Proposed End
		None, 	   	   	   # Proposed Disabled
		sref,   		   # Proposed ServiceReference
		None,   	       # Proposed afterEvent 
		None,  	   	   	   # Proposed justplay 
		None  	   	   	   # Proposed dirname, can we get anything useful here? 
	)

def addAutotimerFromService(session, service = None):	
	from AutoTimerComponent import AutoTimerComponent
	from AutoTimerImporter import AutoTimerImporter
	from plugin import autotimer
		
	# Create instance if needed
	if autotimer is None:
		from AutoTimer import AutoTimer
		autotimer = AutoTimer()

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

	# XXX: we might want to make sure that we actually collected any data because the importer does not do so :-)

	session.openWithCallback(
		importerCallback,
		AutoTimerImporter,
		AutoTimerComponent(
			autotimer.getUniqueId(),	  	# Id
			name,	   						# Name
			"",								# Match
			True							# Enabled
		),
		match,	   	   	   # Proposed Match
		begin,	   	   	   # Proposed Begin
		end,	   	   	   # Proposed End
		None, 	 	   	   # Proposed Disabled
		sref,   		   # Proposed ServiceReference
		None,   	       # Proposed afterEvent 
		None,  	   	   	   # Proposed justplay 
		None  	   	   	   # Proposed dirname, can we get anything useful here? 
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

		autotimer.add(ret)
		
	# Remove instance if not running in background
	if not config.plugins.autotimer.autopoll.value:
		# Save xml (as long as we added something)
		ret and autotimer and autotimer.writeXml()
		autotimer = None
