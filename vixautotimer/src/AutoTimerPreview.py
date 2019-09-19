# -*- coding: UTF-8 -*-
# for localized messages
from . import _

# GUI (Screens)
from Screens.Screen import Screen

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText

from ServiceReference import ServiceReference
from Tools.FuzzyDate import FuzzyTime

class AutoTimerPreview(Screen):
	"""Preview Timers which would be set"""

	skin = """<screen name="AutoTimerPreview" title="Preview AutoTimer" position="center,center" size="565,280">
		<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="timerlist" render="Listbox" position="5,45" size="555,220" scrollbarMode="showAlways">
			<convert type="TemplatedMultiContent">
				{"template": [
						MultiContentEntryText(pos=(2,2), size=(550,24), text = 3, font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(2,26), size=(555,30), text = 0, font = 1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(2,50), size=(400,20), text = 4, font = 1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(290,50), size=(233,20), text = 2, font = 1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER),
					],
				 "fonts": [gFont("Regular", 20),gFont("Regular", 18)],
				 "itemHeight": 72
				}
			</convert>
		</widget>
	</screen>"""

	def __init__(self, session, timers):
		Screen.__init__(self, session)

		# Sort timers by begin
		timers.sort(key = lambda x: x[1])
		self.sort_type = 0

		# name, begin, end, serviceref, timername -> name, begin, timername, sname, timestr
		self.timers = [
			(x[0], x[1], x[4],
			ServiceReference(x[3]).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '').encode('utf-8', 'ignore'),
			(("%s, %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(x[1]) + FuzzyTime(x[2])[1:] + ((x[2] - x[1]) / 60,))))
			for x in timers
		]

		self["timerlist"] = List(self.timers)

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_yellow"] = StaticText()

		self.setSortDescription()

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.sort
			}
		)

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Preview AutoTimer"))

	def setSortDescription(self):
		if self.sort_type == 1:
			self["key_yellow"].text = _("Sort Time")
		else:
			self["key_yellow"].text = _("Sort AutoTimer")

	def sort(self):
		timers = self.timers
		if timers:
			current = self["timerlist"].current
			idx = 0
			for timer in timers:
				if timer == current:
					break
				idx += 1
			if self.sort_type == 1:
				timers.sort(key=lambda x: x[1])
				self.sort_type = 0
			else:
				timers.sort(key = lambda x: x[4].lower())
				self.sort_type = 1
			self["timerlist"].updateList(timers)
			self["timerlist"].index = idx
			self.setSortDescription()

	def cancel(self):
		self.close(None)

	def save(self):
		self.close(True)

