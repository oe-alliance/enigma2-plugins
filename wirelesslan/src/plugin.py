from enigma import eTimer
from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Network import Network, iNetwork
from Plugins.Plugin import PluginDescriptor
from os import system
from Wlan import Wlan, WlanList, wpaSupplicant

plugin_path = "/usr/lib/enigma2/python/Plugins/SystemPlugins/WirelessLan"

class WlanSelectScreen(Screen):
	skin = """
	<screen position="185,238" size="350,100" title="Wireless Network Tools" >
		<widget name="menu" position="10,10" size="330,80" scrollbarMode="showOnDemand" />
	</screen>
	"""
	
	
	def __init__(self, session, iface):
		Screen.__init__(self, session)
		self.session = session
		
		self.skin = WlanSelectScreen.skin
		self.skin_path = plugin_path 		
		
		self.iface = iface
		
		list = []
		list.append(_("Scan for Wireless Networks")) 
		list.append(_("Show WLAN Status"))
		list.append(_("Edit Wireless Settings"))
		
		
		self["menu"] = MenuList(list)
		
		self["actions"] = NumberActionMap(["WizardActions", "InputActions", "EPGSelectActions"],
		{
			"ok": self.ok,
			"back": self.exit,
		}, -1)


	def ok(self):
		idx = self["menu"].getSelectedIndex()
		if idx is 0:
			self.session.open(WlanScan, self.iface)
			print "[plugin.py:Wireless] Starting WlanScan"
		elif idx is 1:
			self.session.open(WlanStatus, self.iface)
			print "[plugin.py:Wireless] Starting WlanStatus"

		elif idx is 2:
			self.session.open(WlanConfiguration, self.iface)
			print "[plugin.py:Wireless] Starting Manual Configuration"

		else:
			print "[plugin.py:Wireless] Unkown Menupoint"
				
	
	def exit(self):
		self.close()



