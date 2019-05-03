# -*- coding: utf-8 -*-
# for localized messages
#from __init__ import _
import os

from enigma import eTimer
from Components.Console import Console
from Components.Harddisk import harddiskmanager #global harddiskmanager
from xml.etree.cElementTree import parse as cet_parse
from shutil import rmtree

XML_FSTAB = "/etc/enigma2/automounts.xml"

def rm_rf(d): # only for removing the ipkg stuff from /media/hdd subdirs
	try:
		for path in (os.path.join(d,f) for f in os.listdir(d)):
			if os.path.isdir(path):
				rm_rf(path)
			else:
				os.unlink(path)
		os.rmdir(d)
	except Exception, ex:
		print "AutoMount failed to remove", d, "Error:", ex

class AutoMount():
	"""Manages Mounts declared in a XML-Document."""
	def __init__(self):
		self.automounts = {}
		self.restartConsole = Console()
		self.MountConsole = Console()
		self.removeConsole = Console()
		self.activeMountsCounter = 0
		# Initialize Timer
		self.callback = None
		self.timer = eTimer()
		self.timer.callback.append(self.mountTimeout)
		self.autofsreload = None

		self.getAutoMountPoints()

	def makeAutoMountPoint(self, mountusing, mounttype, mount):

		def getValue(definitions, default):
			# Return last definition or default if none
			return definitions and definitions[-1].text or default

		try:
			default_options = {
				"nfs": "rw,nolock,tcp",
				"cifs": "rw,utf8,vers=2.1",
			}[mounttype]
			default_sharedir = "/media/hdd/"
			if mounttype == 'cifs':
				username = getValue(mount.findall("username"), "guest").encode("UTF-8")
				password = getValue(mount.findall("password"), "").encode("UTF-8")
			else:
				username = False
				password = False
			data = {
				'isMounted': False,
				'mountusing': mountusing.encode("UTF-8"),
				'mounttype': mounttype.encode("UTF-8"),
				'active': getValue(mount.findall("active"), "False").encode("UTF-8"),
				'hdd_replacement': getValue(mount.findall("hdd_replacement"), "False").encode("UTF-8"),
				'ip': getValue(mount.findall("ip"), "192.168.0.0").encode("UTF-8"),
				'sharedir': getValue(mount.findall("sharedir"), default_sharedir).encode("UTF-8"),
				'sharename': getValue(mount.findall("sharename"), "MEDIA").encode("UTF-8"),
				'options': getValue(mount.findall("options"), default_options).encode("UTF-8"),
				'username': username,
				'password': password,
			}
		except Exception, e:
			print "[MountManager] Error reading Mounts:", e
		else:
			self.automounts[data['sharename']] = data

			if data["active"] == 'True' or data["active"] == True:
				self.activeMountsCounter += 1


	def getAutoMountPoints(self, callback = None, restart=False):
		# Initialize mounts to empty list
		automounts = []
		self.automounts = {}
		self.activeMountsCounter = 0
		if not os.path.exists(XML_FSTAB):
			return
		file = open(XML_FSTAB, 'r')
		tree = cet_parse(file).getroot()
		file.close()

		# Config is stored in "mountmanager" element
		for mountusing in ("autofs", "fstab", "enigma2"):
			for mountusingnode in tree.findall(mountusing):
				for mounttype in ("nfs", "cifs"):
					for fs in mountusingnode.findall(mounttype):
						for mount in fs.findall("mount"):
							self.makeAutoMountPoint(mountusing, mounttype, mount)

		for mounttype in ("nfs", "cifs"):
			for fs in tree.findall(mounttype):
				for mount in fs.findall("mount"):
					self.makeAutoMountPoint("old_enigma2", mounttype, mount)

		self.checkList = self.automounts.keys()
		if not self.checkList:
			# print "[NetworkBrowser] self.automounts without mounts",self.automounts
			if callback is not None:
				callback(True)
		else:
			self.CheckMountPoint(self.checkList.pop(), callback, restart)

	def sanitizeOptions(self, origOptions, cifs=False, fstab=False, autofs=False):
		options = origOptions.strip()
		options = options.replace('utf8','iocharset=utf8')
		if fstab:
			if not options:
				options = 'rw'
				if not cifs:
					options += ',nfsvers=3,rsize=8192,wsize=8192,proto=tcp'
			else:
				if not cifs:
					options += ',nfsvers=3'
					if 'rsize' not in options:
						options += ',rsize=8192'
					if 'wsize' not in options:
						options += ',wsize=8192'
					if 'tcp' not in options and 'udp' not in options:
						options += ',proto=tcp'
					options = options + ',timeo=14,soft'
		elif autofs:
			if not options:
				options = 'rw'
				if not cifs:
					options += ',nfsvers=3,rsize=8192,wsize=8192'
			else:
				if not cifs:
					options += ',nfsvers=3'
					if 'rsize' not in options:
						options += ',rsize=8192'
					if 'wsize' not in options:
						options += ',wsize=8192'
					if 'tcp' not in options and 'udp' not in options:
						options += ',proto=tcp'
					options = options + ',timeo=14,soft'
		else:
			if not options:
				options = 'rw,rsize=8192,wsize=8192'
				if not cifs:
					options += ',proto=tcp'
			else:
				if not cifs:
					if 'rsize' not in options:
						options += ',rsize=8192'
					if 'wsize' not in options:
						options += ',wsize=8192'
					if 'tcp' not in options and 'udp' not in options:
						options += ',proto=tcp'
		if cifs:
			options += ",cache=loose"
		return options

	def CheckMountPoint(self, item, callback, restart):
		self.autofsreload = None
		self.doCheckMountPoint(item, callback, restart)

	def doCheckMountPoint(self, item, callback, restart):
		data = self.automounts[item]
		if not self.MountConsole:
			self.MountConsole = Console()
		command = []
		mountcommand = None
		unmountcommand = []
		if data['mountusing'] == 'autofs':
			path = os.path.join('/media/autofs', data['sharename'])
		elif data['hdd_replacement'] == 'True' or data['hdd_replacement'] is True:
			path = os.path.join('/media/hdd')
		else:
			path = os.path.join('/media/net', data['sharename'])
		if data['mountusing'] == 'autofs' and restart:
			self.autofsreload = "/etc/init.d/autofs reload"
		if os.path.ismount(path) and 'autofs' not in path:
			unmountcommand.append('umount -fl '+ path)
		if self.activeMountsCounter != 0:
			if data['active'] == 'True' or data['active'] is True:
				if data['mountusing'] == 'fstab':
					if data['mounttype'] == 'nfs':
						tmpcmd = 'mount ' + data['ip'] + ':/' + data['sharedir']
					elif data['mounttype'] == 'cifs':
						tmpcmd = 'mount //' + data['ip'] + '/' + data['sharedir']
					mountcommand = tmpcmd.encode("UTF-8")
				elif data['mountusing'] == 'enigma2' or data['mountusing'] == 'old_enigma2':
					tmpsharedir = data['sharedir'].replace(" ", "\\ ")
					if tmpsharedir[-1:] == "$":
						tmpdir = tmpsharedir.replace("$", "\\$")
						tmpsharedir = tmpdir
					if data['mounttype'] == 'nfs':
						tmpcmd = 'mount -t nfs -o ' + self.sanitizeOptions(data['options']) + ' ' + data['ip'] + ':/' + tmpsharedir + ' ' + path
						mountcommand = tmpcmd.encode("UTF-8")
					elif data['mounttype'] == 'cifs':
						tmpusername = data['username'].replace(" ", "\\ ")
						tmpcmd = 'mount -t cifs -o ' + self.sanitizeOptions(data['options'], cifs=True) +',noatime,noserverino,username='+ tmpusername + ',password='+ data['password'] + ' //' + data['ip'] + '/' + tmpsharedir + ' ' + path
						mountcommand = tmpcmd.encode("UTF-8")

		for x in unmountcommand:
			command.append(x)
		if not os.path.exists(path) and data['mountusing'] != 'autofs':
			command.append('mkdir -p ' + path)
		if mountcommand:
			if command:
				command.append('sleep 2')
			command.append(mountcommand)
		if not self.checkList and self.autofsreload is not None:
			if command:
				command.append('sleep 2')
			command.append(self.autofsreload)
			self.autofsreload = None
		print 'command',command
		if command:
			self.MountConsole.eBatch(command, self.CheckMountPointFinished, [data, callback, restart], debug=True)
		else:
			self.CheckMountPointFinished([data, callback, restart])

	def CheckMountPointFinished(self, extra_args):
