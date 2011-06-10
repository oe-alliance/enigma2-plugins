# for localized messages
from . import _

# GUI (Screens)
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from AutoTimerEditor import AutoTimerEditor, AutoTimerChannelSelection
from MPHelp import MPHelp
from AutoTimerImporter import AutoTimerImportSelector
from AutoTimerPreview import AutoTimerPreview
from AutoTimerSettings import AutoTimerSettings
from AutoTimerWizard import AutoTimerWizard

# GUI (Components)
from AutoTimerList import AutoTimerList
from Components.ActionMap import HelpableActionMap
from Components.config import config
from Components.Sources.StaticText import StaticText

class AutoTimerOverviewSummary(Screen):
	skin = """
	<screen position="0,0" size="132,64">
		<widget source="parent.Title" render="Label" position="6,4" size="120,21" font="Regular;18" />
		<widget source="entry" render="Label" position="6,25" size="120,21" font="Regular;16" />
		<widget source="global.CurrentTime" render="Label" position="56,46" size="82,18" font="Regular;16" >
			<convert type="ClockToText">WithSeconds</convert>
		</widget>
	</screen>"""

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent = parent)
		self["entry"] = StaticText("")
		self.onShow.append(self.addWatcher)
		self.onHide.append(self.removeWatcher)

	def addWatcher(self):
		self.parent.onChangedEntry.append(self.selectionChanged)
		self.parent.selectionChanged()

	def removeWatcher(self):
		self.parent.onChangedEntry.remove(self.selectionChanged)

	def selectionChanged(self, text):
		self["entry"].text = text

