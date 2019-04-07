# -*- coding: utf-8 -*-
# for localized messages
from __init__ import _
from enigma import eTimer
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.Network import iNetwork
from Components.Console import Console
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_ACTIVE_SKIN, fileExists
from Tools.LoadPixmap import LoadPixmap
from cPickle import dump, load
import os
import time
import subprocess
import xml.dom.minidom

from AutoMount import iAutoMount
from MountEdit import AutoMountEdit
from UserDialog import UserDialog

def formatIp(ip):
	if ip is None or len(ip) != 4:
		return "0.0.0.0"
	return "%d.%d.%d.%d" % (ip[0], ip[1], ip[2], ip[3])

def write_cache(cache_file, cache_data):
	#Does a cPickle dump
	if not os.path.isdir(os.path.dirname(cache_file)):
		try:
			os.mkdir(os.path.dirname(cache_file))
		except OSError as e:
			print "[Networkbrowser] Can not create cache file directory %s: %s" % (os.path.dirname(cache_file), str(e))
	fd = open(cache_file, 'w')
	dump(cache_data, fd, -1)
	fd.close()

def valid_cache(cache_file, cache_ttl):
	#See if the cache file exists and is still living
	try:
		mtime = os.stat(cache_file).st_mtime
	except:
		return 0
	curr_time = time.time()
	if (curr_time - mtime) > cache_ttl:
		return 0
	else:
		return 1

def load_cache(cache_file):
	#Does a cPickle load
	fd = open(cache_file)
	cache_data = load(fd)
	fd.close()
	return cache_data

class NetworkDescriptor:
	def __init__(self, name = "NetworkServer", description = ""):
		self.name = name
		self.description = description