# 		print "[NetworkBrowser] CheckMountPointFinished"
		(data, callback, restart) = extra_args
		hdd_dir = '/media/hdd'
		sharepath = os.path.join('/media/net', data['sharename'])
		if data['mountusing'] == 'autofs':
			sharepath = os.path.join('/media/autofs', data['sharename'])
			path = os.path.join('/media/autofs', data['sharename'])
		elif data['hdd_replacement'] == 'True' or data['hdd_replacement'] is True:
			path = os.path.join('/media/hdd')
		else:
			path = os.path.join('/media/net', data['sharename'])

		if os.path.exists(path):
			if data['mountusing'] == 'autofs':
				if self.automounts.has_key(data['sharename']):
					self.automounts[data['sharename']]['isMounted'] = True
					desc = data['sharename']
					harddiskmanager.addMountedPartition(sharepath, desc)
				if data['hdd_replacement'] == 'True' or data['hdd_replacement'] is True:
					if os.path.islink(hdd_dir):
						if os.readlink(hdd_dir) != path:
							os.unlink(hdd_dir)
							os.symlink(path, hdd_dir)
					elif not os.path.exists(hdd_dir):
						os.symlink(path, hdd_dir)
			elif os.path.ismount(path):
				if self.automounts.has_key(data['sharename']):
					self.automounts[data['sharename']]['isMounted'] = True
					desc = data['sharename']
					harddiskmanager.addMountedPartition(path, desc)
			else:
				if self.automounts.has_key(data['sharename']):
					self.automounts[data['sharename']]['isMounted'] = False
				if os.path.exists(path):
					if not os.path.ismount(path):
						try:
							rmtree(path)
							harddiskmanager.removeMountedPartition(path)
						except Exception, ex:
							print "Failed to remove", path, "Error:", ex
		if self.checkList:
			# Go to next item in list...
			self.doCheckMountPoint(self.checkList.pop(), callback, restart)
		if self.MountConsole:
			if len(self.MountConsole.appContainers) == 0:
				if callback is not None:
					self.callback = callback
					self.timer.startLongTimer(1)

	def mountTimeout(self):
		self.timer.stop()
		if self.MountConsole:
			if len(self.MountConsole.appContainers) == 0:
				if self.callback is not None:
					self.callback(True)
		elif self.removeConsole:
			if len(self.removeConsole.appContainers) == 0:
				if self.callback is not None:
					self.callback(True)

	def getMountsList(self):
		return self.automounts

	def getMountsAttribute(self, mountpoint, attribute):
		if self.automounts.has_key(mountpoint):
			if self.automounts[mountpoint].has_key(attribute):
				return self.automounts[mountpoint][attribute]
		return None

	def setMountsAttribute(self, mountpoint, attribute, value):
		if self.automounts.has_key(mountpoint):
			self.automounts[mountpoint][attribute] = value

	def removeEntryFromFile(self, entry, filename, separator=None):
		if os.path.exists(filename):
			f = open(filename)
			tmpfile = open(filename + '.tmp', 'w')
			tmpfile.writelines([line for line in f.readlines() if entry not in line.split(separator)])
			tmpfile.close()
			f.close()
			os.rename(filename + '.tmp', filename)

	def escape(self, data):
		return data.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

	def removeEntryFromAutofsMap(self, key, location, filename):
		if os.path.exists(filename):
			f = open(filename)
			tmpfile = open(filename + '.tmp', 'w')
			for line in f.readlines():
				parts = line.split(" ", 2)
				if len(parts) > 1:
					if parts[1].startswith("-") and len(parts) > 2:
						parts = parts[:1] + parts[2:]
					if parts[0] != key and parts[1] != location:
						tmpfile.write(line)
			tmpfile.close()
			f.close()
			os.rename(filename + '.tmp', filename)

	def generateMountXML(self, sharedata):
		res = []
		mounttype = self.escape(sharedata['mounttype'])
		mountusing = self.escape(sharedata['mountusing'])
		if mountusing != 'old_enigma2':
			res.append('<' + mountusing + '>\n')
		res.append(' <' + mounttype + '>\n')
		res.append('  <mount>\n')
		res.append('   <active>' + self.escape(str(sharedata['active'])) + '</active>\n')
		res.append('   <hdd_replacement>' + self.escape(str(sharedata['hdd_replacement'])) + '</hdd_replacement>\n')
		res.append('   <ip>' + self.escape(sharedata['ip']) + '</ip>\n')
		res.append('   <sharename>' + self.escape(sharedata['sharename']) + '</sharename>\n')
		res.append('   <sharedir>' + self.escape(sharedata['sharedir']) + '</sharedir>\n')
		res.append('   <options>' + self.escape(sharedata['options']) + '</options>\n')
		if mounttype == 'cifs':
			res.append("   <username>" + self.escape(sharedata['username']) + "</username>\n")
			res.append("   <password>" + self.escape(sharedata['password']) + "</password>\n")
		res.append('  </mount>\n')
		res.append(' </' + mounttype + '>\n')
		if mountusing != 'old_enigma2':
			res.append('</' + mountusing + '>\n')
		return res


	def writeMountsConfig(self):
		# Generate List in RAM
		list = ['<?xml version="1.0" ?>\n<mountmanager>\n']
		for sharename, sharedata in self.automounts.items():
			mounttype = sharedata['mounttype']
			mountusing = sharedata['mountusing']

			if sharedata['hdd_replacement'] == 'True' or sharedata['hdd_replacement'] is True: #hdd replacement hack
				path = os.path.join('/media/hdd')
				sharepath = os.path.join('/media/net', sharedata['sharename'])
			else:
				path = os.path.join('/media/net', sharedata['sharename'])
				sharepath = ""

			sharetemp = None
			if mounttype == 'nfs':
				sharetemp = sharedata['ip'] + ':/' + sharedata['sharedir']
				self.removeEntryFromAutofsMap(sharedata['sharename'], sharetemp + '\n', '/etc/auto.network')
				self.removeEntryFromFile(sharetemp, '/etc/fstab')
			elif mounttype == 'cifs':
				sharetemp = '//' + sharedata['ip'] + '/' + sharedata['sharedir']
				self.removeEntryFromAutofsMap(sharedata['sharename'], ":" + sharetemp+'\n', '/etc/auto.network')
				self.removeEntryFromFile(sharetemp, '/etc/fstab')

			list += self.generateMountXML(sharedata)
			if mountusing == 'autofs':
				if sharedata['active'] == True or sharedata['active'] == 'True':
					out = open('/etc/auto.network', 'a')
					if mounttype == 'nfs':
						line = sharedata['sharename'] + ' -fstype=' + mounttype + ',' + self.sanitizeOptions(sharedata['options'], autofs=True) + ' ' + sharedata['ip'] + ':/' + sharedata['sharedir'] + '\n'
					elif sharedata['mounttype'] == 'cifs':
						tmpusername = sharedata['username'].replace(" ", "\ ")
						tmppassword = sharedata['password'].replace(" ", "\ ")
						tmpaddress = sharedata['ip']
						line = sharedata['sharename'] + ' -fstype=' + mounttype + ',user=' + tmpusername + ',pass=' + tmppassword +','+ self.sanitizeOptions(sharedata['options'], cifs=True, autofs=True) + ' ://' + tmpaddress + '/' + sharedata['sharedir'] + '\n'
					out.write(line)
					out.close()
			elif mountusing == 'fstab':
				if sharedata['active'] == True or sharedata['active'] == 'True':
					out = open('/etc/fstab', 'a')
					if sharedata['mounttype'] == 'nfs':
						line = sharedata['ip'] + ':/' + sharedata['sharedir'] + '\t' + path + '\tnfs\t_netdev,' + self.sanitizeOptions(sharedata['options'], fstab=True) + '\t0 0\n'
					elif sharedata['mounttype'] == 'cifs':
						line = '//' + sharedata['ip'] + '/' + sharedata['sharedir'] + '\t' + path + '\tcifs\tuser=' + sharedata['username'] + ',pass=' + sharedata['password'] + ',_netdev,' + self.sanitizeOptions(sharedata['options'], cifs=True, fstab=True) + '\t0 0\n'
					out.write(line)
					out.close()

		# Close Mountmanager Tag
		list.append('</mountmanager>\n')

		# Try Saving to Flash
		try:
			f = open(XML_FSTAB, "w")
			f.writelines(list)
			f.close()
			# print "[NetworkBrowser] Saving Mounts List:"
		except Exception, e:
			print "[NetworkBrowser] Error Saving Mounts List:", e

	def stopMountConsole(self):
		if self.MountConsole is not None:
			self.MountConsole = None

	def removeMount(self, mountpoint, callback = None):
