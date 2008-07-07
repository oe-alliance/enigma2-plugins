# GUI (Screens)
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from AutoTimerEditor import AutoTimerEditor
from AutoTimerSettings import AutoTimerSettings
from AutoTimerPreview import AutoTimerPreview
from AutoTimerImporter import AutoTimerImportSelector

# GUI (Components)
from AutoTimerList import AutoTimerList
from Components.ActionMap import HelpableActionMap
from Components.Button import Button

# Plugin
from AutoTimerComponent import AutoTimerComponent

class AutoTimerOverview(Screen, HelpableScreen):
	"""Overview of AutoTimers"""

	skin = """<screen name="AutoTimerOverview" position="140,148" size="460,265" title="AutoTimer Overview">
			<widget name="entries" position="5,5" size="450,200" scrollbarMode="showOnDemand" />
			<ePixmap position="0,220" zPosition="1" size="140,40" pixmap="skin_default/buttons/green.png" alphatest="on" />
			<ePixmap position="140,220" zPosition="1" size="140,40" pixmap="skin_default/buttons/yellow.png" alphatest="on" />
			<ePixmap position="280,220" zPosition="1" size="140,40" pixmap="skin_default/buttons/blue.png" alphatest="on" />
			<ePixmap position="422,230" zPosition="1" size="35,25" pixmap="skin_default/buttons/key_menu.png" alphatest="on" />
			<widget name="key_green" position="0,220" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="140,220" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="280,220" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, autotimer):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		# Save autotimer
		self.autotimer = autotimer

		self.changed = False

		# Button Labels
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_("Delete"))
		self["key_blue"] = Button(_("Add"))

		# Create List of Timers
		self["entries"] = AutoTimerList(self.autotimer.getTupleTimerList())

		# Define Actions
		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
				"ok": (self.ok, _("Edit selected AutoTimer")),
				"cancel": (self.cancel, _("Close and forget changes")),
			}
		)

		self["MenuActions"] = HelpableActionMap(self, "MenuActions",
			{
				"menu": (self.menu, _("Open Context Menu"))
			}
		)

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
			{
				"green": (self.save, _("Close and save changes")),
				"yellow": (self.remove, _("Remove selected AutoTimer")),
				"blue": (self.add, _("Add new AutoTimer")),
			}
		)

	def add(self):
		newTimer = self.autotimer.defaultTimer.clone()
		newTimer.id = self.autotimer.getUniqueId()
		
		self.session.openWithCallback(
			self.addCallback,
			AutoTimerEditor,
			newTimer
		)

	def editCallback(self, ret):
		if ret:
			self.changed = True
			self.refresh()

	def addCallback(self, ret):
		if ret:
			self.changed = True
			self.autotimer.add(ret)
			self.refresh()

	def importCallback(self, ret):
		if ret:
			self.session.openWithCallback(
				self.addCallback,
				AutoTimerEditor,
				ret
			)

	def refresh(self, res = None):
		# Re-assign List
		self["entries"].setList(self.autotimer.getTupleTimerList())

	def ok(self):
		# Edit selected Timer
		current = self["entries"].getCurrent()
		if current is not None:
			self.session.openWithCallback(
				self.editCallback,
				AutoTimerEditor,
				current[0]
			)

	def remove(self):
		# Remove selected Timer
		cur = self["entries"].getCurrent()
		if cur is not None:
			self.session.openWithCallback(
				self.removeCallback,
				MessageBox,
				_("Do you really want to delete %s?") % (cur[0].name),
			)

	def removeCallback(self, ret):
		cur = self["entries"].getCurrent()
		if ret and cur:
			self.autotimer.remove(cur[0].id)
			self.refresh()

	def cancel(self):
		if self.changed:
			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving settings?")
			)
		else:
			self.close(None)

	def cancelConfirm(self, ret):
		if ret:
			# Invalidate config mtime to force re-read on next run
			self.autotimer.configMtime = -1

			# Close and indicated that we canceled by returning None
			self.close(None)

	def menu(self):
		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list = [
				(_("Preview"), "preview"),
				(_("Import"), "import"),
				(_("Setup"), "setup"),
				(_("Edit new timer defaults"), "defaults")
			],
		)

	def menuCallback(self, ret):
		ret = ret and ret[1]
		if ret:
			if ret == "preview":
				total, new, modified, timers = self.autotimer.parseEPG(simulateOnly = True)
				self.session.open(
					AutoTimerPreview,
					timers
				)
			elif ret == "import":
				# XXX: apply defaults here too?
				self.session.openWithCallback(
					self.importCallback,
					AutoTimerImportSelector,
					AutoTimerComponent(
						self.autotimer.getUniqueId(),	# Id
						"",								# Name
						"",								# Match
						True							# Enabled
					)
				)
			elif ret == "setup":
				self.session.open(
					AutoTimerSettings
				)
			elif ret == "defaults":
				self.session.open(
					AutoTimerEditor,
					self.autotimer.defaultTimer,
					editingDefaults = True
				)

	def save(self):
		# Just close here, saving will be done by cb
		self.close(self.session)
