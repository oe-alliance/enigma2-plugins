# l10n
from . import _

# GUI (Screens)
from Screens.WizardLanguage import WizardLanguage
from Screens.Rc import Rc
from AutoTimerEditor import AutoTimerEditorBase, AutoTimerServiceEditor, \
		AutoTimerFilterEditor

# GUI (Components)
from Components.ActionMap import ActionMap

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

	skin = """
		<screen position="0,0" size="720,576" title="Welcome..." flags="wfNoBorder" >
			<widget name="text" position="153,50" size="340,300" font="Regular;22" />
			<widget source="list" render="Listbox" position="53,310" size="440,220" scrollbarMode="showOnDemand" >
				<convert type="StringList" />
			</widget>
			<widget name="config" position="53,310" zPosition="1" size="440,220" transparent="1" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/wizard.png" position="40,50" zPosition="10" size="110,174" transparent="1" alphatest="on"/>
			<ePixmap pixmap="skin_default/buttons/button_red.png" position="40,225" zPosition="0" size="15,16" transparent="1" alphatest="on" />
			<widget name="languagetext" position="55,225" size="95,30" font="Regular;18" />
			<widget name="rc" pixmaps="skin_default/rc.png,skin_default/rcold.png" position="500,50" zPosition="10" size="154,500" alphatest="on" />
			<widget name="arrowdown" pixmap="skin_default/arrowdown.png" position="0,0" zPosition="11" size="37,70" transparent="1" alphatest="on"/>
			<widget name="arrowdown2" pixmap="skin_default/arrowdown.png" position="0,0" zPosition="11" size="37,70" transparent="1" alphatest="on"/>
			<widget name="arrowup" pixmap="skin_default/arrowup.png" position="-100,-100" zPosition="11" size="37,70" transparent="1" alphatest="on"/>
			<widget name="arrowup2" pixmap="skin_default/arrowup.png" position="-100,-100" zPosition="11" size="37,70" transparent="1" alphatest="on"/>
		</screen>"""

	def __init__(self, session, newTimer):
		self.xmlfile = Directories.resolveFilename(Directories.SCOPE_PLUGINS, "Extensions/AutoTimer/autotimerwizard.xml")

		WizardLanguage.__init__(self, session, showSteps = False, showStepSlider = False)
		AutoTimerEditorBase.__init__(self, newTimer)
		Rc.__init__(self)

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
		if self.currStep == AutoTimerWizard.STEP_ID_BASIC: # Basic
			self.timer.enabled = self.enabled.value
			self.timer.name = self.name.value.strip() or self.match.value
			self.timer.match = self.match.value
			self.timer.justplay = self.justplay.value == "zap"
			self.emptyMatch = not self.timer.match.strip()
			self.trailingWhitespacesMatch = (self.timer.match[-1:] == " ")
		elif self.currStep == AutoTimerWizard.STEP_ID_TIMESPAN: # Timespan
			if self.timespan.value:
				start = self.timespanbegin.value
				end = self.timespanend.value
				self.timer.timespan = (start, end)
			else:
				self.timer.timespan = None
		elif self.currStep == AutoTimerWizard.STEP_ID_SERVICES: # Services
			self.servicesDlg.saveCurrent()

			if self.servicesDlg.enabled.value:
				self.timer.services = self.servicesDlg.services[0]
				self.timer.bouquets = self.servicesDlg.services[1]
			else:
				self.timer.services = []
				self.timer.bouquets = []
		elif self.currStep == AutoTimerWizard.STEP_ID_FILTER: # Filters
			self.filterDlg.saveCurrent()

			if self.filterDlg.enabled.value:
				self.timer.includes = self.filterDlg.includes
				self.timer.excludes = self.filterDlg.excludes
			else:
				self.timer.includes = []
				self.timer.excludes = []

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

