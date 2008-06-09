from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER
from Components.MultiContent import MultiContentEntryText
from Components.GUIComponent import GUIComponent
from Components.HTMLComponent import HTMLComponent
from Components.config import config, ConfigYesNo, NoSave, ConfigSubsection, ConfigText, ConfigSelection

from os import system
from string import maketrans, strip
from iwlibs import getNICnames, Wireless, Iwfreq

list = []
list.append(_("WEP"))
list.append(_("WPA"))
list.append(_("WPA2"))

config.plugins.wlan = ConfigSubsection()
config.plugins.wlan.essid = NoSave(ConfigText(default = "home", fixed_size = False))

config.plugins.wlan.encryption = ConfigSubsection()
config.plugins.wlan.encryption.enabled = NoSave(ConfigYesNo(default = False))
config.plugins.wlan.encryption.type = NoSave(ConfigSelection(list, default = _("WPA")))
config.plugins.wlan.encryption.psk = NoSave(ConfigText(default = "mysecurewlan", fixed_size = False))

class Wlan:
	def __init__(self, iface):
		a = ''; b = ''
		
		for i in range(0, 255):
		    a = a + chr(i)
		    if i < 32 or i > 127:
			b = b + ' '
		    else:
			b = b + chr(i)
		
		self.iface = iface
		self.asciitrans = maketrans(a, b)

	
	def asciify(self, str):
		return str.translate(self.asciitrans)

	
	def getWirelessInterfaces(self):
		iwifaces = None
		try:
			iwifaces = getNICnames()
		except:
			print "[Wlan.py] No Wireless Networkcards could be found"
		
		return iwifaces

	
	def getNetworkList(self):
		ifobj = Wireless(self.iface) # a Wireless NIC Object
		print "ifobj.getStatistics(): ", ifobj.getStatistics()
		
		#Association mappings
		stats, quality, discard, missed_beacon = ifobj.getStatistics()
		snr = quality.signallevel - quality.noiselevel
		system("ifconfig "+self.iface+" up")
		
		try:
			scanresults = ifobj.scan()
		except:
			scanresults = None
			print "[Wlan.py] No Wireless Networks could be found"
		
		if scanresults is not None:
			aps = {}
			for result in scanresults:
				
				bssid = result.bssid
		
				encryption = map(lambda x: hex(ord(x)), result.encode)
		
				if encryption[-1] == "0x8":
					encryption = True
				else:
					encryption = False
		
				extra = []
				for element in result.custom:
					element = element.encode()
					extra.append( strip(self.asciify(element)) )
				
				print result.quality.getSignallevel()
				
				if result.quality.sl is 0 and len(extra) > 0:
					begin = extra[0].find('SignalStrength=')+15
									
					done = False
					end = begin+1
					
					while not done:
						if extra[0][begin:end].isdigit():
							end += 1
						else:
							done = True
							end -= 1
					
					signal = extra[0][begin:end]
					print "[Wlan.py] signal is:" + str(signal)

				else:
					signal = str(result.quality.sl)
				
				aps[bssid] = {
					'active' : True,
					'bssid': result.bssid,
					'channel': result.frequency.getChannel(result.frequency.getFrequency()),
					'encrypted': encryption,
					'essid': strip(self.asciify(result.essid)),
					'iface': self.iface,
					'maxrate' : result.rate[-1],
					'noise' : result.quality.getNoiselevel(),
					'quality' : str(result.quality.quality),
					'signal' : signal,
					'custom' : extra,
				}
				print aps[bssid]
			return aps

		
	def getStatus(self):
		ifobj = Wireless(self.iface)
		fq = Iwfreq()
		
		status = {
				  'BSSID': str(ifobj.getAPaddr()),
				  'ESSID': str(ifobj.getEssid()),
				  'quality': str(ifobj.getStatistics()[1].quality),
				  'signal': str(ifobj.getStatistics()[1].sl),
				  'bitrate': str(ifobj.getBitrate()),
				  'channel': str(fq.getChannel(str(ifobj.getFrequency()[0:-3]))),
		}
		
		for (key, item) in status.items():
			if item is "None" or item is "":
					status[key] = _("N/A")
				
		return status