class NetworkBrowser(Screen):
	skin = """
		<screen name="NetworkBrowser" position="center,center" size="560,450" title="Network Neighbourhood">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<widget source="list" render="Listbox" position="5,50" size="540,350" zPosition="10" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template": [
							MultiContentEntryPixmapAlphaTest(pos = (0, 0), size = (48, 48), png = 1), # index 1 is the expandable/expanded/verticalline icon
							MultiContentEntryText(pos = (50, 4), size = (420, 26), font=2, flags = RT_HALIGN_LEFT, text = 2), # index 2 is the Hostname
							MultiContentEntryText(pos = (140, 5), size = (320, 25), font=0, flags = RT_HALIGN_LEFT, text = 3), # index 3 is the sharename
							MultiContentEntryText(pos = (140, 26), size = (320, 17), font=1, flags = RT_HALIGN_LEFT, text = 4), # index 4 is the sharedescription
							MultiContentEntryPixmapAlphaTest(pos = (45, 0), size = (48, 48), png = 5), # index 5 is the nfs/cifs icon
							MultiContentEntryPixmapAlphaTest(pos = (90, 0), size = (48, 48), png = 6), # index 6 is the isMounted icon
						],
					"fonts": [gFont("Regular", 20),gFont("Regular", 14),gFont("Regular", 24)],
					"itemHeight": 50
					}
				</convert>
			</widget>
			<ePixmap pixmap="skin_default/div-h.png" position="0,410" zPosition="1" size="560,2" />
			<widget source="infotext" render="Label" position="0,420" size="560,30" zPosition="10" font="Regular;21" halign="center" valign="center" backgroundColor="#25062748" transparent="1" />
		</screen>"""

	def __init__(self, session, iface, plugin_path):
		Screen.__init__(self, session)
		self.skin_path = plugin_path
		self.session = session
		self.iface = iface
		if self.iface is None:
			self.iface = self.GetNetworkInterfaces()
		if self.iface is None:
			self.iface = 'eth0'
		print "[Networkbrowser] Using Network Interface: %s" % self.iface
		self.networklist = None
		self.mounts = None
		self.onChangedEntry = []
		self.expanded = {}
		self.cache_ttl = 604800 #Seconds cache is considered valid, 7 Days should be ok
		self.cache_file = '/etc/enigma2/networkbrowser.cache' #Path to cache directory
		self.Console = Console()

		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Login..."))
		self["key_yellow"] = StaticText(_("Rescan"))
		self["key_blue"] = StaticText()
		self["infotext"] = StaticText(_("Press OK to mount!"))

		self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions"],
		{
			"ok": self.go,
			"back": self.close,
			"red": self.close,
			"green": self.setCredentials,
			"yellow": self.keyYellow,
		})

		self.list = []
		self.statuslist = []
		self.listindex = 0
		self["list"] = List(self.list)
		self["list"].onSelectionChanged.append(self.selectionChanged)

		self.onLayoutFinish.append(self.startRun)
		self.onShown.append(self.setWindowTitle)
		self.onClose.append(self.cleanup)
		self.Timer = eTimer()
		self.Timer.callback.append(self.TimerFire)

	def GetNetworkInterfaces(self):
		self.adapters = [(iNetwork.getFriendlyAdapterName(x),x) for x in iNetwork.getAdapterList()]

		if not self.adapters:
			self.adapters = [(iNetwork.getFriendlyAdapterName(x),x) for x in iNetwork.getConfiguredAdapters()]

		if len(self.adapters) == 0:
			self.adapters = [(iNetwork.getFriendlyAdapterName(x),x) for x in iNetwork.getInstalledAdapters()]

		for x in self.adapters:
			if iNetwork.getAdapterAttribute(x[1], 'up') is True:
				return x[1]
		return None

	def cleanup(self):
		del self.Timer
		iAutoMount.stopMountConsole()
		iNetwork.stopRestartConsole()
		iNetwork.stopGetInterfacesConsole()

	def startRun(self):
		self["shortcuts"].setEnabled(False)
		self.expanded.clear()
		self.setStatus('update')
		self.mounts = iAutoMount.getMountsList()
		self["infotext"].setText("")
		self.vc = valid_cache(self.cache_file, self.cache_ttl)
		if self.cache_ttl > 0 and self.vc != 0:
			self.process_NetworkIPs()
		else:
			self.Timer.start(3000)

	def TimerFire(self):
		self.Timer.stop()
		self.process_NetworkIPs()

	def setWindowTitle(self):
		self.setTitle(_("Browse network neighbourhood"))

	def keyYellow(self):
		if os.path.exists(self.cache_file):
			os.remove(self.cache_file)
		self.startRun()

	def setStatus(self,status = None):
		if status:
			self.statuslist = []
			if status == 'update':
				if os.path.exists(resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/update.png")):
					statuspng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/update.png"))
				else:
					statuspng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/update.png"))
				self.statuslist.append(( ['info'], statuspng, _("Searching your network. Please wait..."), None, None, None, None ))
				self['list'].setList(self.statuslist)
				name = _("Searching your network. Please wait...")
				desc = name
			elif status == 'error':
				if os.path.exists(resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/error.png")):
					statuspng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/error.png"))
				else:
					statuspng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/error.png"))
				self.statuslist.append(( ['info'], statuspng, _("No network devices found!"), None, None, None, None ))
				self['list'].setList(self.statuslist)
				name = _("No network devices found!")
				desc = name
			else:
				name = " "
				desc = " "
			for cb in self.onChangedEntry:
				cb(name, desc)

	def makeStrIP(self):
		self.IP = iNetwork.getAdapterAttribute(self.iface, "ip")
		self.netmask = iNetwork.getAdapterAttribute(self.iface, "netmask")
		if self.IP and self.netmask and len(self.IP) == 4 and len(self.netmask) == 4 and sum(self.IP) and sum(self.netmask):
			strCIDR = str(sum((bin(x).count('1') for x in self.netmask)))
			strIP = '.'.join((str(ip & mask) for ip, mask in zip(self.IP, self.netmask))) + "/" + strCIDR
			return strIP
		return None

	def process_NetworkIPs(self):
		self.inv_cache = 0
		self.vc = valid_cache(self.cache_file, self.cache_ttl)
		if self.cache_ttl > 0 and self.vc != 0:
			print '[Networkbrowser] Loading network cache from ',self.cache_file
			try:
				self.networklist = load_cache(self.cache_file)
			except:
				self.inv_cache = 1
		if self.cache_ttl == 0 or self.inv_cache == 1 or self.vc == 0:
			# print '[Networkbrowser] Getting fresh network list'
			if fileExists("/usr/bin/nmap"):
				strIP = self.makeStrIP()
				if strIP:
					self.Console.ePopen("nmap -oX - " + strIP + ' -p 445,2049 2>/dev/null', self.nmapComplete)
				else:
					self.session.open(MessageBox, _("Your network interface %s is not properly configured, so a network scan can not be done.\nPlease configure the interface and try again.") % self.iface, type=MessageBox.TYPE_ERROR)
					self.setStatus('error')
					self["shortcuts"].setEnabled(True)
					return
			else:
				self.session.open(MessageBox, _("Nmap is not installed, so a network scan can not be done."), type=MessageBox.TYPE_ERROR)
				self.setStatus('error')
				self["shortcuts"].setEnabled(True)
				return
		else:
			if len(self.networklist) > 0:
				self.updateHostsList()
			else:
				self.setStatus('error')
			self["shortcuts"].setEnabled(True)

	def nmapComplete(self, result, retval, extra_args):
		dom = xml.dom.minidom.parseString(result)
		scan_result = []
		for dhost in dom.getElementsByTagName('host'):
			services = set()
			for port in dhost.getElementsByTagName("port"):
				for portstate in port.getElementsByTagName("state"):
					if portstate.getAttribute("state") == "open":
						if port.getAttribute("portid") == "445":
							services.add("smb")
						if port.getAttribute("portid") == "2049":
							services.add("nfs")
			if services:
				entry = ["host", "", "127.0.0.1", ",".join(services)]
				for addr in dhost.getElementsByTagName("address"):
					if addr.getAttribute("addrtype") == "ipv4":
						entry[2] = str(addr.getAttribute("addr"))
				for dhostname in dhost.getElementsByTagName("hostname"):
					hostname = dhostname.getAttributeNode("name").value
					entry[1] = str(hostname.split('.')[0])
				if not entry[1]:
					entry[1] = self.nmblookup(entry[2])
				scan_result.append(entry)

		self.networklist = scan_result
		write_cache(self.cache_file, self.networklist)
		if len(self.networklist) > 0:
			self.updateHostsList()
		else:
			self.setStatus('error')
		self["shortcuts"].setEnabled(True)

	def nmblookup(self, hostip):
		result = hostip
		cmd = ["nmblookup", "-A", hostip]
		try:
			p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
			(out, err) = p.communicate()
			for line in out.split('\n'):
				item = line.strip().split(' ')
				if "<20>" in item:
					result = item[0]
		except OSError as e:
			print '[Networkbrowser] Running %s failed with %s' % (str(cmd), str(e))
		return result

	def getNetworkShares(self, hostentry):
		hostip = hostentry[2]
		hostname = hostentry[1]
		services = hostentry[3]
		sharelist = []
		self.sharecache_file = None
		self.sharecache_file = '/etc/enigma2/' + hostip.strip() + '.cache'  # Path to cache directory
		username = ""
		password = ""
		if os.path.exists(self.sharecache_file):
			print '[Networkbrowser] Loading userinfo from ', self.sharecache_file
			try:
				self.hostdata = load_cache(self.sharecache_file)
				username = self.hostdata['username']
				password = self.hostdata['password']
			except:
				pass

		if "nfs" in services:
			cmd = ["showmount", "--no-headers", "-e", hostip]
			try:
				p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
				(out, err) = p.communicate()
				for line in out.split('\n'):
					item = line.strip().split(' ')
					if item[0]:
						sharelist.append(["nfsShare", hostname, hostip, item[0], item[0], ""])
			except OSError as e:
				print '[Networkbrowser] Running %s failed with %s' % (str(cmd), str(e))

		if "smb" in services:
			if username:
				cmd = ["/usr/bin/smbclient", "-m SMB3", "-g", "-U", "%s%%%s" % (username, password), "-L", hostip]
			else:
				cmd = ["/usr/bin/smbclient", "-m SMB3", "-g", "-N", "-L", hostip]

			try:
				p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
				(out, err) = p.communicate()
				for line in out.split('\n'):
					item = line.split('|')
					if len(item) == 3 and item[0] == "Disk" and not item[1].endswith("$"):
						sharelist.append(["smbShare", hostname, hostip, item[1], item[0], item[2]])
			except OSError as e:
				print '[Networkbrowser] Running %s failed with %s' % (str(cmd), str(e))
		return sharelist

	def updateHostsList(self):
		self.list = []
		self.network = {}
		for x in self.networklist:
			if not x[2] in self.network:
				self.network[x[2]] = []
			self.network[x[2]].append((NetworkDescriptor(name=x[1], description=x[2]), x))

		for x in self.network.keys():
			hostentry = self.network[x][0][1]
			name = hostentry[2] + " ( " + hostentry[1].strip() + " )"
			if os.path.exists(resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/host.png")):
				expandableIcon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/host.png"))
			else:
				expandableIcon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/host.png"))
			self.list.append((hostentry, expandableIcon, name, None, None, None, None, None))

		if len(self.list):
			for entry in self.list:
				entry[0][2] = "%3s.%3s.%3s.%3s" % tuple(entry[0][2].split("."))
			self.list.sort(key=lambda x: x[0][2])
			for entry in self.list:
				entry[0][2] = entry[0][2].replace(" ", "")
		self["list"].setList(self.list)
		self["list"].setIndex(self.listindex)

	def updateNetworkList(self):
		self.list = []
		self.network = {}
		self.mounts = iAutoMount.getMountsList()  # reloading mount list
		for x in self.networklist:
			if not x[2] in self.network:
				self.network[x[2]] = []
			self.network[x[2]].append((NetworkDescriptor(name=x[1], description=x[2]), x))
		self.network.keys().sort()
		for x in self.network.keys():
			hostentry = self.network[x][0][1]
			name = hostentry[2] + " ( " + hostentry[1].strip() + " )"
			if os.path.exists(resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/host.png")):
				hostIcon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/host.png"))
			else:
				hostIcon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/host.png"))
			self.list.append((hostentry, hostIcon, name, None, None, None, None, None))
			if x in self.expanded:
				for share in self.expanded[x]:
					self.list.append(self.BuildNetworkShareEntry(share))
		if len(self.list):
			for entry in self.list:
				entry[0][2] = "%3s.%3s.%3s.%3s" % tuple(entry[0][2].split("."))
			self.list.sort(key=lambda x: x[0][2])
			for entry in self.list:
				entry[0][2] = entry[0][2].replace(" ", "")
		self["list"].setList(self.list)
		self["list"].setIndex(self.listindex)

	def BuildNetworkShareEntry(self, share):
		if os.path.exists(resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/verticalLine.png")):
			verticallineIcon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/verticalLine.png"))
		else:
			verticallineIcon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/verticalLine.png"))
		sharetype = share[0]
		sharehost = share[2]

		if sharetype == 'smbShare':
			sharedir = share[3]
			sharedescription = share[5]
		else:
			sharedir = share[4]
			sharedescription = share[3]

		if sharetype == 'nfsShare':
			if os.path.exists(resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/i-nfs.png")):
				newpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/i-nfs.png"))
			else:
				newpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/i-nfs.png"))
		else:
			if os.path.exists(resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/i-smb.png")):
				newpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/i-smb.png"))
			else:
				newpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/i-smb.png"))

		self.isMounted = False
		for sharename, sharedata in self.mounts.items():
			if sharedata['ip'] == sharehost:
				if sharetype == 'nfsShare' and sharedata['mounttype'] == 'nfs':
					sharedir = sharedir.replace('/', '')
					if sharedir.endswith(sharedata['sharedir']):
						if sharedata["isMounted"] is True:
							self.isMounted = True
				if sharetype == 'smbShare' and sharedata['mounttype'] == 'cifs':
					if sharedir.endswith(sharedata['sharedir']):
						if sharedata["isMounted"] is True:
							self.isMounted = True
		if self.isMounted is True:
			if os.path.exists(resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/ok.png")):
				isMountedpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/ok.png"))
			else:
				isMountedpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/ok.png"))
		else:
			if os.path.exists(resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/cancel.png")):
				isMountedpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, "networkbrowser/cancel.png"))
			else:
				isMountedpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/cancel.png"))

		return((share, verticallineIcon, None, sharedir, sharedescription, newpng, isMountedpng, self.isMounted))

	def createSummary(self):
		from Screens.PluginBrowser import PluginBrowserSummary
		return PluginBrowserSummary

	def selectionChanged(self):
		current = self["list"].getCurrent()
		self.listindex = self["list"].getIndex()
		if current:
			if len(current[0]) >= 2:
				name = str(current[2])
				if current[0][0] in ("nfsShare", "smbShare"):
					self["infotext"].setText(_("Press OK to mount this share!"))
					name = str(current[0][2]) + ' ( ' + str(current[0][1]) + ' )'
					if current[0][0] == "nfsShare":
						desc = str(current[0][4])
					elif current[0][0] == "smbShare":
						desc = str(current[0][3])
				else:
					name = str(current[2])
					selectedhost = current[0][2]
					if selectedhost in self.expanded:
						self["infotext"].setText(_("Press OK to collapse this host"))
						desc = _("Press OK to collapse this host")
					else:
						self["infotext"].setText(_("Press OK to expand this host"))
						desc = _("Press OK to expand this host")
			else:
				name = ""
				desc = ""
		else:
			name = ""
			desc = ""
		for cb in self.onChangedEntry:
			cb(name, desc)

	def setCredentials(self):
		sel = self["list"].getCurrent()
		selectedhost = sel[0][2]
		self.session.openWithCallback(self.credentialsDone, UserDialog, self.skin_path, selectedhost.strip())

	def credentialsDone(self, ret=None):
		self.updateNetworkList()

	def go(self):
		sel = self["list"].getCurrent()
		if sel is None:
			return
		if len(sel[0]) <= 1:
			return

		selectedhost = sel[0][2]
		selectedhostname = sel[0][1]

		self.hostcache_file = '/etc/enigma2/' + selectedhost.strip() + '.cache' #Path to cache directory
		if os.path.exists(self.hostcache_file):
			try:
				self.hostdata = load_cache(self.hostcache_file)
			except Exception as e:
				print '[Networkbrowser] load cache failed:', str(e)
			self.passwordQuestion(False)
		else:
			self.session.openWithCallback(self.passwordQuestion, MessageBox, (_("Do you want to enter a username and password for this host?") ) )

	def passwordQuestion(self, ret=False):
		sel = self["list"].getCurrent()
		hostentry = sel[0]
		selectedhost = hostentry[2]
		if (ret):
			self.session.openWithCallback(self.UserDialogClosed, UserDialog, self.skin_path, selectedhost.strip())
		else:
			if hostentry[0] == 'host': # host entry selected
				if selectedhost in self.expanded:
					del self.expanded[selectedhost]
				else:
					self.expanded[selectedhost] = self.getNetworkShares(hostentry)

				self.updateNetworkList()
			elif hostentry[0] in ('nfsShare', 'smbShare'): # share entry selected
				self.openMountEdit(hostentry)

	def UserDialogClosed(self, *ret):
		if ret is not None and len(ret):
			self.go()

	def openMountEdit(self, selection):
		if selection is not None and len(selection):
			mounts = iAutoMount.getMountsList()
			newmount = True
			# Initialize blank mount entry
			data = {
				'isMounted': False,
				'active': True,
				'ip': selection[2],
				'sharename': False,
				'sharedir': False,
				'username': False,
				'password': False,
				'options': False
			}
			if selection[0] == 'nfsShare':
				# add data
				data['mounttype'] = 'nfs'
				data['sharename'] = selection[1]
				data['sharedir'] = selection[4]
				data['options'] = "rw,nolock,tcp"

				for sharename, sharedata in mounts.items():
					if sharedata['ip'] == selection[2] and sharedata['sharedir'] in selection[4]:
						data = sharedata
						newmount = False
			elif selection[0] == 'smbShare':
				# add data
				data['mounttype'] = 'cifs'
				data['sharename'] = selection[3] + "@" + selection[1]
				data['sharedir'] = selection[3]
				data['options'] = "rw,utf8,vers=2.1"
				data['username'] = ""
				data['password'] = ""
				self.sharecache_file = '/etc/enigma2/' + selection[2].strip() + '.cache'
				if os.path.exists(self.sharecache_file):
					print '[Networkbrowser] Loading userinfo from ', self.sharecache_file
					try:
						self.hostdata = load_cache(self.sharecache_file)
						data['username'] = self.hostdata['username']
						data['password'] = self.hostdata['password']
					except:
						pass
				for sharename, sharedata in mounts.items():
					if sharedata['ip'] == selection[2].strip() and sharedata['sharedir'] in selection[3].strip():
						data = sharedata
						newmount = False
			self.session.openWithCallback(self.MountEditClosed, AutoMountEdit, self.skin_path, data, newmount)

	def MountEditClosed(self, returnValue=None):
		if returnValue is None:
			self.updateNetworkList()
