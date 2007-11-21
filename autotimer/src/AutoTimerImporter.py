# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.TimerList import TimerList
from Components.SelectionList import SelectionList, SelectionEntryComponent

# Timer
from RecordTimer import AFTEREVENT

# Needed to convert our timestamp back and forth
from time import localtime

afterevent = { AFTEREVENT.NONE: _("do nothing"), AFTEREVENT.DEEPSTANDBY: _("go to deep standby"), AFTEREVENT.STANDBY: _("go to standby")}

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
		self.setTitle(_("Select a Timer to Import"))

	def fillTimerList(self):
		del self.list[:]

		for timer in self.session.nav.RecordTimer.timer_list:
			self.list.append((timer, False))

		for timer in self.session.nav.RecordTimer.processed_timers:
			self.list.append((timer, True))
		self.list.sort(cmp = lambda x, y: x[0].begin < y[0].begin)

	def importerClosed(self, ret):
		if ret is not None:
			ret.name = ret.match
		self.close(ret)

	def openImporter(self):
		cur=self["timerlist"].getCurrent()
		if cur:
			self.session.openWithCallback(
				self.importerClosed,
				AutoTimerImporter,
				cur,
				self.autotimer
			)

	def cancel(self):
		self.close(None)

class AutoTimerImporter(Screen):
	"""Import AutoTimer from Timer"""

	skin = """<screen name="AutoTimerImporter" title="Import AutoTimer" position="75,155" size="565,280">
		<widget name="list" position="5,5" size="555,225" scrollbarMode="showOnDemand" />
		<ePixmap position="0,235" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,235" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,235" zPosition="4" size="140,40" pixmap="skin_default/key-yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,235" zPosition="4" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="280,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="420,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, timer, autotimer):
		Screen.__init__(self, session)

		# Keep AutoTimer
		self.autotimer = autotimer

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button()
 		self["key_blue"] = Button()

		begin = localtime(timer.begin)
		end = localtime(timer.end)
		list = [
			SelectionEntryComponent(
				': '.join([_("Enabled"), {True: _("disable"), False: _("enable")}[bool(timer.disabled)]]),
				not timer.disabled,
				0,
				True
			),
			SelectionEntryComponent(
				_("Match title: %s") % (timer.name),
				timer.name,
				1,
				True
			),
			SelectionEntryComponent(
				_("Match Timespan: %02d:%02d - %02d:%02d") % (begin[3], begin[4], end[3], end[4]),
				((begin[3], begin[4]), (end[3], end[4])),
				2,
				True
			),
			SelectionEntryComponent(
				_("Only on Service: %s") % (timer.service_ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')),
				str(timer.service_ref),
				3,
				True
			),
			SelectionEntryComponent(
				': '.join([_("After event"), afterevent[timer.afterEvent]]),
				timer.afterEvent,
				4,
				True
			),
			SelectionEntryComponent(
				': '.join([_("Timer Type"), {0: _("record"), 1: _("zap")}[int(timer.justplay)]]),
				int(timer.justplay),
				5,
				True
			)
		]

		self["list"] = SelectionList(list)

		# Define Actions
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], 
		{
			"ok": self["list"].toggleSelection,
			"cancel": self.cancel,
			"red": self.cancel,
			"green": self.accept
		}, -1)

	def cancel(self):
		self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))

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
				self.close(self.autotimer)

	def trailingWhitespaceRemoval(self, ret):
		if ret is not None:
			if ret:
				self.autotimer.match = self.autotimer.match.rstrip()
			self.close(self.autotimer)

	def accept(self):
		list = self["list"].getSelectionsList()

		for item in list:
			if item[2] == 0: # Enable
				self.autotimer.enabled = item[1]
			elif item[2] == 1: # Match
				self.autotimer.match = item[1]
			elif item[2] == 2: # Timespan
				self.autotimer.timespan = item[1]
			elif item[2] == 3: # Service
				value = item[1]

				# strip all after last :
				pos = value.rfind(':')
				if pos != -1:
					value = value[:pos+1]

				self.autotimer.services = [value]
			elif item[2] == 4: # AfterEvent
				self.autotimer.afterevent = [(item[1], None)]
			elif item[2] == 5: # Justplay
				self.autotimer.justplay = item[1]

		if self.autotimer.match == "":
			self.session.openWithCallback(
					self.gotCustomMatch,
					InputBox,
					title = _("Please provide a Text to Match")
			)
		else:
			self.close(self.autotimer)
