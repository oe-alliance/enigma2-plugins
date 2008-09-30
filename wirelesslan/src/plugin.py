# for localized messages
from __init__ import _

from enigma import eTimer
from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.config import config, getConfigListEntry, ConfigYesNo, NoSave, ConfigSubsection, ConfigText, ConfigSelection
from Components.ConfigList import ConfigListScreen
from Components.Network import Network, iNetwork
from Plugins.Plugin import PluginDescriptor
from os import system, path as os_path, listdir
from Wlan import Wlan, WlanList, wpaSupplicant

plugin_path = "/usr/lib/enigma2/python/Plugins/SystemPlugins/WirelessLan"

list = []
list.append(_("WEP"))
list.append(_("WPA"))
list.append(_("WPA2"))

config.plugins.wlan = ConfigSubsection()
config.plugins.wlan.essidscan = NoSave(ConfigYesNo(default = False))
config.plugins.wlan.essid = NoSave(ConfigText(default = "home", fixed_size = False))

config.plugins.wlan.encryption = ConfigSubsection()
config.plugins.wlan.encryption.enabled = NoSave(ConfigYesNo(default = False))
config.plugins.wlan.encryption.type = NoSave(ConfigSelection(list, default = _("WPA")))
config.plugins.wlan.encryption.psk = NoSave(ConfigText(default = "mysecurewlan", fixed_size = False))


class WlanStatus(Screen):
	skin = """
	<screen position="90,150" size="550,300" title="Wireless Network State" >
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
		<widget name="Statustext" position="20,250" size="115,21" zPosition="10" font="Regular;19" transparent="1"/>
		<widget name="statuspic_inactive" pixmap="skin_default/buttons/button_green_off.png" position="120,250" zPosition="10" size="15,16" transparent="1" alphatest="on"/>
		<widget name="statuspic_active" pixmap="skin_default/buttons/button_green.png" position="120,250" zPosition="10" size="15,16" transparent="1" alphatest="on"/>
		<widget name="ButtonRedtext" position="430,225" size="120,21" zPosition="10" font="Regular;21" transparent="1" />
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
		
		self["actions"] = NumberActionMap(["WizardActions", "InputActions", "EPGSelectActions", "ShortcutActions"],
		{
			"ok": self.exit,
			"back": self.exit,
			"red": self.exit,
		}, -1)
		self.onLayoutFinish.append(self.layoutFinished)
		
	def layoutFinished(self):
		self.setTitle(_("Wireless Network State"))
		
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
		<widget name="canceltext" position="450,325" size="120,21" zPosition="10" font="Regular;21" transparent="1" />
		<ePixmap pixmap="skin_default/buttons/button_green.png" position="50,325" zPosition="10" size="15,16" transparent="1" alphatest="on" />
		<widget name="selecttext" position="80,325" size="150,21" zPosition="10" font="Regular;21" transparent="1" />
		<ePixmap pixmap="skin_default/buttons/button_yellow.png" position="50,355" zPosition="10" size="15,16" transparent="1" alphatest="on" />
		<widget name="rescantext" position="80,355" size="150,21" zPosition="10" font="Regular;21" transparent="1" />
	</screen>
	"""

	
	def __init__(self, session, iface):
	
		Screen.__init__(self, session)
		self.session = session
		self.iface = iface
		self.skin = WlanScan.skin
		self.skin_path = plugin_path 
		
		
		self["info"] = Label()
		
		self.list = []	
		self["list"] = WlanList(self.session, self.iface)
		
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
		self.onLayoutFinish.append(self.layoutFinished)
		
	def layoutFinished(self):
		self.setTitle(_("Choose a Wireless Network"))
	
	def select(self):
		cur = self["list"].getCurrent()
		#print "CURRENT",cur
		if cur[1] is not None:
			essid = cur[0]
			if essid == '':
				essid = cur[1]
			encrypted = cur[2]
			self.close(essid,self["list"].getList())
		else:
			self.close(self["list"].getList())
	
	def WlanSetupClosed(self, *ret):
		if ret[0] == 2:
			self.close(None)
	
	def rescan(self):
		self["list"].reload()
		self.setInfo()
	
	def exit(self):
		self.close(None)

	def setInfo(self):
		length = self["list"].getLength()
		
		if length == 0:
			length = _("No") 
		self["info"].setText(str(length)+_(" Wireless Network(s) found!"))	


def WlanStatusScreenMain(session, iface):
	session.open(WlanStatus, iface)


def callFunction(iface):
	
	w = Wlan(iface)
	i = w.getWirelessInterfaces()
	if i:
		if iface in i:
			return WlanStatusScreenMain	
	
	return None


def configStrings(iface):
	driver = iNetwork.detectWlanModule()
	print "WLAN-MODULE",driver
	if driver == 'ralink':
		return "	pre-up /usr/sbin/wpa_supplicant -i"+iface+" -c/etc/wpa_supplicant.conf -B -Dralink\n	post-down wpa_cli terminate"
	if driver == 'madwifi':
		return "	pre-up /usr/sbin/wpa_supplicant -i"+iface+" -c/etc/wpa_supplicant.conf -B -dd -Dmadwifi\n	post-down wpa_cli terminate"
	if driver == 'zydas':
		return "	pre-up /usr/sbin/wpa_supplicant -i"+iface+" -c/etc/wpa_supplicant.conf -B -Dzydas\n	post-down wpa_cli terminate"

def Plugins(**kwargs):
	return PluginDescriptor(name=_("Wireless LAN"), description=_("Connect to a Wireless Network"), where = PluginDescriptor.WHERE_NETWORKSETUP, fnc={"ifaceSupported": callFunction, "configStrings": configStrings, "WlanPluginEntry": lambda x: "Wireless Network Configuartion..."})
	