class WlanStatus(Screen):
	#<screen position="185,188" size="350,223" title="Wireless Network Status" >
	skin = """
	<screen position="90,150" size="550,300" title="Wireless Network Status" >
		<widget name="LabelBSSID" position="10,10" size="150,25" valign="left" font="Regular;20" transparent="1" foregroundColor="#FFFFFF" />
		<widget name="LabelESSID" position="10,38" size="150,25" valign="center" font="Regular;20" transparent="1" foregroundColor="#FFFFFF" />
		<widget name="LabelQuality" position="10,66" size="150,25" valign="center" font="Regular;20" transparent="1" foregroundColor="#FFFFFF" />
		<widget name="LabelSignal" position="10,94" size="150,25" valign="center" font="Regular;20" transparent="1" foregroundColor="#FFFFFF" />
		<widget name="LabelBitrate" position="10,122" size="150,25" valign="center" font="Regular;20" transparent="1" foregroundColor="#FFFFFF" />
		<widget name="LabelChannel" position="10,150" size="150,25" valign="center" font="Regular;20" transparent="1" foregroundColor="#FFFFFF" />
		
		<widget name="BSSID" position="320,10" size="180,25" valign="center" font="Regular;20" transparent="1" foregroundColor="#FFFFFF" />
		<widget name="ESSID" position="320,38" size="180,25" valign="center" font="Regular;20" transparent="1" foregroundColor="#FFFFFF" />
		<widget name="quality" position="320,66" size="180,25" valign="center" font="Regular;20" transparent="1" foregroundColor="#FFFFFF" />
		<widget name="signal" position="320,94" size="180,25" valign="center" font="Regular;20" transparent="1" foregroundColor="#FFFFFF" />
		<widget name="bitrate" position="320,122" size="180,25" valign="center" font="Regular;20" transparent="1" foregroundColor="#FFFFFF" />
		<widget name="channel" position="320,150" size="180,25" valign="center" font="Regular;20" transparent="1" foregroundColor="#FFFFFF" />
		
		<widget name="BottomBG" pixmap="skin_default/bottombar.png" position="5,210" size="540,120" zPosition="1" transparent="1" alphatest="on" />
		<widget name="IFtext" position="20,225" size="100,21" zPosition="10" font="Regular;19" transparent="1" />
		<widget name="IF" position="110,225" size="300,21" zPosition="10" font="Regular;19" transparent="1" />
		<widget name="Statustext" position="20,250" size="60,21" zPosition="10" font="Regular;19" transparent="1"/>
		<widget name="statuspic_inactive" pixmap="skin_default/buttons/button_green_off.png" position="70,250" zPosition="10" size="15,16" transparent="1" alphatest="on"/>
		<widget name="statuspic_active" pixmap="skin_default/buttons/button_green.png" position="70,250" zPosition="10" size="15,16" transparent="1" alphatest="on"/>
		<widget name="ButtonRedtext" position="430,225" size="80,21" zPosition="10" font="Regular;21" transparent="1" />
		<widget name="ButtonRed" pixmap="skin_default/buttons/button_red.png" position="410,225" zPosition="10" size="15,16" transparent="1" alphatest="on" />

	</screen>
	"""
	
	
	def __init__(self, session, iface):
		
		Screen.__init__(self, session)
		
		self.session = session
		self.iface = iface
		self.skin = WlanStatus.skin
		
		self.timer = eTimer()
		self.timer.timeout.get().append(self.resetList) 
		self.onShown.append(lambda: self.timer.start(5000))
						    
		self["LabelBSSID"] = Label(_('Accesspoint:'))
		self["LabelESSID"] = Label(_('SSID:'))
		self["LabelQuality"] = Label(_('Link Quality:'))
		self["LabelSignal"] = Label(_('Signal Strength:'))
		self["LabelBitrate"] = Label(_('Bitrate:'))
		self["LabelChannel"] = Label(_('Channel:'))
			
		self["BSSID"] = Label()
		self["ESSID"] = Label()
		self["quality"] = Label()
		self["signal"] = Label()
		self["bitrate"] = Label()
		self["channel"] = Label()

		self["IFtext"] = Label()
		self["IF"] = Label()
		self["Statustext"] = Label()
		self["statuspic_active"] = Pixmap()
		self["statuspic_active"].hide()
		self["statuspic_inactive"] = Pixmap()
		self["statuspic_inactive"].hide()
		self["BottomBG"] = Pixmap()
		self["ButtonRed"] = Pixmap()
		self["ButtonRedtext"] = Label(_("Close"))

		self.resetList()
		self.updateStatusbar()
		
		self["actions"] = NumberActionMap(["WizardActions", "InputActions", "EPGSelectActions"],
		{
			"ok": self.exit,
			"back": self.exit,
		}, -1)
		
	
	def resetList(self):
		w = Wlan(self.iface)
		stats = w.getStatus()
		if stats['BSSID'] == "00:00:00:00:00:00":
			stats['BSSID'] = _("No Connection!")
		self["BSSID"].setText(stats['BSSID'])
		self["ESSID"].setText(stats['ESSID'])
		self["quality"].setText(stats['quality']+"%")
		self["signal"].setText(stats['signal']+"%")
		self["bitrate"].setText(stats['bitrate'])
		self["channel"].setText(stats['channel'])
		
	
	def exit(self):
		self.timer.stop()
		self.close()	

	def updateStatusbar(self):
		self["IFtext"].setText(_("Network:"))
		self["IF"].setText(iNetwork.getFriendlyAdapterName(self.iface))
		self["Statustext"].setText(_("Link:"))
		w = Wlan(self.iface)
		stats = w.getStatus()
		if stats['BSSID'] == "00:00:00:00:00:00":
			self["statuspic_active"].hide()
			self["statuspic_inactive"].show()
		else:
			self["statuspic_active"].show()
			self["statuspic_inactive"].hide()


