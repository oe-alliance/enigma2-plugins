# -*- coding: utf-8 -*-
from Components.Sources.Source import Source
from os import popen as os_popen, path as os_path

class WebScriptList(Source):
	LIST = 0
	EXEC = 1
	
	def __init__(self, session, func=LIST, wap=False):
		Source.__init__(self)
		self.func = func
		self.wap = wap
		self.session = session
		self.res = (False, "Missing or Wrong Argument")
			
	def handleCommand(self, cmd):
		if cmd is not None:
			if self.func is self.EXEC:
				self.res = self.execScript(cmd)
			elif self.func is self.LIST:
				pass
			
	def execScript(self, cmd):
		return (False, "bla")
			
	def getList(self):
		list = []
		files = os_popen("ls /usr/script")
		for n in files:
			file = n[:-1]
			if file.endswith(".sh"):
				print "[WebScriptList] file ", file
				text = ""
				with open("/usr/script/" + file) as f:
					text = f.read()
					print "[WebScriptList] text ", text
					f.close()
				list.append((file, text))
		return list

	def getResult(self):
		if self.func is not self.LIST:
			return self.res
		return (False, "illegal call")

	result = property(getResult)
	
	list = property(getList)
	lut = {"Name": 0			, "Text": 1
		}
