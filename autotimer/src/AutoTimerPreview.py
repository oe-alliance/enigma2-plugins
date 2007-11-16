# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button
from AutoTimerList import AutoTimerPreviewList

class AutoTimerPreview(Screen):
	"""Preview Timers which would be set"""

	# <ePixmap position="140,220" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
	# <widget name="key_green" position="140,220" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	# <ePixmap position="420,220" zPosition="4" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
	# <widget name="key_blue" position="420,220" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />

	skin = """<screen name="AutoTimerPreview" title="Preview AutoTimer" position="75,155" size="565,265">
		<widget name="timerlist" position="5,5" size="555,210" scrollbarMode="showOnDemand" />
		<ePixmap position="0,220" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
		<ePixmap position="280,220" zPosition="4" size="140,40" pixmap="skin_default/key-yellow.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,220" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="280,220" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, timers):
		Screen.__init__(self, session)

		# Sort timers by begin
		timers.sort(key = lambda x: x[1])
		self.sort_type = 0

		self.timers = timers

		self["timerlist"] = AutoTimerPreviewList(self.timers)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("???"))
		self["key_yellow"] = Button()
 		self["key_blue"] = Button(_("???"))

		self.setSortDescription()

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.sort,
				"blue": self.blue
			}
		)

	def setSortDescription(self):
		if self.sort_type == 1:
			self["key_yellow"].setText(_("Sort Time"))
		else:
			self["key_yellow"].setText(_("Sort AutoTimer"))

	def sort(self):
		if len(self.timers):
			timer = self["timerlist"].getCurrent()
			if self.sort_type == 1:
				self.timers.sort(key=lambda x: x[1])
				self.sort_type = 0
			else:
				self.timers.sort(key = lambda x: x[4].lower())
				self.sort_type = 1
			self["timerlist"].setList(self.timers)
			self["timerlist"].moveToEntry(timer)
			self.setSortDescription()

	def blue(self):
		pass

	def cancel(self):
		self.close(None)

	def save(self):
		self.close(True)