class AutoTimerOverview(Screen, HelpableScreen):
	"""Overview of AutoTimers"""

	skin = """<screen name="AutoTimerOverview" position="center,center" size="460,280" title="AutoTimer Overview">
			<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="280,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<ePixmap position="422,10" zPosition="1" size="35,25" pixmap="skin_default/buttons/key_menu.png" alphatest="on" />
			<widget source="key_green" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_yellow" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_blue" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="entries" position="5,45" size="450,225" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, autotimer):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		# Save autotimer
		self.autotimer = autotimer

		self.changed = False

		# Button Labels
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Delete"))
		self["key_blue"] = StaticText(_("Add"))

		# Create List of Timers
		self["entries"] = AutoTimerList(autotimer.getSortedTupleTimerList())

		# Summary
		self.onChangedEntry = []
		self["entries"].onSelectionChanged.append(self.selectionChanged)

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

		self.onLayoutFinish.append(self.setCustomTitle)
		self.onFirstExecBegin.append(self.firstExec)

	def firstExec(self):
		if config.plugins.autotimer.show_help.value:
			config.plugins.autotimer.show_help.value = False
			config.plugins.autotimer.show_help.save()
			self.menuCallback((False, "help"))

	def setCustomTitle(self):
		self.setTitle(_("AutoTimer overview"))

	def createSummary(self):
		return AutoTimerOverviewSummary

	def selectionChanged(self):
		sel = self["entries"].getCurrent()
		text = sel and sel.name or ""
		for x in self.onChangedEntry:
			try:
				x(text)
			except Exception:
				pass

	def add(self):
		newTimer = self.autotimer.defaultTimer.clone()
		newTimer.id = self.autotimer.getUniqueId()

		if config.plugins.autotimer.editor.value == "wizard":
			self.session.openWithCallback(
				self.addCallback,
				AutoTimerWizard,
				newTimer
			)
		else:
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
		cur = self["entries"].getCurrent()
		self["entries"].setList(self.autotimer.getSortedTupleTimerList())
		self["entries"].moveToEntry(cur)

	def ok(self):
		# Edit selected Timer
		current = self["entries"].getCurrent()
		if current is not None:
			self.session.openWithCallback(
				self.editCallback,
				AutoTimerEditor,
				current
			)

	def remove(self):
		# Remove selected Timer
		cur = self["entries"].getCurrent()
		if cur is not None:
			self.session.openWithCallback(
				self.removeCallback,
				MessageBox,
				_("Do you really want to delete %s?") % (cur.name),
			)

	def removeCallback(self, ret):
		cur = self["entries"].getCurrent()
		if ret and cur:
			self.autotimer.remove(cur.id)
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
		list = [
			(_("Help"), "help"),
			(_("Preview"), "preview"),
			(_("Import existing Timer"), "import"),
			(_("Import from EPG"), "import_epg"),
			(_("Setup"), "setup"),
			(_("Edit new timer defaults"), "defaults"),
		]

		if config.plugins.autotimer.editor.value == "wizard":
			list.append((_("Create a new timer using the classic editor"), "newplain"))
		else:
			list.append((_("Create a new timer using the wizard"), "newwizard"))

		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list = list,
		)

	def menuCallback(self, ret):
		ret = ret and ret[1]
		if ret:
			if ret == "help":
				pages = (
					(
						_("Welcome to the AutoTimer-Plugin"),
						_("This help screen is supposed to give you a quick look at everything the AutoTimer has to offer.\nYou can abort it at any time by pressing the RED or EXIT button on your remote control or bring it up at a later point by selecting it from the control menu using the MENU button from the regular entry point of the plugin (more on that later).\n\n\nBut you really should consider to take the few minutes it takes to read this help pages.")
					),
					(
						_("The \"Overview\""),
						_("The AutoTimer overview is the standard entry point to this plugin.\n\nIf AutoTimers are configured you can choose them from a list to change them (OK button on your remove) or remove them (YELLOW button on your remote).\nNew Timers can be added by pressing the BLUE button and the control menu can be opened using the MENU button.\n\nWhen leaving the plugin using the GREEN button it will search the EPG for matching events ONCE. To configure a regular search interval of the plugin to search for events open the control menu and enter the plugin setup.")
					),
					(
						_("What is this \"control menu\" you keep talking about?"),
						_("The control menu hides less frequently used options of the plugin, including the configuration and default settings for new AutoTimers.\n\nWhile you can just open the menu and take a look for yourself, let's go through the available options:\n - Help:\n   What you are looking at right now\n - Preview:\n   Simulate EPG search, helps finding errors in your setup.\n - Import existing Timer:\n   Create a new AutoTimer based on an existing regular timer.\n - Import from EPG:\n   Create an AutoTimer based on an EPG event.\n - Setup:\n   Generic configuration of the plugin.\n - Edit new timer defaults:\n   Configure default values for new AutoTimers.\n - Create a new timer using the wizard/classic editor:\n   Use the non-default editor to create a new AutoTimer.")
					),
					(
						_("Generic setup"),
						_("This screen should be pretty straight-forward. If the option name does not give its meaning away there should be an explanation for each of them when you select them. If there is no visible explanation this is most likely a skin issue and please try if the default skin fixes the issue.\n\nA lot of effort has been put in making the parameters as easy to understand as possible, so give reading them a try ;-).")
					),
					(
						_("Wizard or Classic Editor?"),
						_("This is mostly a matter of taste.\nThe Wizard provides you with a reduced set of options and presents them in smaller sets at a time. It is mostly aimed at users not very experienced with this plugin or the \"expert\" level features of enigma2.\n\nYou can check out the \"classic\" editor by opening an existing timer from the overview and if you prefer this view over the wizard you can change the default editor in the setup dialog.")
					),
					(
						_("Congratulations"),
						_("You now know almost everything there is to know about the AutoTimer-Plugin.\n\nAs a final hint I can't stress how important it is to take a look at the help texts that are shown in the setup dialogs as they cover the most frequently asked questions. Surprisingly even after the hints were added ;-).")
					),
				)
				self.session.open(MPHelp, pages, title=_("AutoTimer Help"), additionalSkin="AutoTimerHelp")
			elif ret == "preview":
				total, new, modified, timers, conflicts = self.autotimer.parseEPG(simulateOnly = True)
				self.session.open(
					AutoTimerPreview,
					timers
				)
			elif ret == "import":
				newTimer = self.autotimer.defaultTimer.clone()
				newTimer.id = self.autotimer.getUniqueId()

				self.session.openWithCallback(
					self.importCallback,
					AutoTimerImportSelector,
					newTimer
				)
			elif ret == "import_epg":
				self.session.openWithCallback(
					self.refresh,
					AutoTimerChannelSelection,
					self.autotimer
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
			elif ret == "newwizard":
				newTimer = self.autotimer.defaultTimer.clone()
				newTimer.id = self.autotimer.getUniqueId()

				self.session.openWithCallback(
					self.addCallback, # XXX: we could also use importCallback... dunno what seems more natural
					AutoTimerWizard,
					newTimer
				)
			elif ret == "newplain":
				newTimer = self.autotimer.defaultTimer.clone()
				newTimer.id = self.autotimer.getUniqueId()

				self.session.openWithCallback(
					self.addCallback,
					AutoTimerEditor,
					newTimer
				)

	def save(self):
		# Just close here, saving will be done by cb
		self.close(self.session)

