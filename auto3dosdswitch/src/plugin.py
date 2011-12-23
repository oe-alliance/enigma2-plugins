#
#  Auto3DOSDSwitch E2
#
#  Coded by Dr.Best (c) 2010
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.ServiceEventTracker import ServiceEventTracker
from enigma import iPlayableService, iServiceInformation, eServiceCenter, eServiceReference
from ServiceReference import ServiceReference

def Plugins(**kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart)]

def autostart(session, **kwargs):
	Auto3DOSDSwitch(session)

class Auto3DOSDSwitch(Screen):
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
			{
				iPlayableService.evUpdatedInfo: self.__evUpdatedInfo,
				iPlayableService.evStart: self.__evStart
			})
		self.newService = False
		f = open('/proc/stb/fb/primary/3d' , "r")
		if f:
			self.lastmode = f.readline().replace('\n','')
			f.close()
		else:
			self.lastmode = "off"

	def __evStart(self):
		self.newService = True

	def __evUpdatedInfo(self):
		if self.newService and self.session.nav.getCurrentlyPlayingServiceReference():
			self.newService = False
			ref = self.session.nav.getCurrentService() 
			serviceRef = self.session.nav.getCurrentlyPlayingServiceReference()
			if serviceRef.getPath():
				serviceHandler = eServiceCenter.getInstance()
				r = eServiceReference(ref.info().getInfoString(iServiceInformation.sServiceref))
				info = serviceHandler.info(r)
				if info:
					name = ServiceReference(info.getInfoString(r, iServiceInformation.sServiceref)).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
				else:
					name = ""
			else:
				name =  ServiceReference(ref.info().getInfoString(iServiceInformation.sServiceref)).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')

			if name.lower().endswith("3d"): 
				mode = "sbs"
			else:
				mode = "off"

			if self.lastmode != mode:
				self.lastmode = mode
				f = open('/proc/stb/fb/primary/3d' , "w")
				if f:
					f.write("%s\n" % mode)
					f.close()
