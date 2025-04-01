# -*- coding: utf-8 -*-
# for localized messages
from __future__ import print_function
from __future__ import absolute_import
from .__init__ import _
import os
import subprocess
import shlex
from enigma import eTimer
from Components.Console import Console
from Components.Harddisk import harddiskmanager  # global harddiskmanager
from xml.etree.cElementTree import parse as cet_parse
import six

XML_FSTAB = "/etc/enigma2/automounts.xml"


def rm_rf(d):  # only for removing the ipkg stuff from /media/hdd subdirs
	try:
		for path in (os.path.join(d, f) for f in os.listdir(d)):
			if os.path.isdir(path):
				rm_rf(path)
			else:
				os.unlink(path)
		os.rmdir(d)
	except Exception as ex:
		print("AutoMount failed to remove", d, "Error:", ex)


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

	def getAutoMountPoints(self, callback=None):
		# Initialize mounts to empty list
		automounts = []
		self.automounts = {}
		self.activeMountsCounter = 0

		if not os.path.exists(XML_FSTAB):
			return
		tree = cet_parse(XML_FSTAB).getroot()

		def enc(val):
			if six.PY2:
				return val.encode("UTF-8")
			return val

		def getValue(definitions, default):
			# Initialize Output
			ret = ""
			# How many definitions are present
			Len = len(definitions)
			if six.PY2:
				return Len > 0 and definitions[Len - 1].text.encode("UTF-8") or default.encode("UTF-8")
			else:
				return Len > 0 and definitions[Len - 1].text or default

		# Config is stored in "mountmanager" element
		# Read out NFS Mounts
		for nfs in tree.findall("nfs"):
			for mount in nfs.findall("mount"):
				data = {'isMounted': False, 'active': False, 'ip': False, 'host': False, 'sharename': False, 'sharedir': False, 'username': False,
							'password': False, 'mounttype': False, 'options': False, 'hdd_replacement': False}
				try:
					data['mounttype'] = enc('nfs')
					data['active'] = getValue(mount.findall("active"), False)
					if data["active"] == 'True' or data["active"] is True:
						self.activeMountsCounter += 1
					data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False")
					data['ip'] = getValue(mount.findall("ip"), "192.168.0.0")
					data['host'] = getValue(mount.findall("host"), "")
					data['sharedir'] = getValue(mount.findall("sharedir"), "/exports/")
					data['sharename'] = getValue(mount.findall("sharename"), "MEDIA")
					data['options'] = getValue(mount.findall("options"), "rw,nolock,tcp,utf8")
					self.automounts[data['sharename']] = data
				except Exception as e:
					print("[MountManager] Error reading Mounts:", e)

		# Read out CIFS Mounts
		for nfs in tree.findall("cifs"):
			for mount in nfs.findall("mount"):
				data = {'isMounted': False, 'active': False, 'ip': False, 'host': False, 'sharename': False, 'sharedir': False, 'username': False,
							'password': False, 'mounttype': False, 'options': False, 'hdd_replacement': False}
				try:
					data['mounttype'] = enc('cifs')
					data['active'] = getValue(mount.findall("active"), False)
					if data["active"] == 'True' or data["active"] is True:
						self.activeMountsCounter += 1
					data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), 'False')
					data['ip'] = getValue(mount.findall("ip"), '')
					data['host'] = getValue(mount.findall("host"), '')
					data['sharedir'] = getValue(mount.findall("sharedir"), '/media/')
					data['sharename'] = getValue(mount.findall("sharename"), 'MEDIA')
					data['options'] = getValue(mount.findall("options"), "")
					data['username'] = getValue(mount.findall("username"), 'guest')
					data['password'] = getValue(mount.findall("password"), 'guest')
					self.automounts[data['sharename']] = data
				except Exception as e:
					print("[MountManager] Error reading Mounts:", e)

		self.checkList = list(self.automounts.keys())
		if not self.checkList:
			print("[AutoMount.py] self.automounts without mounts", self.automounts)
			if callback is not None:
				callback(True)
		else:
			self.CheckMountPoint(self.checkList.pop(), callback)

	def sanitizeOptions(self, origOptions, mounttype=None, username=None, password=None):
		# split the options into their components
		lexer = shlex.shlex(origOptions, posix=True)
		lexer.whitespace_split = True
		lexer.whitespace = ','
		options = list(map(str.strip, list(lexer)))

		# if not specified, mount read/write
		if 'ro' not in options and 'rw' not in options:
			options.append('rw')

		# cifs specific options

		if mounttype == "cifs":
			# remove any hardcoded username and passwords
			options = [i for i in options if not i.startswith('user=')]
			options = [i for i in options if not i.startswith('username=')]
			options = [i for i in options if not i.startswith('pass=')]
			options = [i for i in options if not i.startswith('password=')]

			# and add any passed
			if username or password:
				options.append('username="%s"' % username)
				options.append('password="%s"' % ("" if password is None else password))

			# default to utf8
			if not [i for i in options if i.startswith('iocharset=')]:
				options.append('iocharset=utf8')

		# nfs specific options

		elif mounttype == "nfs":

			# if not specified, disable locking
			if 'lock' not in options and 'nolock' not in options:
				options.append('nolock')

			# if no protocol given, default to udp
			if 'tcp' not in options and 'udp' not in options and 'proto=tcp' not in options and 'proto=udp' not in options:
				options.append('proto=tcp')

			# by default do not retry
			if not [i for i in options if i.startswith('retry=')]:
				options.append('retry=0')

			# if not specified, allow file service interruptions
			if 'intr' not in options and 'nointr' not in options:
				options.append('intr')

			# if not specified, don't hang on server errors
			if 'soft' not in options and 'hard' not in options:
				options.append('soft')

			# if not specified, don't update last access time
			if 'atime' not in options and 'noatime' not in options and 'relatime' not in options:
				options.append('noatime')

		# unknown mounttype
		else:
			print("[AutoMount.py] Unknown mount type: ", mounttype)

		# return the sanitized options list
		return ",".join(options)

	def CheckMountPoint(self, item, callback):
		# possible CIFS version/security combinations
		secvers = (
			'vers=3.0,sec=ntlmssp', 'vers=3.0,sec=ntlmv2', 'vers=2.1,sec=ntlmssp', 'vers=2.1,sec=ntlmv2',
			'vers=2.1,sec=ntlm', 'vers=1.0,sec=ntlmssp', 'vers=1.0,sec=ntlmv2', 'vers=1.0,sec=ntlm',
			'vers=default', ''
		)

		# create a console object if it doesnt exist
		if not self.MountConsole:
			self.MountConsole = Console()

		def enc(val):
			if six.PY2:
				return val.encode("UTF-8")
			return val

		# fetch the config for tis mount
		data = self.automounts[item]

		# by default, no command to execute
		command = None

		# construct the mount path
		path = os.path.join('/media/net', data['sharename'])

		# any active mounts?
		if self.activeMountsCounter == 0:
			# nope, nothing more to do there
			print("[AutoMount.py] self.automounts without active mounts", self.automounts)

		# current mount definition disabled?
		if data['active'] == 'False' or data['active'] is False:
			# unmount it
			command = "umount -fl '%s'" % path
			print("[AutoMount.py] UMOUNT-CMD-1 --->", command)

		# current mount definition active
		else:

			try:
				# unmount if something already mounted there
				# if so, unmount that first
				umountcmd = "umount -fl '%s'" % path
				print("[AutoMount.py] UMOUNT-CMD-3 --->", umountcmd)
				ret = subprocess.call(umountcmd, shell=True)

				# make sure the mount point exists
				if not os.path.exists(path):
					os.makedirs(path)

				# host name goes before ip address
				host = data['host']
				if not host:
					host = data['ip']

				# NFS
				if data['mounttype'] == 'nfs':
					# validate and client the mount options
					options = self.sanitizeOptions(data['options'], data['mounttype'])

					# construct the NFS mount command, and mount it
					tmpcmd = "mount -t nfs -o %s '%s' '%s'" % (options, host + ':/' + data['sharedir'], path)
					command = enc(tmpcmd)
					# print("[AutoMount.py] NFS MOUNT-CMD--->", command)

				# CIFS
				elif data['mounttype'] == 'cifs':
					# validate and client the mount options
					options = self.sanitizeOptions(data['options'], data['mounttype'], data['username'], data['password'])

					# version and/or security level given?
					if "vers=" in options or "sec=" in options:

						# construct the CIFS mount command
						tmpcmd = "mount -t cifs -o %s '//%s/%s' '%s'" % (options, host, data['sharedir'], path)
						command = enc(tmpcmd)
						# print( "[AutoMount.py] CIFS MOUNT-CMD--->", command)

					else:
						# loop over the version and security options
						for secver in secvers:
							# add the options
							if options:
								secver += ','

							# construct the CIFS mount command
							tmpcmd = "mount -t cifs -o %s '//%s/%s' '%s'" % (secver + options, host, data['sharedir'], path)
							command = enc(tmpcmd)
							# print("[AutoMount.py] CIFS AUTODETECT MOUNTCMD--->", command)

							# attempt to mount it, don't use the background console here, we need to wait
							ret = subprocess.call(command, shell=True)
							print("[AutoMount.py] Command returned: ", ret)

							# mount succeeded?
							if ret == 0 and os.path.ismount(path):
								# save these options
								self.automounts[item]['options'] = secver + data['options']
								self.writeMountsConfig()
								# umount the test mount
								umountcmd = "umount -fl '%s'" % path
								print("[AutoMount.py] UMOUNT-AUTODETECT --->", umountcmd)
								ret = subprocess.call(umountcmd, shell=True)
								# print("[AutoMount.py] CIFS MOUNT-CMD--->", command)
								# and terminate the loop
								break

							command = None

			except Exception as ex:
					print("[AutoMount.py] Failed to create", path, "Error:", ex)

		# execute any command constructed
		if command:
			self.MountConsole.ePopen(command, self.CheckMountPointFinished, [data, callback])
		else:
			self.CheckMountPointFinished(None, None, [data, callback])

	def CheckMountPointFinished(self, result, retval, extra_args):
		print("[AutoMount.py] CheckMountPointFinished", result, retval)
		(data, callback) = extra_args
		path = os.path.join('/media/net', data['sharename'])
		print("[AutoMount.py] CheckMountPointFinished, verifying: ", path)

		if os.path.exists(path):
			if os.path.ismount(path):
				if data['sharename'] in self.automounts:
					self.automounts[data['sharename']]['isMounted'] = True
					desc = data['sharename']
					if self.automounts[data['sharename']]['hdd_replacement'] == 'True':  # hdd replacement hack
						self.makeHDDlink(path)
					harddiskmanager.addMountedPartition(path, desc)
			else:
				print("[AutoMount.py] CheckMountPointFinished, path not found, disabling...")
				if data['sharename'] in self.automounts:
					self.automounts[data['sharename']]['isMounted'] = False
				if os.path.exists(path):
					if not os.path.ismount(path):
						try:
							os.rmdir(path)
							harddiskmanager.removeMountedPartition(path)
						except Exception as ex:
							print("Failed to remove", path, "Error:", ex)
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
		print("[AutoMount.py] symlink %s %s" % (path, hdd_dir))
		if os.path.islink(hdd_dir):
			if os.readlink(hdd_dir) != path:
				os.remove(hdd_dir)
				os.symlink(path, hdd_dir)
		elif os.path.ismount(hdd_dir) is False:
			if os.path.isdir(hdd_dir):
				rm_rf(hdd_dir)
		try:
			os.symlink(path, hdd_dir)
		except OSError as ex:
			print("[AutoMount.py] add symlink fails!", ex)
		movie = os.path.join(hdd_dir, 'movie')
		if not os.path.exists(movie):
			try:
				os.mkdir(movie)
			except Exception as ex:
				print("[AutoMount.py] Failed to create ", movie, "Error:", ex)

	def mountTimeout(self):
		self.timer.stop()
		if self.MountConsole:
			if len(self.MountConsole.appContainers) == 0:
				print("self.automounts after mounting", self.automounts)
				if self.callback is not None:
					self.callback(True)

	def getMountsList(self):
		return self.automounts

	def getMountsAttribute(self, mountpoint, attribute):
		if mountpoint in self.automounts:
			if attribute in self.automounts[mountpoint]:
				return self.automounts[mountpoint][attribute]
		return None

	def setMountsAttribute(self, mountpoint, attribute, value):
		if mountpoint in self.automounts:
			self.automounts[mountpoint][attribute] = value

	def writeMountsConfig(self):
		# Generate List in RAM
		self.list = ['<?xml version="1.0" ?>\n<mountmanager>\n']
		for sharename, sharedata in list(self.automounts.items()):
			mtype = sharedata['mounttype']
			self.list.append('<' + mtype + '>\n')
			self.list.append(' <mount>\n')
			self.list.append("  <active>" + str(sharedata['active']) + "</active>\n")
			self.list.append("  <hdd_replacement>" + str(sharedata['hdd_replacement']) + "</hdd_replacement>\n")
			if sharedata['host']:
				self.list.append("  <host>" + sharedata['host'] + "</host>\n")
			if sharedata['ip']:
				self.list.append("  <ip>" + sharedata['ip'] + "</ip>\n")
			self.list.append("  <sharename>" + sharedata['sharename'] + "</sharename>\n")
			self.list.append("  <sharedir>" + sharedata['sharedir'] + "</sharedir>\n")
			self.list.append("  <options>" + sharedata['options'] + "</options>\n")

			if sharedata['mounttype'] == 'cifs':
				self.list.append("  <username>" + sharedata['username'] + "</username>\n")
				self.list.append("  <password>" + sharedata['password'] + "</password>\n")

			self.list.append(' </mount>\n')
			self.list.append('</' + mtype + '>\n')

		# Close Mountmanager Tag
		self.list.append('</mountmanager>\n')

		# Try Saving to Flash
		try:
			open(XML_FSTAB, "w").writelines(self.list)
		except Exception as e:
			print("[AutoMount.py] Error Saving Mounts List:", e)

	def stopMountConsole(self):
		if self.MountConsole is not None:
			self.MountConsole = None

	def removeMount(self, mountpoint, callback=None):
		print("[AutoMount.py] removing mount: ", mountpoint)
		self.newautomounts = {}
		for sharename, sharedata in list(self.automounts.items()):
			if sharename is not mountpoint.strip():
				self.newautomounts[sharename] = sharedata
		self.automounts.clear()
		self.automounts = self.newautomounts
		if not self.removeConsole:
			self.removeConsole = Console()
		path = '/media/net/' + mountpoint
		umountcmd = "umount -fl '%s'" % path
		print("[AutoMount.py] UMOUNT-CMD--->", umountcmd)
		self.removeConsole.ePopen(umountcmd, self.removeMountPointFinished, [path, callback])

	def removeMountPointFinished(self, result, retval, extra_args):
		print("[AutoMount.py] removeMountPointFinished result", result, "retval", retval)
		(path, callback) = extra_args
		if os.path.exists(path):
			if not os.path.ismount(path):
				try:
					os.rmdir(path)
					harddiskmanager.removeMountedPartition(path)
				except Exception as ex:
					print("Failed to remove", path, "Error:", ex)
		if self.removeConsole:
			if len(self.removeConsole.appContainers) == 0:
				if callback is not None:
					self.callback = callback
					self.timer.startLongTimer(1)


iAutoMount = AutoMount()
