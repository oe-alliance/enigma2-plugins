# -*- coding: UTF-8 -*-
# for localized messages
from . import _

# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.SelectionList import SelectionList, SelectionEntryComponent
from Components.Sources.StaticText import StaticText
from Components.TimerList import TimerList

# Timer
from RecordTimer import AFTEREVENT

# Needed to convert our timestamp back and forth
from time import localtime
from AutoTimerEditor import weekdays

from enigma import eServiceReference

afterevent = {
	AFTEREVENT.NONE: _("do nothing"),
	AFTEREVENT.DEEPSTANDBY: _("go to deep standby"),
	AFTEREVENT.STANDBY: _("go to standby"),
	AFTEREVENT.AUTO: _("auto")
}

class AutoTimerImportSelector(Screen):
	def __init__(self, session, autotimer):
		Screen.__init__(self, session)
		self.skinName = "TimerEditList"

		self.autotimer = autotimer

		self.list = []
		self.fillTimerList()

		self["timerlist"] = TimerList(self.list)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.openImporter,
			"cancel": self.cancel,
			"green": self.openImporter,
			"red": self.cancel
		}, -1)
		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Select a timer to import"))

	def fillTimerList(self):
		l = self.list
		del l[:]

		l.extend([(timer, False) for timer in self.session.nav.RecordTimer.timer_list])
		l.extend([(timer, True) for timer in self.session.nav.RecordTimer.processed_timers])
		l.sort(key = lambda x: x[0].begin)

	def importerClosed(self, ret):
		ret = ret and ret[0]
		if ret is not None:
			ret.name = ret.match
		self.close(ret)

	def openImporter(self):
		cur=self["timerlist"].getCurrent()
		if cur:
			self.session.openWithCallback(
				self.importerClosed,
				AutoTimerImporter,
				self.autotimer,
				cur.name,
				cur.begin,
				cur.end,
				cur.disabled,
				cur.service_ref,
				cur.afterEvent,
				cur.justplay,
				cur.dirname,
				cur.tags
			)

	def cancel(self):
		self.close(None)

class AutoTimerImporter(Screen):
	"""Import AutoTimer from Timer"""

	skin = """<screen name="AutoTimerImporter" title="Import AutoTimer" position="center,center" size="565,290">
		<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="list" position="5,45" size="555,240" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session, autotimer, name, begin, end, disabled, sref, afterEvent, justplay, dirname, tags):
		Screen.__init__(self, session)

		# Keep AutoTimer
		self.autotimer = autotimer

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText()
 		self["key_blue"] = StaticText()

		entries = []
		append = entries.append

		if disabled is not None:
			append(
				SelectionEntryComponent(
					': '.join((_("Enabled"), {True: _("disable"), False: _("enable")}[bool(disabled)])),
					not disabled,
					0,
					True
			))

		if name != "":
			append(
				SelectionEntryComponent(
					_("Match title: %s") % (name),
					name,
					1,
					True
			))
			append(
				SelectionEntryComponent(
					_("Exact match"),
					True,
					8,
					True
			))

		if begin and end:
			begin = localtime(begin)
			end = localtime(end)
			append(
				SelectionEntryComponent(
					_("Match Timespan: %02d:%02d - %02d:%02d") % (begin[3], begin[4], end[3], end[4]),
					((begin[3], begin[4]), (end[3], end[4])),
					2,
					True
			))
			append(
				SelectionEntryComponent(
					_("Only on Weekday: %s") % (weekdays[begin.tm_wday][1],), # XXX: the lookup is dirty but works :P
					str(begin.tm_wday),
					9,
					True
			))

		if sref:
			append(
				SelectionEntryComponent(
					_("Only on Service: %s") % (sref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')),
					str(sref),
					3,
					True
			))

		if afterEvent is not None:
			append(
				SelectionEntryComponent(
					': '.join((_("After event"), afterevent[afterEvent])),
					afterEvent,
					4,
					True
			))

		if justplay is not None:
			append(
				SelectionEntryComponent(
					': '.join((_("Timer type"), {0: _("record"), 1: _("zap")}[int(justplay)])),
					int(justplay),
					5,
					True
			))

		if dirname is not None:
			append(
				SelectionEntryComponent(
					': '.join((_("Location"), dirname or "/hdd/movie/")),
					dirname,
					6,
					True
			))

		if tags:
			append(
				SelectionEntryComponent(
					': '.join((_("Tags"), ', '.join(tags))),
					tags,
					7,
					True
			))

		self["list"] = SelectionList(entries)

		# Define Actions
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self["list"].toggleSelection,
			"cancel": self.cancel,
			"red": self.cancel,
			"green": self.accept
		}, -1)

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Import AutoTimer"))

	def cancel(self):
		self.session.openWithCallback(
			self.cancelConfirm,
			MessageBox,
			_("Really close without saving settings?")
		)

	def cancelConfirm(self, ret):
		if ret:
			self.close(None)

	def gotCustomMatch(self, ret):
		if ret:
			self.autotimer.match = ret
			# Check if we have a trailing whitespace
			if ret[-1:] == " ":
				self.session.openWithCallback(
					self.trailingWhitespaceRemoval,
					MessageBox,
					_('You entered "%s" as Text to match.\nDo you want to remove trailing whitespaces?') % (ret)
				)
			# Just confirm else
			else:
				self.close((
				self.autotimer,
				self.session
			))

	def trailingWhitespaceRemoval(self, ret):
		if ret is not None:
			if ret:
				self.autotimer.match = self.autotimer.match.rstrip()
			self.close((
				self.autotimer,
				self.session
			))

	def accept(self):
		list = self["list"].getSelectionsList()
		autotimer = self.autotimer

		for item in list:
			if item[2] == 0: # Enable
				autotimer.enabled = item[1]
			elif item[2] == 1: # Match
				autotimer.match = item[1]
			elif item[2] == 2: # Timespan
				autotimer.timespan = item[1]
			elif item[2] == 3: # Service
				value = item[1]

				myref = eServiceReference(value)
				if not (myref.flags & eServiceReference.isGroup):
					# strip all after last :
					pos = value.rfind(':')
					if pos != -1:
						if value[pos-1] == ':':
							pos -= 1
						value = value[:pos+1]

				autotimer.services = [value]
			elif item[2] == 4: # AfterEvent
				autotimer.afterevent = [(item[1], None)]
			elif item[2] == 5: # Justplay
				autotimer.justplay = item[1]
			elif item[2] == 6: # Location
				autotimer.destination = item[1]
			elif item[2] == 7: # Tags
				autotimer.tags = item[1]
			elif item[2] == 8: # Exact match
				autotimer.searchType = "exact"
				autotimer.searchCase = "sensitive"
			elif item[2] == 9: # Weekday
				includes = [
						autotimer.getIncludedTitle(),
						autotimer.getIncludedShort(),
						autotimer.getIncludedDescription(),
						[item[1]],
				]
				autotimer.include = includes

		if autotimer.match == "":
			self.session.openWithCallback(
					self.gotCustomMatch,
					InputBox,
					title = _("Please provide a Text to match")
			)
		else:
			self.close((
				autotimer,
				self.session
			))

