# -*- coding: utf-8 -*-
from __future__ import print_function
from Components.Sources.Source import Source
from os import popen as os_popen, statvfs as os_statvfs, path as os_path
from shutil import move as sh_move

class PkgConfList(Source):
	LIST=0
	SWITCH=1
	MEM=2
	
	def __init__(self, session, func=LIST, wap=False):
		Source.__init__(self)
		self.func = func
		self.wap = wap
		self.session = session
		self.res = ( False, "Missing or Wrong Argument" )
			
	def handleCommand(self, cmd):
		if cmd is not None:
			if self.func is self.SWITCH:
				self.res = self.switch(cmd)
			if self.func is self.MEM:
				self.res = self.getMem()
			elif self.func is self.LIST:
				pass
			
	def switch(self, cmd):
		if cmd:
			try:
				file = cmd["file"]
				if os_path.exists("/etc/opkg/" + file):
					sh_move("/etc/opkg/" + file, "/etc/opkg/" + file + ".off")
					return (True, file + ".off")
				else:
					sh_move("/etc/opkg/" + file + ".off", "/etc/opkg/" + file)
					return (True, file)
			except Exception as e:
				return (False, str(e))
			
	def getMem(self):
		try:
			stat = os_statvfs("/")
		except OSError:
			return (False, "-1")
		freespace = stat.f_bfree / 1000 * stat.f_bsize / 1000
		return (True, '%d' %freespace)
			
	def getList(self):
		list = []
		files = os_popen("ls /etc/opkg")
		for n in files:
			file = n[:-1]
			if file.endswith(".conf") or file.endswith(".off"):
				print("[PkgConfList] file ", file)
				text =""
				with open("/etc/opkg/" + file) as f:
					text = f.read()
					print("[PkgConfList] text ", text)
					f.close()
				list.append((file, text))
		return list

	def getResult(self):
		if self.func is not self.LIST:
			return self.res
		return ( False, "illegal call" )

	result = property(getResult)
	
	list = property(getList)
	lut = {"Name": 0
			, "Text": 1
		}
