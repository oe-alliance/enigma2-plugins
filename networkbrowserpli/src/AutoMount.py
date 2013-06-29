# -*- coding: utf-8 -*-
# for localized messages
from __init__ import _
import os
from enigma import eTimer
from Components.Console import Console
from Components.Harddisk import harddiskmanager #global harddiskmanager
from xml.etree.cElementTree import parse as cet_parse

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

	def getAutoMountPoints(self, callback = None):
		# Initialize mounts to empty list
		automounts = []
		self.automounts = {}
		self.activeMountsCounter = 0

		if not os.path.exists(XML_FSTAB):
			return
		tree = cet_parse(XML_FSTAB).getroot()

		def getValue(definitions, default):
			# Initialize Output
			ret = ""
			# How many definitions are present
			Len = len(definitions)
			return Len > 0 and definitions[Len-1].text or default
		# Config is stored in "mountmanager" element
		# Read out NFS Mounts
		for nfs in tree.findall("nfs"):
			for mount in nfs.findall("mount"):
				data = { 'isMounted': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, \
							'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
				try:
					data['mounttype'] = 'nfs'.encode("UTF-8")
					data['active'] = getValue(mount.findall("active"), False).encode("UTF-8")
					if data["active"] == 'True' or data["active"] == True:
						self.activeMountsCounter +=1
					data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False").encode("UTF-8")
					data['ip'] = getValue(mount.findall("ip"), "192.168.0.0").encode("UTF-8")
					data['sharedir'] = getValue(mount.findall("sharedir"), "/exports/").encode("UTF-8")
					data['sharename'] = getValue(mount.findall("sharename"), "MEDIA").encode("UTF-8")
					data['options'] = getValue(mount.findall("options"), "rw,nolock,tcp").encode("UTF-8")
					self.automounts[data['sharename']] = data
				except Exception, e:
					print "[MountManager] Error reading Mounts:", e
			# Read out CIFS Mounts
		for nfs in tree.findall("cifs"):
			for mount in nfs.findall("mount"):
				data = { 'isMounted': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, \
							'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
				try:
					data['mounttype'] = 'cifs'.encode("UTF-8")
					data['active'] = getValue(mount.findall("active"), False).encode("UTF-8")
					if data["active"] == 'True' or data["active"] == True:
						self.activeMountsCounter +=1
					data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False").encode("UTF-8")
					data['ip'] = getValue(mount.findall("ip"), "192.168.0.0").encode("UTF-8")
					data['sharedir'] = getValue(mount.findall("sharedir"), "/exports/").encode("UTF-8")
					data['sharename'] = getValue(mount.findall("sharename"), "MEDIA").encode("UTF-8")
					data['options'] = getValue(mount.findall("options"), "rw,nolock").encode("UTF-8")
					data['username'] = getValue(mount.findall("username"), "guest").encode("UTF-8")
					data['password'] = getValue(mount.findall("password"), "").encode("UTF-8")
					self.automounts[data['sharename']] = data
				except Exception, e:
					print "[MountManager] Error reading Mounts:", e

		self.checkList = self.automounts.keys()
		if not self.checkList:
			print "[AutoMount.py] self.automounts without mounts",self.automounts
			if callback is not None:
				callback(True)
		else:
			self.CheckMountPoint(self.checkList.pop(), callback)

	def sanitizeOptions(self, origOptions, cifs=False):
		options = origOptions.strip()
		if not options:
			options = 'rsize=8192,wsize=8192'
			if not cifs:
				options += ',tcp'
		else:
			if 'rsize' not in options:
				options += ',rsize=8192'
			if 'wsize' not in options:
				options += ',wsize=8192'
			if not cifs and 'tcp' not in options and 'udp' not in options:
				options += ',tcp'
		return options

	def CheckMountPoint(self, item, callback):
		data = self.automounts[item]
		if not self.MountConsole:
			self.MountConsole = Console()
		self.command = None
		path = os.path.join('/media/net', data['sharename'])
		if self.activeMountsCounter == 0:
			print "self.automounts without active mounts",self.automounts
			if data['active'] == 'False' or data['active'] is False:
				umountcmd = 'umount -fl '+ path
				print "[AutoMount.py] UMOUNT-CMD--->",umountcmd
				self.MountConsole.ePopen(umountcmd, self.CheckMountPointFinished, [data, callback])
		else:
			if data['active'] == 'False' or data['active'] is False:
				self.command = 'umount -fl '+ path

			elif data['active'] == 'True' or data['active'] is True:
			        try:
					if not os.path.exists(path):
						os.makedirs(path)
					tmpsharedir = data['sharedir'].replace(" ", "\\ ")
					if tmpsharedir[-1:] == "$":
						tmpdir = tmpsharedir.replace("$", "\\$")
						tmpsharedir = tmpdir

					if data['mounttype'] == 'nfs':
						if not os.path.ismount(path):
							if data['options']:
								options = "tcp,noatime," + data['options']
							else:
								options = "tcp,noatime"
							tmpcmd = 'mount -t nfs -o ' + options + ' ' + data['ip'] + ':/' + tmpsharedir + ' ' + path
							self.command = tmpcmd.encode("UTF-8")

					elif data['mounttype'] == 'cifs':
						if not os.path.ismount(path):
							tmpusername = data['username'].replace(" ", "\\ ")
							tmpcmd = 'mount -t cifs -o '+ data['options'] +',noatime,noserverino,iocharset=utf8,username='+ tmpusername + ',password='+ data['password'] + ' //' + data['ip'] + '/' + tmpsharedir + ' ' + path
							self.command = tmpcmd.encode("UTF-8")
				except Exception, ex:
				        print "[AutoMount.py] Failed to create", path, "Error:", ex
					self.command = None
			if self.command is not None:
				print "[AutoMount.py] U/MOUNTCMD--->",self.command
				self.MountConsole.ePopen(self.command, self.CheckMountPointFinished, [data, callback])
			else:
				self.CheckMountPointFinished(None,None, [data, callback])

	def CheckMountPointFinished(self, result, retval, extra_args):
		print "[AutoMount.py] CheckMountPointFinished",result,retval
		(data, callback ) = extra_args
		path = os.path.join('/media/net', data['sharename'])
		if os.path.exists(path):
			if os.path.ismount(path):
				if self.automounts.has_key(data['sharename']):
					self.automounts[data['sharename']]['isMounted'] = True
					desc = data['sharename']
					if self.automounts[data['sharename']]['hdd_replacement'] == 'True': #hdd replacement hack
						self.makeHDDlink(path)
					harddiskmanager.addMountedPartition(path, desc)
			else:
				if self.automounts.has_key(data['sharename']):
					self.automounts[data['sharename']]['isMounted'] = False
				if os.path.exists(path):
					if not os.path.ismount(path):
					        try:
							os.rmdir(path)
							harddiskmanager.removeMountedPartition(path)
						except Exception, ex:
						        print "Failed to remove", path, "Error:", ex
		if self.checkList:
			# Go to next item in list...
			self.CheckMountPoint(self.checkList.pop(), callback)
		if self.MountConsole:
			if len(self.MountConsole.appContainers) == 0:
				if callback is not None:
					self.callback = callback
					self.timer.startLongTimer(1)

	def makeHDDlink(self, path):
		hdd_dir = '/media/hdd'
		print "[AutoMount.py] symlink %s %s" % (path, hdd_dir)
		if os.path.islink(hdd_dir):
			if os.readlink(hdd_dir) != path:
				os.remove(hdd_dir)
				os.symlink(path, hdd_dir)
		elif os.path.ismount(hdd_dir) is False:
			if os.path.isdir(hdd_dir):
				rm_rf(hdd_dir)
		try:
			os.symlink(path, hdd_dir)
		except OSError, ex:
			print "[AutoMount.py] add symlink fails!", ex
		movie = os.path.join(hdd_dir, 'movie')
		if not os.path.exists(movie):
		        try:
				os.mkdir(movie)
			except Exception, ex:
				print "[AutoMount.py] Failed to create ", movie, "Error:", ex

	def mountTimeout(self):
		self.timer.stop()
		if self.MountConsole:
			if len(self.MountConsole.appContainers) == 0:
				print "self.automounts after mounting",self.automounts
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

	def writeMountsConfig(self):
		# Generate List in RAM
		list = ['<?xml version="1.0" ?>\n<mountmanager>\n']
		for sharename, sharedata in self.automounts.items():
			mtype = sharedata['mounttype']
			list.append('<' + mtype + '>\n')
			list.append(' <mount>\n')
			list.append("  <active>" + str(sharedata['active']) + "</active>\n")
			list.append("  <hdd_replacement>" + str(sharedata['hdd_replacement']) + "</hdd_replacement>\n")
			list.append("  <ip>" + sharedata['ip'] + "</ip>\n")
			list.append("  <sharename>" + sharedata['sharename'] + "</sharename>\n")
			list.append("  <sharedir>" + sharedata['sharedir'] + "</sharedir>\n")
			list.append("  <options>" + sharedata['options'] + "</options>\n")

			if sharedata['mounttype'] == 'cifs':
				list.append("  <username>" + sharedata['username'] + "</username>\n")
				list.append("  <password>" + sharedata['password'] + "</password>\n")

			list.append(' </mount>\n')
			list.append('</' + mtype + '>\n')

		# Close Mountmanager Tag
		list.append('</mountmanager>\n')

		# Try Saving to Flash
		try:
			open(XML_FSTAB, "w").writelines(list)
		except Exception, e:
			print "[AutoMount.py] Error Saving Mounts List:", e

	def stopMountConsole(self):
		if self.MountConsole is not None:
			self.MountConsole = None

	def removeMount(self, mountpoint, callback = None):
		print "[AutoMount.py] removing mount: ",mountpoint
		self.newautomounts = {}
		for sharename, sharedata in self.automounts.items():
			if sharename is not mountpoint.strip():
				self.newautomounts[sharename] = sharedata
		self.automounts.clear()
		self.automounts = self.newautomounts
		if not self.removeConsole:
			self.removeConsole = Console()
		path = '/media/net/'+ mountpoint
		umountcmd = 'umount -fl '+ path
		print "[AutoMount.py] UMOUNT-CMD--->",umountcmd
		self.removeConsole.ePopen(umountcmd, self.removeMountPointFinished, [path, callback])

	def removeMountPointFinished(self, result, retval, extra_args):
		print "[AutoMount.py] removeMountPointFinished result", result, "retval", retval
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
