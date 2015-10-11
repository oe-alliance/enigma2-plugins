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

		self.getAutoMountPoints()

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

		def getValue(definitions, default):
			# Initialize Output
			ret = ""
			# How many definitions are present
			Len = len(definitions)
			return Len > 0 and definitions[Len-1].text or default
		mountusing = 0 # 0=old_enigma2, 1 =fstab, 2=enigma2
		# Config is stored in "mountmanager" element
		# Read out NFS Mounts
		for autofs in tree.findall("autofs"):
			mountusing = 1
			for nfs in autofs.findall("nfs"):
				for mount in nfs.findall("mount"):
					data = { 'isMounted': False, 'mountusing': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, 'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
					try:
						data['mountusing'] = 'autofs'.encode("UTF-8")
						data['mounttype'] = 'nfs'.encode("UTF-8")
						data['active'] = getValue(mount.findall("active"), False).encode("UTF-8")
						if data["active"] == 'True' or data["active"] == True:
							self.activeMountsCounter +=1
						data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False").encode("UTF-8")
						data['ip'] = getValue(mount.findall("ip"), "192.168.0.0").encode("UTF-8")
						data['sharedir'] = getValue(mount.findall("sharedir"), "/media/hdd/").encode("UTF-8")
						data['sharename'] = getValue(mount.findall("sharename"), "MEDIA").encode("UTF-8")
						data['options'] = getValue(mount.findall("options"), "rw,nolock,tcp,utf8").encode("UTF-8")
						self.automounts[data['sharename']] = data
					except Exception, e:
						print "[MountManager] Error reading Mounts:", e
			for cifs in autofs.findall("cifs"):
				for mount in cifs.findall("mount"):
					data = { 'isMounted': False, 'mountusing': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, 'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
					try:
						data['mountusing'] = 'autofs'.encode("UTF-8")
						data['mounttype'] = 'cifs'.encode("UTF-8")
						data['active'] = getValue(mount.findall("active"), False).encode("UTF-8")
						if data["active"] == 'True' or data["active"] == True:
							self.activeMountsCounter +=1
						data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False").encode("UTF-8")
						data['ip'] = getValue(mount.findall("ip"), "192.168.0.0").encode("UTF-8")
						data['sharedir'] = getValue(mount.findall("sharedir"), "/media/hdd/").encode("UTF-8")
						data['sharename'] = getValue(mount.findall("sharename"), "MEDIA").encode("UTF-8")
						data['options'] = getValue(mount.findall("options"), "rw,utf8").encode("UTF-8")
						data['username'] = getValue(mount.findall("username"), "guest").encode("UTF-8")
						data['password'] = getValue(mount.findall("password"), "").encode("UTF-8")
						self.automounts[data['sharename']] = data
					except Exception, e:
						print "[MountManager] Error reading Mounts:", e

		for fstab in tree.findall("fstab"):
			mountusing = 2
			for nfs in fstab.findall("nfs"):
				for mount in nfs.findall("mount"):
					data = { 'isMounted': False, 'mountusing': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, 'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
					try:
						data['mountusing'] = 'fstab'.encode("UTF-8")
						data['mounttype'] = 'nfs'.encode("UTF-8")
						data['active'] = getValue(mount.findall("active"), False).encode("UTF-8")
						if data["active"] == 'True' or data["active"] == True:
							self.activeMountsCounter +=1
						data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False").encode("UTF-8")
						data['ip'] = getValue(mount.findall("ip"), "192.168.0.0").encode("UTF-8")
						data['sharedir'] = getValue(mount.findall("sharedir"), "/media/hdd/").encode("UTF-8")
						data['sharename'] = getValue(mount.findall("sharename"), "MEDIA").encode("UTF-8")
						data['options'] = getValue(mount.findall("options"), "rw,nolock,tcp,utf8").encode("UTF-8")
						self.automounts[data['sharename']] = data
					except Exception, e:
						print "[MountManager] Error reading Mounts:", e
			for cifs in fstab.findall("cifs"):
				for mount in cifs.findall("mount"):
					data = { 'isMounted': False, 'mountusing': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, 'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
					try:
						data['mountusing'] = 'fstab'.encode("UTF-8")
						data['mounttype'] = 'cifs'.encode("UTF-8")
						data['active'] = getValue(mount.findall("active"), False).encode("UTF-8")
						if data["active"] == 'True' or data["active"] == True:
							self.activeMountsCounter +=1
						data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False").encode("UTF-8")
						data['ip'] = getValue(mount.findall("ip"), "192.168.0.0").encode("UTF-8")
						data['sharedir'] = getValue(mount.findall("sharedir"), "/media/hdd/").encode("UTF-8")
						data['sharename'] = getValue(mount.findall("sharename"), "MEDIA").encode("UTF-8")
						data['options'] = getValue(mount.findall("options"), "rw,utf8").encode("UTF-8")
						data['username'] = getValue(mount.findall("username"), "guest").encode("UTF-8")
						data['password'] = getValue(mount.findall("password"), "").encode("UTF-8")
						self.automounts[data['sharename']] = data
					except Exception, e:
						print "[MountManager] Error reading Mounts:", e

		for enigma2 in tree.findall("enigma2"):
			mountusing = 3
			for nfs in enigma2.findall("nfs"):
				for mount in nfs.findall("mount"):
					data = { 'isMounted': False, 'mountusing': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, 'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
					try:
						data['mountusing'] = 'enigma2'.encode("UTF-8")
						data['mounttype'] = 'nfs'.encode("UTF-8")
						data['active'] = getValue(mount.findall("active"), False).encode("UTF-8")
						if data["active"] == 'True' or data["active"] == True:
							self.activeMountsCounter +=1
						data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False").encode("UTF-8")
						data['ip'] = getValue(mount.findall("ip"), "192.168.0.0").encode("UTF-8")
						data['sharedir'] = getValue(mount.findall("sharedir"), "/exports/").encode("UTF-8")
						data['sharename'] = getValue(mount.findall("sharename"), "MEDIA").encode("UTF-8")
						data['options'] = getValue(mount.findall("options"), "rw,nolock,tcp,utf8").encode("UTF-8")
						self.automounts[data['sharename']] = data
					except Exception, e:
						print "[MountManager] Error reading Mounts:", e
				# Read out CIFS Mounts
			for cifs in enigma2.findall("cifs"):
				for mount in cifs.findall("mount"):
					data = { 'isMounted': False, 'mountusing': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, 'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
					try:
						data['mountusing'] = 'enigma2'.encode("UTF-8")
						data['mounttype'] = 'cifs'.encode("UTF-8")
						data['active'] = getValue(mount.findall("active"), False).encode("UTF-8")
						if data["active"] == 'True' or data["active"] == True:
							self.activeMountsCounter +=1
						data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False").encode("UTF-8")
						data['ip'] = getValue(mount.findall("ip"), "192.168.0.0").encode("UTF-8")
						data['sharedir'] = getValue(mount.findall("sharedir"), "/exports/").encode("UTF-8")
						data['sharename'] = getValue(mount.findall("sharename"), "MEDIA").encode("UTF-8")
						data['options'] = getValue(mount.findall("options"), "rw,utf8").encode("UTF-8")
						data['username'] = getValue(mount.findall("username"), "guest").encode("UTF-8")
						data['password'] = getValue(mount.findall("password"), "").encode("UTF-8")
						self.automounts[data['sharename']] = data
					except Exception, e:
						print "[MountManager] Error reading Mounts:", e

		if mountusing == 0:
			for nfs in tree.findall("nfs"):
				for mount in nfs.findall("mount"):
					data = { 'isMounted': False, 'mountusing': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, 'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
					try:
						data['mountusing'] = 'old_enigma2'.encode("UTF-8")
						data['mounttype'] = 'nfs'.encode("UTF-8")
						data['active'] = getValue(mount.findall("active"), False).encode("UTF-8")
						if data["active"] == 'True' or data["active"] == True:
							self.activeMountsCounter +=1
						data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False").encode("UTF-8")
						data['ip'] = getValue(mount.findall("ip"), "192.168.0.0").encode("UTF-8")
						data['sharedir'] = getValue(mount.findall("sharedir"), "/exports/").encode("UTF-8")
						data['sharename'] = getValue(mount.findall("sharename"), "MEDIA").encode("UTF-8")
						data['options'] = getValue(mount.findall("options"), "rw,nolock,tcp,utf8").encode("UTF-8")
						self.automounts[data['sharename']] = data
					except Exception, e:
						print "[MountManager] Error reading Mounts:", e
			for cifs in tree.findall("cifs"):
				for mount in cifs.findall("mount"):
					data = { 'isMounted': False, 'mountusing': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, 'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
					try:
						data['mountusing'] = 'old_enigma2'.encode("UTF-8")
						data['mounttype'] = 'cifs'.encode("UTF-8")
						data['active'] = getValue(mount.findall("active"), False).encode("UTF-8")
						if data["active"] == 'True' or data["active"] == True:
							self.activeMountsCounter +=1
						data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False").encode("UTF-8")
						data['ip'] = getValue(mount.findall("ip"), "192.168.0.0").encode("UTF-8")
						data['sharedir'] = getValue(mount.findall("sharedir"), "/exports/").encode("UTF-8")
						data['sharename'] = getValue(mount.findall("sharename"), "MEDIA").encode("UTF-8")
						data['options'] = getValue(mount.findall("options"), "rw,utf8").encode("UTF-8")
						data['username'] = getValue(mount.findall("username"), "guest").encode("UTF-8")
						data['password'] = getValue(mount.findall("password"), "").encode("UTF-8")
						self.automounts[data['sharename']] = data
					except Exception, e:
						print "[MountManager] Error reading Mounts:", e

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
		return options

	def CheckMountPoint(self, item, callback, restart):
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
			unmountcommand.append("/etc/init.d/autofs stop")
		if os.path.ismount(path) and 'autofs' not in path:
			unmountcommand.append('umount -fl '+ path)
		if self.activeMountsCounter != 0:
			if data['active'] == 'True' or data['active'] is True:
				if data['mountusing'] == 'autofs' and restart:
					mountcommand = "/etc/init.d/autofs start"
				elif data['mountusing'] == 'fstab':
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
						if not os.path.ismount(path):
							tmpcmd = 'mount -t nfs -o ' + self.sanitizeOptions(data['options']) + ' ' + data['ip'] + ':/' + tmpsharedir + ' ' + path
							mountcommand = tmpcmd.encode("UTF-8")
					elif data['mounttype'] == 'cifs':
						if not os.path.ismount(path):
							tmpusername = data['username'].replace(" ", "\\ ")
							tmpcmd = 'mount -t cifs -o ' + self.sanitizeOptions(data['options'], cifs=True) +',noatime,noserverino,username='+ tmpusername + ',password='+ data['password'] + ' //' + data['ip'] + '/' + tmpsharedir + ' ' + path
							mountcommand = tmpcmd.encode("UTF-8")

		if len(unmountcommand) > 0 or mountcommand is not None:
			if len(unmountcommand) > 0:
				for x in unmountcommand:
					command.append(x)
			if not os.path.exists(path) and data['mountusing'] != 'autofs':
				command.append('mkdir -p ' + path)
			if command is not None:
				command.append('sleep 2')
			if mountcommand is not None:
				command.append(mountcommand)
			print 'command',command
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
			self.CheckMountPoint(self.checkList.pop(), callback, restart)
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
		
	def generateMountXML(self, sharedata):
		res = []
		mounttype = sharedata['mounttype']
		mountusing = sharedata['mountusing']
		if mountusing != 'old_enigma2':
			res.append('<' + mountusing + '>\n')
		res.append(' <' + mounttype + '>\n')
		res.append('  <mount>\n')
		res.append('   <active>' + str(sharedata['active']) + '</active>\n')
		res.append('   <hdd_replacement>' + str(sharedata['hdd_replacement']) + '</hdd_replacement>\n')
		res.append('   <ip>' + sharedata['ip'] + '</ip>\n')
		res.append('   <sharename>' + sharedata['sharename'] + '</sharename>\n')
		res.append('   <sharedir>' + sharedata['sharedir'] + '</sharedir>\n')
		res.append('   <options>' + sharedata['options'] + '</options>\n')
		if mounttype == 'cifs':
			res.append("   <username>" + sharedata['username'] + "</username>\n")
			res.append("   <password>" + sharedata['password'] + "</password>\n")
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
				self.removeEntryFromFile(sharetemp+'\n', '/etc/auto.network', ' ')
				self.removeEntryFromFile(sharetemp, '/etc/fstab')
			elif mounttype == 'cifs':
				sharetemp = '//' + sharedata['ip'] + '/' + sharedata['sharedir']
				self.removeEntryFromFile(":" + sharetemp+'\n', '/etc/auto.network', ' ')
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
				self.removeEntryFromFile(sharetemp+'\n', '/etc/auto.network' , ' ')
				self.removeEntryFromFile(sharetemp, '/etc/fstab')
		self.automounts.clear()
		self.automounts = self.newautomounts
		if not self.removeConsole:
			self.removeConsole = Console()
		command = []
		autofsstop = None
		if sharedata['mountusing'] == 'autofs':
			command.append("/etc/init.d/autofs stop")
			command.append("sleep 2")
			command.append("/etc/init.d/autofs start")
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
