#from Plugins.Plugin import PluginDescriptor
from MPHelp import MPHelp

from collections import Callable

helpList = []

class PluginHelp(object):
	def __init__(self, getNameFunc, getPagesFunc, additionalSkin=""):
		if not isinstance(getNameFunc, Callable):
			getNameFunc = lambda x: getNameFunc
		self.getNameFunc = getNameFunc

		if not isinstance(getPagesFunc, Callable):
			getPagesFunc = lambda x: getPagesFunc
		self.getPagesFunc = getPagesFunc

		self.additionalSkin = additionalSkin

	def __getattr__(self, attr):
		if attr == "name": return self.getNameFunc()
		elif attr == "pages": return self.getPagesFunc()
		return object.__getattr__(self, attr)

	def open(self, session):
		session.open(MPHelp, self.pages, title=self.name, additionalSkin=self.additionalSkin)

	def openWithCallback(self, session, callback):
		assert isinstance(callback, Callable), "callback has to be callable!"
		session.openWithCallback(callback, MPHelp, self.pages, title=self.name, additionalSkin=self.additionalSkin)

def registerHelp(getNameFunc, getPagesFunc, additionalSkin=""):
	curName = getNameFunc()
	for x in helpList:
		if x.name == curName:
			return x
	x = PluginHelp(getNameFunc, getPagesFunc, additionalSkin=additionalSkin)
	helpList.append(x)
	return x

def showHelp(session, curName, callback=None):
	for x in helpList:
		if x.name == curName:
			if callback:
				x.openWithCallback(session, callback)
			else:
				x.open(session)
			return True
	return False

def Plugins(**kwargs):
	return [
	]

__all__ = ['Plugins', 'registerHelp', 'showHelp', 'PluginHelp']
