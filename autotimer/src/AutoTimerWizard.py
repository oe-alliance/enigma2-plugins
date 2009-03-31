# l10n
from . import _

# GUI (Screens)
from Screens.WizardLanguage import WizardLanguage
from Screens.Rc import Rc
from AutoTimerEditor import AutoTimerEditorBase, AutoTimerServiceEditor, \
		AutoTimerFilterEditor

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap

# Configuration
from Components.config import getConfigListEntry, KEY_0, KEY_DELETE, \
		KEY_BACKSPACE

# Wizard XML Path
from Tools import Directories

class AutoTimerWizard(WizardLanguage, AutoTimerEditorBase, Rc):
	STEP_ID_BASIC = 2
	STEP_ID_TIMESPAN = 5
	STEP_ID_SERVICES = 7
	STEP_ID_FILTER = 8

	def __init__(self, session, newTimer):
		self.xmlfile = Directories.resolveFilename(Directories.SCOPE_PLUGINS, "Extensions/AutoTimer/autotimerwizard.xml")

		WizardLanguage.__init__(self, session, showSteps = True, showStepSlider = True)
		AutoTimerEditorBase.__init__(self, newTimer)
		Rc.__init__(self)

		self.skinName = "StartWizard"
		self["wizard"] = Pixmap()

		self.doCancel = False
		self.emptyMatch = False
		self.tailingWhitespacesMatch = False

		# We might need to change shown items, so add some notifiers
		self.timespan.addNotifier(self.regenTimespanList, initial_call = False)
		self.generateTimespanList()

		self.servicesDlg = self.session.instantiateDialog(
				AutoTimerServiceEditor,
				self.serviceRestriction, self.services, self.bouquets
		)

		self.filterDlg = self.session.instantiateDialog(
				AutoTimerFilterEditor,
				self.filterSet, self.excludes, self.includes
		)

		self["TextEntryActions"] = ActionMap(["TextEntryActions"],
			{
				"deleteForward": self.deleteForward,
				"deleteBackward": self.deleteBackward
			}, -2
		)

	def getTranslation(self, text):
		return _(text)

	def regenTimespanList(self, *args, **kwargs):
		self.generateTimespanList()
		if self.currStep == AutoTimerWizard.STEP_ID_TIMESPAN:
			self["config"].setList(self.timespanList)

	def generateTimespanList(self):
		self.timespanList = [
			getConfigListEntry(_("Only match during Timespan"), self.timespan)
		]

		# Only allow editing timespan when it's enabled
		if self.timespan.value:
			self.timespanList.extend([
				getConfigListEntry(_("Begin of Timespan"), self.timespanbegin),
				getConfigListEntry(_("End of Timespan"), self.timespanend)
			])

	def getConfigList(self):
		if self.currStep == AutoTimerWizard.STEP_ID_BASIC: # Basic
			return [
				getConfigListEntry(_("Enabled"), self.enabled),
				getConfigListEntry(_("Description"), self.name),
				getConfigListEntry(_("Match Title"), self.match),
				getConfigListEntry(_("Timer Type"), self.justplay),
			]
		elif self.currStep == AutoTimerWizard.STEP_ID_TIMESPAN: # Timespan
			return self.timespanList
		elif self.currStep == AutoTimerWizard.STEP_ID_SERVICES: # Services
			return self.servicesDlg["config"].getList()
		elif self.currStep == AutoTimerWizard.STEP_ID_FILTER: # Filters
			return self.filterDlg["config"].getList()
		return []

	def selectionMade(self):
		timer = self.timer
		if self.currStep == AutoTimerWizard.STEP_ID_BASIC: # Basic
			timer.enabled = self.enabled.value
			timer.name = self.name.value.strip() or self.match.value
			timer.match = self.match.value
			timer.justplay = self.justplay.value == "zap"
			self.emptyMatch = not timer.match.strip()
			self.trailingWhitespacesMatch = (timer.match[-1:] == " ")
		elif self.currStep == AutoTimerWizard.STEP_ID_TIMESPAN: # Timespan
			if self.timespan.value:
				start = self.timespanbegin.value
				end = self.timespanend.value
				timer.timespan = (start, end)
			else:
				timer.timespan = None
		elif self.currStep == AutoTimerWizard.STEP_ID_SERVICES: # Services
			self.servicesDlg.refresh()

			if self.servicesDlg.enabled.value:
				timer.services = self.servicesDlg.services[0]
				timer.bouquets = self.servicesDlg.services[1]
			else:
				timer.services = []
				timer.bouquets = []
		elif self.currStep == AutoTimerWizard.STEP_ID_FILTER: # Filters
			self.filterDlg.refresh()

			if self.filterDlg.enabled.value:
				timer.includes = self.filterDlg.includes
				timer.excludes = self.filterDlg.excludes
			else:
				timer.includes = []
				timer.excludes = []

	def keyNumberGlobal(self, number):
		if self.currStep == AutoTimerWizard.STEP_ID_BASIC or self.currStep == AutoTimerWizard.STEP_ID_TIMESPAN:
			self["config"].handleKey(KEY_0 + number)
		else:
			WizardLanguage.keyNumberGlobal(self, number)

	def blue(self):
		if self.currStep == AutoTimerWizard.STEP_ID_SERVICES:
			self.servicesDlg.new()
		elif self.currStep == AutoTimerWizard.STEP_ID_FILTER:
			self.filterDlg.new()

	def yellow(self):
		if self.currStep == AutoTimerWizard.STEP_ID_SERVICES:
			self.servicesDlg.remove()
		elif self.currStep == AutoTimerWizard.STEP_ID_FILTER:
			self.filterDlg.remove()

	def maybeRemoveWhitespaces(self):
		# XXX: Hack alert
		if self["list"].current[1] == "removeTrailingWhitespaces":
			print "Next step would be to remove trailing whitespaces, removing them and redirecting to 'conf2'"
			self.timer.match = self.timer.match.rstrip()
			self.match.value = self.match.value.rstrip()
			self.currStep = self.getStepWithID("conf2")
		self.trailingWhitespacesMatch = False

	def deleteForward(self):
		self["config"].handleKey(KEY_DELETE)

	def deleteBackward(self):
		self["config"].handleKey(KEY_BACKSPACE)

	def cancel(self):
		self.doCancel = True
		self.currStep = len(self.wizard)

	def close(self, *args, **kwargs):
		if self.doCancel:
			WizardLanguage.close(self, None)
		else:
			WizardLanguage.close(self, self.timer)

