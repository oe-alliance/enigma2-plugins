from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText

from . import _

class AutoTimerHelp(Screen):
	skin = """
		<screen name="AutoTimerHelp" flags="wfNoBorder" position="0,0" size="720,576">
			<ePixmap pixmap="skin_default/buttons/red.png" position="75,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="215,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="355,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="495,10" size="140,40" alphatest="on" />
			<widget render="Label" source="key_red" position="75,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<!--<widget render="Label" source="key_green" position="215,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />-->
			<widget render="Label" source="key_yellow" position="355,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget render="Label" source="key_blue" position="495,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<widget render="Label" source="title" position="60,50" size="600,50" zPosition="5" valign="center" halign="left" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="detailtext" position="60,120" size="610,370" zPosition="10" font="Regular;21" transparent="1" halign="left" valign="top"/>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["key_red"] = StaticText(_("Close"))
		#self["key_green"] = StaticText()
		self["key_yellow"] = StaticText("<<")
		self["key_blue"] = StaticText(">>")
		self["title"] = StaticText()
		self["detailtext"] = ScrollLabel()
		self.curPage = 0

		self["actions"] = ActionMap(["ShortcutActions", "WizardActions"],
		{
			"back": self.close,
			"red": self.close,
			"up": self.pageUp,
			"down":	self.pageDown,
			"left":	self.pageUp,
			"right": self.pageDown,
			"yellow": self.prevPage,
			"blue": self.nextPage,
		}, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("AutoTimer Help"))
		self.setPage(0)

	def setPage(self, newPage):
		if newPage == 0:
			self["title"].text = _("Welcome to the AutoTimer-Plugin")
			self["detailtext"].setText(_("This help screen is supposed to give you a quick look at everything the AutoTimer has to offer.\nYou can abort it at any time by pressing the RED or EXIT button on your remote control or bring it up at a later point by selecting it from the control menu using the MENU button from the regular entry point of the plugin (more on that later).\n\n\nBut you really should consider to take the few minutes it takes to read this help pages."))
		elif newPage == 1:
			self["title"].text = _("The \"Overview\"")
			self["detailtext"].setText(_("The AutoTimer overview is the standard entry point to this plugin.\n\nIf AutoTimers are configured you can choose them from a list to change them (OK button on your remove) or remove them (YELLOW button on your remote).\nNew Timers can be added by pressing the BLUE button and the control menu can be opened using the MENU button.\n\nWhen leaving the plugin using the GREEN button it will search the EPG for matching events ONCE. To configure a regular search interval of the plugin to search for events open the control menu and enter the plugin setup."))
		elif newPage == 2:
			self["title"].text = _("What is this \"control menu\" you keep talking about?")
			self["detailtext"].setText(_("The control menu hides less frequently used options of the plugin, including the configuration and default settings for new AutoTimers.\n\nWhile you can just open the menu and take a look for yourself, let's go through the available options:\n - Help:\n   What you are looking at right now\n - Preview:\n   Simulate EPG search, helps finding errors in your setup.\n - Import existing Timer:\n   Create a new AutoTimer based on an existing regular timer.\n - Import from EPG:\n   Create an AutoTimer based on an EPG event.\n - Setup:\n   Generic configuration of the plugin.\n - Edit new timer defaults:\n   Configure default values for new AutoTimers.\n - Create a new timer using the wizard/classic editor:\n   Use the non-default editor to create a new AutoTimer."))
		elif newPage == 3:
			self["title"].text = _("Generic setup")
			self["detailtext"].setText(_("This screen should be pretty straight-forward. If the option name does not give its meaning away there should be an explanation for each of them when you select them. If there is no visible explanation this is most likely a skin issue and please try if the default skin fixes the issue.\n\nA lot of effort has been put in making the parameters as easy to understand as possible, so give reading them a try ;-)."))
		elif newPage == 4:
			self["title"].text = _("Wizard or Classic Editor?")
			self["detailtext"].setText(_("This is mostly a matter of taste.\nThe Wizard provides you with a reduced set of options and presents them in smaller sets at a time. It is mostly aimed at users not very experienced with this plugin or the \"expert\" level features of enigma2.\n\nYou can check out the \"classic\" editor by opening an existing timer from the overview and if you prefer this view over the wizard you can change the default editor in the setup dialog."))
		elif newPage == 5:
			self["title"].text = _("Congratulations")
			self["detailtext"].setText(_("You now know almost everything there is to know about the AutoTimer-Plugin.\n\nAs a final hint I can't stress how important it is to take a look at the help texts that are shown in the setup dialogs as they cover the most frequently asked questions. Suprisingly even after the hints were added ;-)."))
		else:
			# XXX: just during development
			self["title"].text = "Invalid Help Page"
			self["detailtext"].setText("You managed to jump to an invalid page. Stop it :-)")
			newPage = self.curPage
		self.curPage = newPage
	
	def pageUp(self):
		self["detailtext"].pageUp()

	def pageDown(self):
		self["detailtext"].pageDown()

	def prevPage(self):
		if self.curPage > 0:
			self.setPage(self.curPage - 1)

	def nextPage(self):
		if self.curPage < 5:
			self.setPage(self.curPage + 1)

