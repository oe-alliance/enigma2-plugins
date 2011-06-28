#from Plugins.Plugin import PluginDescriptor
from MPHelp import MPHelp

from collections import Callable

helpList = []

class PluginHelp(object):
	def __init__(self, getNameFunc, getTextFunc, additionalSkin=""):
		if not isinstance(getNameFunc, Callable):
			print "NOT CALLABLE?!"
			getNameFunc = lambda x: getNameFunc
		self.getNameFunc = getNameFunc

		if not isinstance(getTextFunc, Callable):
			print "NOT CALLABLE EITHER?!"
			getTextFunc = lambda x: getTextFunc
		self.getTextFunc = getTextFunc

		self.additionalSkin = additionalSkin

	def __getattr__(self, attr):
		if attr == "name": return self.getNameFunc()
		elif attr == "text": return self.getTextFunc()
		return object.__getattr__(self, attr)

	def open(self, session):
		session.open(MPHelp, self.text, title=self.name, additionalSkin=self.additionalSkin)

	def openWithCallback(self, session, callback):
		assert isinstance(callback, Callable), "callback has to be callable!"
		session.openWithCallback(callback, MPHelp, self.text, title=self.name, additionalSkin=self.additionalSkin)

def registerHelp(getNameFunc, getTextFunc, additionalSkin=""):
	curName = getNameFunc()
	for x in helpList:
		if x.name == curName:
			return x
	x = PluginHelp(getNameFunc, getTextFunc, additionalSkin=additionalSkin)
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

__all__ = ['Plugins', 'registerHelp', 'showHelp']
