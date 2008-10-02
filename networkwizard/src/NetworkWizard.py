# for localized messages
from __init__ import _

from Screens.Wizard import wizardManager, WizardSummary
from Components.Pixmap import Pixmap, MovingPixmap, MultiPixmap
from Components.config import config, ConfigBoolean, configfile, ConfigYesNo, NoSave, ConfigSubsection, ConfigText, getConfigListEntry, ConfigSelection
from Components.Network import iNetwork
from Components.Label import Label
from Components.MenuList import MenuList
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
import time, os, re
from WizardPluginLanguage import WizardPluginLanguage
from Screens.Rc import Rc

config.misc.firstrun = ConfigBoolean(default = True)
list = []
list.append(_("WEP"))
list.append(_("WPA"))
list.append(_("WPA2"))

config.plugins.wlan = ConfigSubsection()
config.plugins.wlan.essidscan = NoSave(ConfigYesNo(default = True))
config.plugins.wlan.essid = NoSave(ConfigText(default = "home", fixed_size = False))
config.plugins.wlan.encryption = ConfigSubsection()
config.plugins.wlan.encryption.enabled = NoSave(ConfigYesNo(default = False))
config.plugins.wlan.encryption.type = NoSave(ConfigSelection(list, default = _("WPA")))
config.plugins.wlan.encryption.psk = NoSave(ConfigText(default = "mysecurewlan", fixed_size = False))

class NetworkWizard(WizardPluginLanguage, Rc):
	skin = """
		<screen position="0,0" size="720,576" title="Welcome..." flags="wfNoBorder" >
			<widget name="text" position="153,50" size="340,300" font="Regular;22" />
			<widget source="list" render="Listbox" position="53,310" size="440,220" scrollbarMode="showOnDemand" >
				<convert type="StringList" />
			</widget>
			<widget name="config" position="53,310" zPosition="1" size="440,220" transparent="1" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/buttons/button_red.png" position="40,225" zPosition="0" size="15,16" transparent="1" alphatest="on" />
			<widget name="languagetext" position="55,225" size="95,30" font="Regular;18" />
			<widget name="wizard" pixmap="skin_default/wizard.png" position="40,50" zPosition="10" size="110,174" alphatest="on" />
			<widget name="rc" pixmaps="skin_default/rc.png,skin_default/rcold.png" position="500,50" zPosition="10" size="154,500" alphatest="on" />
			<widget name="arrowdown" pixmap="skin_default/arrowdown.png" position="-100,-100" zPosition="11" size="37,70" alphatest="on" />
			<widget name="arrowdown2" pixmap="skin_default/arrowdown.png" position="-100,-100" zPosition="11" size="37,70" alphatest="on" />
			<widget name="arrowup" pixmap="skin_default/arrowup.png" position="-100,-100" zPosition="11" size="37,70" alphatest="on" />
			<widget name="arrowup2" pixmap="skin_default/arrowup.png" position="-100,-100" zPosition="11" size="37,70" alphatest="on" />
		</screen>"""
	def __init__(self, session):
		self.xmlfile = resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkWizard/networkwizard.xml")
		WizardPluginLanguage.__init__(self, session, showSteps = False, showStepSlider = False)
		Rc.__init__(self)
		self.session = session
		self["wizard"] = Pixmap()
		
		self.InterfaceState = None
		self.isInterfaceUp = None
		self.WlanPluginInstalled = None
		self.ap = None
		self.selectedInterface = None
		self.NextStep = None
		
		self.isWlanPluginInstalled()

	def listInterfaces(self):
		list = [(iNetwork.getFriendlyAdapterName(x),x) for x in iNetwork.getAdapterList()]
		list.append((_("Exit wizard and configure later manually"), "end"))
		return list

	def InterfaceSelectionMade(self, index):
		self.selectedInterface = index
		self.InterfaceSelect(index)

	def InterfaceSelect(self, index):
		if index == 'end':
			self.NextStep = 'end'
		elif index == 'eth0':
			self.NextStep = 'nwconfig'
		else:
			self.NextStep = 'scanwlan'

	def InterfaceSelectionMoved(self):
		self.InterfaceSelect(self.selection)
		
	def checkInterface(self,iface):
		self.Adapterlist = iNetwork.getAdapterList()
		if len(self.Adapterlist) == 0:
			#Reset Network to defaults if network broken
			iNetwork.resetNetworkConfig('lan')
		if iface == 'eth0':
			iNetwork.resetNetworkConfig('lan')
			self.InterfaceUp('eth0')
		if iface == 'wlan0':
			iNetwork.resetNetworkConfig('wlan')
			self.InterfaceUp('wlan0')
		if iface == 'ath0':
			iNetwork.resetNetworkConfig('wlan-mpci')
			self.InterfaceUp('ath0')
			
	def InterfaceUp(self,iface):
		iNetwork.getInterfaces()
		if iNetwork.getAdapterAttribute(iface, 'up') is True:
			self.isInterfaceUp = True
		else:
			self.isInterfaceUp = False
			
	def markDone(self):
		pass

	def listModes(self):
		list = []
		try:
			from Plugins.SystemPlugins.WirelessLan.Wlan import Wlan
		except ImportError:
			list.append( ( _("No Networks found"),_("unavailable") ) )
			return list
		else:	
			self.w = Wlan(self.selectedInterface)
			aps = self.w.getNetworkList()
			if aps is not None:
				print "[Wlan.py] got Accespoints!"
				for ap in aps:
					a = aps[ap]
					if a['active']:
						if a['essid'] == "":
							a['essid'] = a['bssid']
						list.append( (a['essid'], a['essid']) )
			else:
				list.append( ( _("No Networks found"),_("unavailable") ) )
			list.sort(key = lambda x: x[0])
			return list

	def modeSelectionMade(self, index):
		self.ap = index
		self.modeSelect(index)
		
	def modeSelectionMoved(self):
		self.modeSelect(self.selection)
		
	def modeSelect(self, mode):
		print "ModeSelected:", mode

	def saveAccessPoint(self, mode):
		from Plugins.SystemPlugins.WirelessLan.Wlan import wpaSupplicant,Wlan
		self.ws = wpaSupplicant()
		wsconfig = self.ws.loadConfig()
		config.plugins.wlan.essid.value = str(mode)
		config.plugins.wlan.essid.save()
		self.ws.writeConfig()

	def checkNetwork(self):
		ret = iNetwork.checkNetworkState()
		if ret == True:
			self.InterfaceState = True
		else:
			self.InterfaceState = False

	def restartNetwork(self):
		iNetwork.restartNetwork()
		self.checkNetwork()
	
	def isWlanPluginInstalled(self):		
		try:
			from Plugins.SystemPlugins.WirelessLan.Wlan import Wlan
		except ImportError:
			self.WlanPluginInstalled = False
		else:
			self.WlanPluginInstalled = True

	def AdapterSetupEnd(self, iface):
		self.iface = iface
		if iNetwork.getAdapterAttribute(self.iface, "dhcp") is True:
			self.checkNetwork()
			self.NextStep = 'checklanstatusend'
		else:
			self.NextStep = 'confdns'
			