class WlanScan(Screen):
	skin = """
	<screen position="70,90" size="600,400" title="Choose a Wireless Network" >
		<widget name="info" position="10,10" size="580,30" font="Regular;24" transparent="1" foregroundColor="#FFFFFF" />
		<widget name="list" position="10,50" size="580,240" scrollbarMode="showOnDemand" />

		<ePixmap pixmap="skin_default/bottombar.png" position="30,310" size="540,120" zPosition="1" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/button_red.png" position="430,325" zPosition="10" size="15,16" transparent="1" alphatest="on" />
		<widget name="canceltext" position="450,325" size="80,21" zPosition="10" font="Regular;21" transparent="1" />
		<ePixmap pixmap="skin_default/buttons/button_green.png" position="50,325" zPosition="10" size="15,16" transparent="1" alphatest="on" />
		<widget name="selecttext" position="80,325" size="150,21" zPosition="10" font="Regular;21" transparent="1" />
		<ePixmap pixmap="skin_default/buttons/button_yellow.png" position="50,355" zPosition="10" size="15,16" transparent="1" alphatest="on" />
		<widget name="rescantext" position="80,355" size="150,21" zPosition="10" font="Regular;21" transparent="1" />
	</screen>
	"""

	
	def __init__(self, session, iface):
	
		Screen.__init__(self, session)
		self.session = session

		self.skin = WlanScan.skin
		self.skin_path = plugin_path 
		
		
		self["info"] = Label()
		
		self.list = []	
		self["list"] = WlanList(self.session, iface)
		
		self.setInfo()
		
		self["canceltext"] = Label(_("Close"))
		self["selecttext"] = Label(_("Connect"))
		self["rescantext"] = Label(_("Refresh"))
			
		self["actions"] = NumberActionMap(["WizardActions", "InputActions", "EPGSelectActions"],
		{
			"ok": self.select,
			"back": self.exit,
		}, -1)
		
		self["shortcuts"] = ActionMap(["ShortcutActions"],
		{
		 	"red": self.exit,
			"green": self.select,
			"yellow": self.rescan,
		})

	
	def select(self):
		cur = self["list"].getCurrent()
		print "CURRENT",cur
		if cur[1] is not None:
			essid = cur[0]
			encrypted = cur[2]
			iface = cur[3]
			self.session.openWithCallback(self.WlanSetupClosed, WlanConfiguration, iface, essid, encrypted)
		else:
			self.session.openWithCallback(self.WlanSetupClosed, WlanConfiguration)
	
	def WlanSetupClosed(self, *ret):
		print "RET im WlanSetupClosed",ret
		if ret[0] == 2:
			self.close()
	
	def rescan(self):
		self["list"].reload()
		self.setInfo()
	
	def exit(self):
		self.close( (None ,) )

	def setInfo(self):
		length = self["list"].getLength()
		
		if length == 0:
			length = "No" 
		self["info"].setText(str(length)+_(" Wireless Network(s) found!"))	


	