# 		print "[NetworkBrowser] removing mount: ",mountpoint
		self.newautomounts = {}
		for sharename, sharedata in self.automounts.items():
			sharepath = os.path.join('/media/net', sharedata['sharename'])
			if sharedata['mountusing'] == 'autofs':
				sharepath = os.path.join('/media/autofs', sharedata['sharename'])
				path = os.path.join('/media/autofs', sharedata['sharename'])
				if sharedata['hdd_replacement'] == 'True' or sharedata['hdd_replacement'] is True:
					if os.path.islink('/media/hdd'):
						if os.readlink('/media/hdd') == path:
							os.unlink('/media/hdd')
			elif sharedata['hdd_replacement'] == 'True' or sharedata['hdd_replacement'] is True:
				path = os.path.join('/media/hdd')
			else:
				path = os.path.join('/media/net', sharedata['sharename'])
			if sharename is not mountpoint.strip():
				self.newautomounts[sharename] = sharedata
			if sharedata['mounttype'] == 'nfs':
				sharetemp = sharedata['ip'] + ':/' + sharedata['sharedir']
			elif sharedata['mounttype'] == 'cifs':
				sharetemp = '://' + sharedata['ip'] + '/' + sharedata['sharedir']
			if sharetemp:
				self.removeEntryFromAutofsMap(sharedata['sharename'], sharetemp + '\n', '/etc/auto.network')
				self.removeEntryFromFile(sharetemp, '/etc/fstab')
		self.automounts.clear()
		self.automounts = self.newautomounts
		if not self.removeConsole:
			self.removeConsole = Console()
		command = []
		autofsstop = None
		if sharedata['mountusing'] == 'autofs':
			# With a short sleep to allow time for the reload
			command.append("/etc/init.d/autofs reload; sleep 2")
		else:
			command.append('umount -fl '+ path)
# 		print "[NetworkBrowser] UMOUNT-CMD--->",umountcmd
		self.removeConsole.eBatch(command, self.removeMountPointFinished, [path, callback], debug=True)

	def removeMountPointFinished(self, extra_args):
		(path, callback ) = extra_args
		if os.path.exists(path):
			if not os.path.ismount(path):
				try:
					os.rmdir(path)
					harddiskmanager.removeMountedPartition(path)
				except Exception, ex:
					print "Failed to remove", path, "Error:", ex
		if self.removeConsole:
			if len(self.removeConsole.appContainers) == 0:
				if callback is not None:
					self.callback = callback
					self.timer.startLongTimer(1)

iAutoMount = AutoMount()
