Version = '$Header$';

from __init__ import _

from enigma import eListboxPythonMultiContent, gFont
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText, ConfigSelection
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText

from Components.ActionMap import ActionMap

from Components.Network import iNetwork

def initInterfaceConfig(i=None, new=False):
	choices = getConfiguredIPs()

	if i is None and new is True:
		i = config.plugins.Webinterface.interfacecount.value
	elif i is None:
		i = config.plugins.Webinterface.interfacecount.value - 1

	print "[WebIfConfig.initInterfaceConfig] i is %s" % i
	config.plugins.Webinterface.interfaces.append(ConfigSubsection())
	config.plugins.Webinterface.interfaces[i].disabled = ConfigYesNo(default=False)
	config.plugins.Webinterface.interfaces[i].address = ConfigSelection(choices, default=choices[0])
	config.plugins.Webinterface.interfaces[i].port = ConfigInteger(80, (0, 65535))
	config.plugins.Webinterface.interfaces[i].useauth = ConfigYesNo(default=False)
	config.plugins.Webinterface.interfaces[i].usessl = ConfigYesNo(default=False)

	config.plugins.Webinterface.interfacecount.value = i + 1

	return i

def updateConfig():
	choices = getConfiguredIPs()
	default = choices[0]
	for c in config.plugins.Webinterface.interfaces:
		c.address.setChoices(choices, default=default)
		c.address.load()

def getConfiguredIPs():
	choices = [
		'0.0.0.0',
		'127.0.0.1'
	]
	for adaptername in iNetwork.ifaces:
		extip = iNetwork.ifaces[adaptername]['ip']
		if iNetwork.ifaces[adaptername]['up'] is True:
			extip = "%i.%i.%i.%i" % (extip[0], extip[1], extip[2], extip[3])
			choices.append(extip)
	return choices

def initConfig():
	interfacecount = config.plugins.Webinterface.interfacecount.value
	if interfacecount == 0:
		# setting default interface
		# 0.0.0.0:80 auth=False
		config.plugins.Webinterface.interfaces.append(ConfigSubsection())
		config.plugins.Webinterface.interfaces[0].disabled = ConfigYesNo(default=False)

		#needs to be refreshed before each call, because ifaces can be changed since e2 boot
		config.plugins.Webinterface.interfaces[0].address = ConfigSelection(getConfiguredIPs(), default='0.0.0.0')

		config.plugins.Webinterface.interfaces[0].port = ConfigInteger(80, (0, 65535))
		config.plugins.Webinterface.interfaces[0].useauth = ConfigYesNo(default=False)
		config.plugins.Webinterface.interfaces[0].usessl = ConfigYesNo(default=False)
		config.plugins.Webinterface.interfaces[0].save()

		config.plugins.Webinterface.interfacecount.value = 1
		config.plugins.Webinterface.interfacecount.save()
	else:
		i = 0
		while i < interfacecount:
			print "[WebIfConfig.initConfig] i is %s" % i
			initInterfaceConfig(i)
			i += 1

class WebIfConfigScreen(ConfigListScreen, Screen):
	skin = """
		<screen name="WebIfConfigScreen" position="center,center" size="560,400" title="Webinterface: Main Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget name="config" position="5,50" size="550,360" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>"""

	def __init__(self, session, args=0):
		Screen.__init__(self, session)
		l = [
			getConfigListEntry(_("Start Webinterface"), config.plugins.Webinterface.enable),
			getConfigListEntry(_("Enable /media"), config.plugins.Webinterface.includemedia),
			getConfigListEntry(_("Allow zapping via Webinterface"), config.plugins.Webinterface.allowzapping),
			getConfigListEntry(_("Autowrite timer"), config.plugins.Webinterface.autowritetimer),
			getConfigListEntry(_("Load movie-length"), config.plugins.Webinterface.loadmovielength)
		]

		ConfigListScreen.__init__(self, l)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Interfaces"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"yellow": self.openIfacesConfig,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("Webinterface: Main Setup"))

	def openIfacesConfig(self):
		print "yellow"
		self.session.open(WebIfInterfaceListConfigScreen)

	def save(self):
		print "saving"
		for x in self["config"].list:
			x[1].save()
		self.close(True, self.session)

	def cancel(self):
		print "cancel"
		for x in self["config"].list:
			x[1].cancel()
		self.close(False, self.session)

