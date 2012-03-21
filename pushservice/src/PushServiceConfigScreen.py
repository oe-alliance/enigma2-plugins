'''
Created on 06.11.2011

@author: Frank Glaser
'''

# Config
from Components.config import *
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText

# Screen
from Components.ActionMap import ActionMap
from Components.ActionMap import HelpableActionMap
from Components.ScrollLabel import ScrollLabel
from enigma import eSize, ePoint, getDesktop
from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen

# Plugin internal
from . import _
from PushService import PushService


# Constants
separator = "".ljust(250,"-")


# TODO Everytime the user will enter the ConfigurationScreen:
#  Modules will be reloaded
# TODO Everytime the user will leave the ConfigurationScreen:
#  Plugins will be reloaded

#######################################################
# Configuration screen
class PushServiceConfigScreen(Screen, ConfigListScreen, HelpableScreen):

	skin = """
		<screen name="PushServiceConfigScreen" title="" position="center,center" size="565,350">
			<ePixmap position="0,5" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,5" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,5" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,5" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="0,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="140,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_yellow" render="Label" position="280,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_blue" render="Label" position="420,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="5,50" size="555,225" enableWrapAround="1" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,275" zPosition="1" size="565,2" />
		</screen>
	"""
#			<widget source="help" render="Label" position="5,280" size="555,63" font="Regular;21" />

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.skinName = ["PushServiceConfigScreen", "ConfigListScreen"]
		
		# Summary
		from plugin import NAME, VERSION, gPushService
		self.setup_title = NAME + " " + _("Configuration") + " " + VERSION
		
		if gPushService:
			# Save PushService instance
			self.pushservice = gPushService
			# Stop PushService
			self.pushservice.stop()
		else:
			# PushService not running - Instantiate a new one
			global gPushService
			self.pushservice = PushService()
		
		# Load local plugins to work on
		self.plugins = self.pushservice.load()
		
		# Buttons
		self["key_red"]   = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_blue"]  = StaticText(_("Add plugin"))
		self["key_yellow"]  = StaticText(_("Remove plugin"))
		#TODO
		#self["key_info"] test mail
		#self["key_play"] test run
		
		#TODO Maybe LATER
		#self["help"] = StaticText()
		#self["HelpWindow"].hide()
		#self["VirtualKB"].setEnabled(False)
		#self["VKeyIcon"].boolean = False
		self.help_window = None
		
		# Define Actions
		#Bug self["custom_actions"] = HelpableActionMap(self, ["SetupActions", "ColorActions", "PushServiceConfigActions"],
		self["custom_actions"] = HelpableActionMap(self, "PushServiceConfigActions",
		{
			"cancel":				(self.keyCancel,    _("Exit without saving")),
			"save":					(self.keySave,      _("Save and exit.")),
			"blue":					(self.addPlugin,    _("Add plugin")),
			"yellow":				(self.removePlugin, _("Remove plugin")),
			"pageUp":				(self.pageUp,       _("Page up")),
			"pageDown":			(self.pageDown,     _("Page down")),
			"testMail":			(self.testMail,     _("Send a test mail")),
			"runNow":				(self.runNow,       _("Test run")),
		}, -2) # higher priority
		
		# Initialize Configuration part
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.buildConfig)
		self.buildConfig()
		
		# Override selectionChanged because our config tuples are bigger
		self.onChangedEntry = [ ]
		def selectionChanged():
			current = self["config"].getCurrent()
			if self["config"].current != current:
				if self["config"].current:
					self["config"].current[1].onDeselect(self.session)
				if current:
					current[1].onSelect(self.session)
				self["config"].current = current
			for x in self["config"].onSelectionChanged:
				x()
		self["config"].selectionChanged = selectionChanged
		
		self.setTitle(self.setup_title)

	def buildConfig(self, selectuniqueid=None):
		self.list = []
		select = None
		lappend = self.list.append
		
		lappend( getConfigListEntry( _("Enable PushService"), config.pushservice.enable, 0 ) )
		
		if config.pushservice.enable.value:
			lappend( getConfigListEntry( _("Dreambox name"), config.pushservice.boxname, 0 ) )
			lappend( getConfigListEntry( _("Config file"), config.pushservice.xmlpath, 0 ) )

			lappend( getConfigListEntry( _("Start time (HH:MM)"), config.pushservice.time, 0 ) )
			lappend( getConfigListEntry( _("Period in hours (0=disabled)"), config.pushservice.period, 0 ) )
			lappend( getConfigListEntry( _("Run on boot"), config.pushservice.runonboot, 0 ) )
			
			lappend( getConfigListEntry( _("SMTP Server"), config.pushservice.smtpserver, 0 ) )
			lappend( getConfigListEntry( _("SMTP Port"), config.pushservice.smtpport, 0 ) )
			lappend( getConfigListEntry( _("SMTP SSL"), config.pushservice.smtpssl, 0 ) )
			lappend( getConfigListEntry( _("SMTP TLS"), config.pushservice.smtptls, 0 ) )
			lappend( getConfigListEntry( _("User name"), config.pushservice.username, 0 ) )
			lappend( getConfigListEntry( _("Password"), config.pushservice.password, 0 ) )
			lappend( getConfigListEntry( _("Mail from"), config.pushservice.mailfrom, 0 ) )
			lappend( getConfigListEntry( _("Mail to or leave empty"), config.pushservice.mailto, 0 ) )
			
			if self.plugins:
				lappend( getConfigListEntry( separator, config.pushservice.about, 0 ) )
				
				for idx, plugin in enumerate(self.plugins):
					lappend( getConfigListEntry( plugin.getNameId(), plugin.getConfigEnable(), idx ) )
					if plugin.getUniqueID() == selectuniqueid:
						# Select the added plugin
						select = len(self.list)-1
					if plugin.getEnable():
						for key, element, description in plugin.getConfigOptions():
							lappend( getConfigListEntry( "  " + str(description), element, idx ) )
		
		self["config"].setList( self.list )
		del lappend
		
		if select is not None:
			self["config"].instance.moveSelectionTo(select)

	def addPlugin(self):
		self.hideHelpWindow()
		addlist = []
		pluginclasslist = []
		if self.plugins:
			pluginclasslist = [ plg.getPluginClass() for plg in self.plugins]
		for name, module in self.pushservice.modules.iteritems():
			if module.forceSingle():
				# We have to check if there is already a plugin instance
				if module in pluginclasslist:
					# A plugin instance already exists
					continue
			addlist.append( (name, name) )
			addlist.sort()
		self.session.openWithCallback(self.addPluginCB, ChoiceBox,_("Add plugin"), addlist)

	def addPluginCB(self, result):
		name = result and result[1]
		if name:
			plugin = self.pushservice.instantiatePlugin( name )
			if plugin:
				plugin.setEnable(True)
				
				self.plugins.append( plugin )
				self.plugins.sort( key=lambda x: ( x.getUniqueID() ) )
				
				self.buildConfig( plugin.getUniqueID() )

	def removePlugin(self):
		self.hideHelpWindow()
		if self.plugins:
			select = 0
			current = self["config"].getCurrent()
			if current:
				select = current[2]
			plist = []
			if self.plugins:
				plist = [( plugin.getNameId(), plugin ) for plugin in self.plugins ]
			self.session.openWithCallback(self.removePluginCB, ChoiceBox,_("Remove plugin"), list=plist, selection=select)

	def removePluginCB(self, result):
		plugin = result and result[1]
		if plugin:
			self.plugins.remove( plugin )
			self.buildConfig()

	# Overwrite ConfigListScreen keySave function
	def keySave(self):
		self.hideHelpWindow()
		
		# Save E2 PushService config
		self.saveAll()
		
		# Build xml config and write it
		self.pushservice.save(self.plugins)
		
		from plugin import gPushService
		global gPushService
		if config.pushservice.enable.value:
			gPushService = self.pushservice
			#TODO gPushService.load()
			gPushService.start() #with load
		else:
			gPushService = None
		
		self.close()

	# Overwrite ConfigListScreen keyCancel function
	def keyCancel(self):
		self.hideHelpWindow()
		# Call baseclass function
		ConfigListScreen.keyCancel(self)

	# Overwrite ConfigListScreen cancelConfirm function
	def cancelConfirm(self, result):
		from plugin import gPushService
		if gPushService:
			# Start PushService
			self.pushservice.start()
		
		# Call baseclass function
		ConfigListScreen.cancelConfirm(self, result)

	# Overwrite Screen close function
	def close(self):
		self.hideHelpWindow()
		from plugin import ABOUT
		self.session.openWithCallback(self.closeConfirm, MessageBox, ABOUT, MessageBox.TYPE_INFO)

	def closeConfirm(self, dummy=None):
		# Call baseclass function
		Screen.close(self)

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def pageUp(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)

	def pageDown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)

	def testMail(self):
		self.hideHelpWindow()
		self.testMailBox = None
		timeout = 30
		# Send test mail
		connector = self.pushservice.push(_("Test mail"), _("If You can see this, Your SMTP configuration is correct."), [], self.success, self.error, timeout=timeout)
		def testMailCB(result):
			connector.disconnect()
		self.testMailBox = self.session.openWithCallback(testMailCB, TestMailBox, _("Testing SMTP"), _("Sending test mail...\n\nCancel?"), MessageBox.TYPE_INFO, timeout=timeout)
	def success(self):
		if self.testMailBox:
			self.testMailBox.setText(_("The mail has been sent successfully"))
	def error(self, e):
		if self.testMailBox:
			self.testMailBox.setText(_("Mail sent failed:\n\n%s") % e.getErrorMessage())
			self.testMailBox.setText(_("Mail sent failed:\n\n%s\n\n%s") % (e.type, e.value))

	def runNow(self):
		self.hideHelpWindow()
		# Test actually not saved configuration
		response = self.pushservice.run(self.plugins, False)
		self.session.open(TestRunConsole, _("Test run"), response)

	def hideHelpWindow(self):
		current = self["config"].getCurrent()
		if current and hasattr(current[1], "help_window"):
			help_window = current[1].help_window
			if help_window:
				help_window.hide()


class TestMailBox(MessageBox):
	def __init__(self, session, title, text, type = MessageBox.TYPE_YESNO, timeout = -1, close_on_any_key = False, default = True, enable_input = True, msgBoxID = None):
		MessageBox.__init__(self, session, text, type, timeout, close_on_any_key, default, enable_input, msgBoxID)
		self.skinName = ["TestMailBox", "MessageBox"]
		self.setTitle(title)

	def setText(self, text):
		self.stopTimer()
		self["text"].setText(text)
		#self.resize()
		self.createGUIScreen(self.instance, self.desktop, updateonly = True)


class TestRunConsole(Screen):
	def __init__(self, session, title = "Console", text = ""):
		Screen.__init__(self, session)
		self.skinName = ["TestMailBox", "Console"]
			
		self["text"] = ScrollLabel("")
		self["actions"] = ActionMap(["WizardActions", "DirectionActions"], 
		{
			"ok": self.cancel,
			"back": self.cancel,
			"up": self["text"].pageUp,
			"down": self["text"].pageDown
		}, -1)
		self.setTitle(title)
		self.setText(text)

	def setText(self, text):
		self["text"].setText(text)

	def cancel(self):
		self.close()