class WlanList(HTMLComponent, GUIComponent):
	def __init__(self, session, iface):
		
		GUIComponent.__init__(self)
		self.w = Wlan(iface)
		self.iface = iface
		
		self.length = 0
		
		self.l = None
		self.l = eListboxPythonMultiContent()
		
		self.l.setFont(0, gFont("Regular", 32))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setFont(2, gFont("Regular", 16))
		self.l.setBuildFunc(self.buildWlanListEntry)		
				
		self.reload()
	
	
	def buildWlanListEntry(self, essid, bssid, encrypted, iface, maxrate, signal):                                                                                                 
		
		res = [ (essid, encrypted, iface) ]
		
		if essid == "":
			essid = bssid
		
		e = encrypted and _("Yes") or _("No")
		res.append( MultiContentEntryText(pos=(0, 0), size=(470, 35), font=0, flags=RT_HALIGN_LEFT, text=essid) )
		res.append( MultiContentEntryText(pos=(425, 0), size=(60, 20), font=1, flags=RT_HALIGN_LEFT, text=_("Signal: ")))
		res.append( MultiContentEntryText(pos=(480, 0), size=(70, 35), font=0, flags=RT_HALIGN_RIGHT, text="%s" %signal))
		res.append( MultiContentEntryText(pos=(0, 40), size=(180, 20), font=1, flags=RT_HALIGN_LEFT, text=_("Max. Bitrate: %s") %maxrate ))
		res.append( MultiContentEntryText(pos=(190, 40), size=(180, 20), font=1, flags=RT_HALIGN_CENTER, text=_("Encrypted: %s") %e ))
		res.append( MultiContentEntryText(pos=(360, 40), size=(190, 20), font=1, flags=RT_HALIGN_RIGHT, text=_("Interface: %s") %iface ))
		return res
		
			
	def reload(self):
		aps = self.w.getNetworkList()
		list = []
		if aps is not None:
			print "[Wlan.py] got Accespoints!"
			for ap in aps:
				a = aps[ap]
				if a['active']:
					list.append( (a['essid'], a['bssid'], a['encrypted'], a['iface'], a['maxrate'], a['signal']) )
		
		self.length = len(list)
		self.l.setList([])
		self.l.setList(list)
		 	
	GUI_WIDGET = eListbox


	def getCurrent(self):
		return self.l.getCurrentSelection()
	
	
	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.setItemHeight(60)
	
	
	def getLength(self):
		return self.length



class wpaSupplicant:
	def __init__(self):
		pass
	
		
	def writeConfig(self):	
			
			essid = config.plugins.wlan.essid.value
			encrypted = config.plugins.wlan.encryption.enabled.value
			encryption = config.plugins.wlan.encryption.type.value
			psk = config.plugins.wlan.encryption.psk.value

		
			fp = file('/etc/wpa_supplicant.conf', 'w')
			fp.write('#WPA Supplicant Configuration by enigma2\n\n')
			fp.write('ctrl_interface=/var/run/wpa_supplicant\n')
			fp.write('ctrl_interface_group=0\n')
			fp.write('network={\n')
			fp.write('\tssid="'+essid+'"\n')
			fp.write('\tscan_ssid=1\n')
			
			if encrypted:
							
				if encryption == 'WPA' or encryption == 'WPA2':
					fp.write('\tkey_mgmt=WPA-PSK\n')
					
					if encryption == 'WPA':
						fp.write('\tproto=WPA\n')
						fp.write('\tpairwise=TKIP\n')
						fp.write('\tgroup=TKIP\n')
					else:
						fp.write('\tproto=WPA RSN\n')
						fp.write('\tpairwise=CCMP TKIP\n')
						fp.write('\tgroup=CCMP TKIP\n')
					
					fp.write('\tpsk="'+psk+'"\n')
				
				elif encryption == 'WEP':
					fp.write('\tkey_mgmt=NONE\n')
					fp.write('\twep_key0="'+psk+'"\n')
			else:
				fp.write('\tkey_mgmt=NONE\n')			
			fp.write('}')	
			fp.close()
				
			
	def loadConfig(self):
		try:
			#parse the wpasupplicant configfile
			fp = file('/etc/wpa_supplicant.conf', 'r')
			supplicant = fp.readlines()
			fp.close()
			
			for s in supplicant:
			
				split = s.strip().split('=')
				if split[0] == 'ssid':
					print "[Wlan.py] Got SSID "+split[1][1:-1]
					config.plugins.wlan.essid.value = split[1][1:-1]
					
				elif split[0] == 'proto':
					config.plugins.wlan.encryption.enabled.value = True
					if split[1] == "WPA RSN" : split[1] = 'WPA2'
					config.plugins.wlan.encryption.type.value = split[1]
					print "[Wlan.py] Got Encryption: "+split[1]
					
				elif split[0] == 'wep_key0':
					config.plugins.wlan.encryption.enabled.value = True
					config.plugins.wlan.encryption.type.value = 'WEP'
					config.plugins.wlan.encryption.psk.value = split[1][1:-1]
					print "[Wlan.py] Got Encryption: WEP - key0 is: "+split[1][1:-1]
					
				elif split[0] == 'psk':
					config.plugins.wlan.encryption.psk.value = split[1][1:-1]
					print "[Wlan.py] Got PSK: "+split[1][1:-1]
				else:
					pass
				
		except:
			print "[Wlan.py] Error parsing /etc/wpa_supplicant.conf"
	
	
	def restart(self, iface):
		system("start-stop-daemon -K -x /usr/sbin/wpa_supplicant")
		system("start-stop-daemon -S -x /usr/sbin/wpa_supplicant -- -B -i"+iface+" -c/etc/wpa_supplicant.conf")