class WebIfInterfaceListConfigScreen(Screen):
	skin = """
		<screen name="WebIfInterfaceListConfigScreen" position="center,center" size="560,400" title="Webinterface: List of configured Interfaces" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<widget source="address" render="Label" position="10,50" size="150,50" font="Regular;20" halign="left" backgroundColor="#25062748" transparent="1" />
			<widget source="port" render="Label" position="125,50" size="50,50" font="Regular;20" halign="left" backgroundColor="#25062748" transparent="1" />
			<widget source="ssl" render="Label" position="175,50" size="50,50" font="Regular;20" halign="left" backgroundColor="#25062748" transparent="1" />
			<widget source="auth" render="Label" position="235,50" size="170,50" font="Regular;20" halign="left" backgroundColor="#25062748" transparent="1" />
			<widget source="disabled" render="Label" position="405,50" size="160,50" font="Regular;20" halign="left" backgroundColor="#25062748" transparent="1" />
			<widget name="ifacelist" position="5,80" size="550,300" scrollbarMode="showOnDemand"/>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["address"] = StaticText(_("Address"))
		self["port"] = StaticText(_("Port"))
		self["auth"] = StaticText(_("Authorization"))
		self["ssl"] = StaticText(_("SSL"))
		self["disabled"] =StaticText(_("Disabled"))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Add"))
		self["key_yellow"] = StaticText(_("Change"))
		self["key_blue"] = StaticText(_("Delete"))

		self["ifacelist"] = WebIfInterfaceList([])

		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions"],
			{
			 "ok"	:	self.keyGreen,
			 "back"	:	self.close,
			 "red"	:	self.close,
			 "green":	self.keyGreen,
			 "yellow":	self.keyYellow,
			 "blue"	:	self.keyDelete,
			 "up"	:	self.up,
			 "down"	:	self.down,
			 "left"	:	self.left,
			 "right":	self.right,
			 }, -1)

		self.updateList()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("Webinterface: List of configured Interfaces"))

	def updateList(self):
		ifaceguilist = []
		i = 0
		for c in config.plugins.Webinterface.interfaces:
			res = [
				i, #550,400
				MultiContentEntryText(pos=(5, 0), size=(150, 25), font=0, text=c.address.value),
				MultiContentEntryText(pos=(120, 0), size=(50, 25), font=0, text=str(c.port.value))
			]

			if c.usessl.value:
				res.append(MultiContentEntryText(pos=(170, 0), size=(200, 25), font=0, text=_("yes"), color=0x0000FF00))
			else:
				res.append(MultiContentEntryText(pos=(170, 0), size=(200, 25), font=0, text=_("no"), color=0x00FF0000))

			if c.useauth.value:
				res.append(MultiContentEntryText(pos=(230, 0), size=(170, 25), font=0, text=_("yes"), color=0x0000FF00))
			else:
				res.append(MultiContentEntryText(pos=(230, 0), size=(170, 25), font=0, text=_("no"), color=0x00FF0000))

			if c.disabled.value:
				res.append(MultiContentEntryText(pos=(400, 0), size=(160, 25), font=0, text=_("yes"), color=0x0000FF00))
			else:
				res.append(MultiContentEntryText(pos=(400, 0), size=(160, 25), font=0, text=_("no"), color=0x00FF0000))
			ifaceguilist.append(res)
			i += 1

		ifaceguilist.sort()
		self["ifacelist"].l.setList(ifaceguilist)

	def keyGreen(self):
		print "KEYGREEN"
		self.session.openWithCallback(self.updateList, WebIfInterfaceConfigScreen, None)

	def keyYellow(self):
		x = self["ifacelist"].getCurrent()[0]
		print "current list index", x
		self.session.openWithCallback(self.updateList, WebIfInterfaceConfigScreen, int(x))

	def keyDelete(self):
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Interface?"))

	def deleteConfirm(self, result):
		if not result:
			return
		x = self["ifacelist"].getCurrent()[0]
		print "current list index", x
		del(config.plugins.Webinterface.interfaces[int(x)])
		config.plugins.Webinterface.interfaces.save()
		config.plugins.Webinterface.interfacecount.value = config.plugins.Webinterface.interfacecount.value - 1;
		config.plugins.Webinterface.interfacecount.save()
		config.plugins.Webinterface.save()
		self.updateList()

	def up(self):
		self["ifacelist"].up()

	def down(self):
		self["ifacelist"].down()

	def left(self):
		self["ifacelist"].pageUp()

	def right(self):
		self["ifacelist"].pageDown()

class WebIfInterfaceList(MenuList):
	def __init__(self, list, enableWrapAround=False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		#self.l.setFont(1, gFont("Regular", 25))

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(25)

class WebIfInterfaceConfigScreen(Screen, ConfigListScreen):
	skin = """
		<screen name="WebIfInterfaceConfigScreen" position="center,center" size="560,400" title="Webinterface: Edit Interface">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<widget name="config" position="5,50" size="550,350" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, ifacenum):
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"blue": self.keyDelete,
			"cancel": self.keyCancel
		}, -2)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_blue"] = StaticText(_("Delete"))

		if ifacenum is None:
			i = initInterfaceConfig(None, True)
		else:
			i = ifacenum

		try:
			current = config.plugins.Webinterface.interfaces[i]
		except IndexError, e:
			print "[WebIf] iface config %i not found, adding it and setting default values" % i
			initInterfaceConfig()
			current = config.plugins.Webinterface.interfaces[ifacenum]

		#reloading current network devices
		current.address = ConfigSelection(getConfiguredIPs(), default=current.address.value)

		cfglist = [
			getConfigListEntry(_("Disabled"), current.disabled),
			getConfigListEntry(_("Address"), current.address),
			getConfigListEntry(_("Port"), current.port),
			getConfigListEntry(_("Require Authorization"), current.useauth),
			getConfigListEntry(_("SSL Encryption"), current.usessl)
		]
		ConfigListScreen.__init__(self, cfglist, session)
		self.ifacenum = i
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("Webinterface: Edit Interface"))

	def keySave(self):
		config.plugins.Webinterface.interfacecount.save()
		for x in self["config"].list:
			if isinstance(x[1].value, str):
				x[1].value = x[1].value.strip()
			x[1].save()
		config.plugins.Webinterface.save()
		self.close()

	def cancelConfirm(self, result):
		if result:
			config.plugins.Webinterface.interfacecount.cancel()
		self.callback = None
		ConfigListScreen.cancelConfirm(self, result)

	def keyDelete(self):
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Interface?"))

	def deleteConfirm(self, result):
		if not result:
			return
		del(config.plugins.Webinterface.interfaces[self.ifacenum])
		config.plugins.Webinterface.interfaces.save()
		config.plugins.Webinterface.interfacecount.value = config.plugins.Webinterface.interfacecount.value - 1;
		config.plugins.Webinterface.interfacecount.save()
		config.plugins.Webinterface.save()
		self.close()