class WlanConfiguration(ConfigListScreen, Screen):
	skin = """
		<screen position="90,100" size="550,400" title="Wireless Network Configuration" >
			<widget name="interface" position="10,10" size="530,30" font="Regular;24" valign="center" />
			<widget name="config" position="10,60" size="530,150" scrollbarMode="showOnDemand" />
			
			<ePixmap name="BottomBG" pixmap="skin_default/bottombar.png" position="5,310" size="540,120" zPosition="1" transparent="1" alphatest="on" />
			<widget name="Adaptertext" position="20,325" size="100,21" zPosition="10" font="Regular;19" transparent="1" />
			<widget name="Adapter" position="110,325" size="300,21" zPosition="10" font="Regular;19" transparent="1" />
			<widget name="introduction" position="110,360" size="300,20" zPosition="10" font="Regular;21" halign="center" transparent="1" />
			<widget name="ButtonRedtext" position="430,325" size="80,21" zPosition="10" font="Regular;21" transparent="1" />
			<ePixmap name="ButtonRed" pixmap="skin_default/buttons/button_red.png" position="410,325" zPosition="10" size="15,16" transparent="1" alphatest="on" />
		</screen>
	"""
	
	def __init__(self, session, iface = "wlan0", essid = None, encrypted = False):		
		Screen.__init__(self, session)		
		self.skin = WlanConfiguration.skin
		print "ESSID,",essid
		self.iface = iface
		self.list = []
		self.ws = wpaSupplicant()
		
		self["introduction"] = Label(_("Press OK to activate the settings."))
		self["interface"] = Label(_("Interface: ")+self.iface)
		self["Adaptertext"] = Label(_("Network:"))
		self["Adapter"] = Label(iNetwork.getFriendlyAdapterName(self.iface))
		self["ButtonRedtext"] = Label(_("Close"))
		
		if essid is None:
			self.ws.loadConfig()
		
		else:
			config.plugins.wlan.essid.value = essid
			config.plugins.wlan.encryption.enabled.value = True
			

		self["actions"] = ActionMap(["SetupActions"],
		{
			"ok": self.ok,
			"cancel": self.cancel,
		}, -2)
		
		ConfigListScreen.__init__(self, self.list)
		self.createSetup()

	
	def createSetup(self):
		self.list = [ ]
						
		self.list.append(getConfigListEntry(_("Network SSID"), config.plugins.wlan.essid))
		#self.list.append(getConfigListEntry(_("Encryption"), config.plugins.wlan.encryption.enabled))
		self.encryptionEnabled = getConfigListEntry(_("Encryption"), config.plugins.wlan.encryption.enabled)
		self.list.append(self.encryptionEnabled)		
		if config.plugins.wlan.encryption.enabled.value:
			self.list.append(getConfigListEntry(_("Encryption Type"), config.plugins.wlan.encryption.type))
			self.list.append(getConfigListEntry(_("Encryption Key"), config.plugins.wlan.encryption.psk))
		
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	
	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()

	
	def ok(self):
		self.ws.writeConfig()
		iNetwork.deactivateNetworkConfig()
		iNetwork.activateNetworkConfig()
		self.close(2)

	def cancel(self):
		self.close(1)



def EntryChosen(parms):
	if parms[0]:
		session = parms[0]
		if parms[1] is not None:
			val = parms[1]
			essid = val[0]
			encrypted = val[2]
			iface = val[3]
			session.open(WlanConfiguration, iface, essid, encrypted)
		else:
			session.open(WlanConfiguration)


def WlanSelectScreenMain(session, iface):
	session.open(WlanSelectScreen, iface)


def callFunction(iface):
	
	w = Wlan(iface)
	i = w.getWirelessInterfaces()
	if i:
		if iface in i:
			return WlanSelectScreenMain	
	
	return None


def configStrings(iface):
	ret=system("dmesg | grep \"rt73: using permanent MAC addr\"")
	ret2=system("dmesg | grep \"rt73: using net dev supplied MAC addr\"")
	if ret == 0 or ret2 == 0:
		return "	post-down start-stop-daemon -K -x /usr/sbin/wpa_supplicant\n	pre-up /usr/sbin/wpa_supplicant -i"+iface+" -c/etc/wpa_supplicant.conf -B -Dralink"
	else:
		return "	post-down start-stop-daemon -K -x /usr/sbin/wpa_supplicant\n	pre-up /usr/sbin/wpa_supplicant -i"+iface+" -c/etc/wpa_supplicant.conf -B"
	

def Plugins(**kwargs):
	return PluginDescriptor(name=_("Wireless LAN"), description=_("Connect to a Wireless Network"), where = PluginDescriptor.WHERE_NETWORKSETUP, fnc={"ifaceSupported": callFunction, "configStrings": configStrings, "menuEntryName": lambda x: "Wireless Network Configuartion..."})
	