# -*- coding: utf-8 -*-

from __future__ import print_function
from enigma import eListboxPythonMultiContent, gFont

from Plugins.Plugin import PluginDescriptor
from Bonjour import bonjour

from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.ActionMap import ActionMap

class BonjourScreen(Screen):	
	skin = """
	<screen position="center,center" size="600,400" title="Bonjour" >
		<widget name="menuList" position="10,10" size="580,380" scrollbarMode="showOnDemand" />
	</screen>"""
	
	def __init__(self, session, services, files):
		Screen.__init__(self, session)
		self.session = session
		self.services = services
		self.files = files
		
		self["menuList"] = MenuList([], content=eListboxPythonMultiContent)
		self["menuList"].l.setItemHeight(75)
		self["menuList"].l.setFont(0, gFont("Regular", 20) )
		self["menuList"].l.setFont(1, gFont("Regular", 16) )
		
		self["actions"] = ActionMap(["OkCancelActions"],
			{
			 "ok": self._ok,
			 "cancel": self._exit,
			 }, -1)
		
		self.onLayoutFinish.append(self.buildMenu)
		self.onLayoutFinish.append(self.layoutFinished)
								
	def layoutFinished(self):
		print("LAYOUT FINISHED!!")
		self.setTitle(_("Bonjour: Overview"))
										
	def _ok(self):
		print("OK OK OK OK")
		pass
	
	def _exit(self):
		self.close()
		
	def buildMenu(self):
		list = []
		for key in sorted(self.files):
			if self.files[key] != None:
				list.append( self.__buildMenuEntry(self.services[self.files[key]]) )
		
		self["menuList"].l.setList(list)
		self["menuList"].setList(list)
		
	def __buildMenuEntry(self, service):
		print("[Bonjour.__buildMenuEntry] service=%s" %service)
		
		file = "%s" %(service['file'])
		name = "Name: %s" %(service['name'])
		type = "Type: %s" %(service['type'].split('.')[0].replace('_', ''))
		prot = "Protocol: %s" %(service['type'].split('.')[1].replace('_', ''))
		port = "Port: %s" %(service['port'])
		text = "Text: %s" %(service['text'])
		
		return [
			service,
			MultiContentEntryText(pos=(5, 0), size=(185, 30), font=0, text=file),
			MultiContentEntryText(pos=(190, 0), size=(385, 30), font=0, text=name),
			MultiContentEntryText(pos=(5, 25), size=(150, 30), font=1, text=type),
			MultiContentEntryText(pos=(160, 25), size=(150, 30), font=1, text=prot),
			MultiContentEntryText(pos=(315, 25), size=(150, 30), font=1, text=port),
			MultiContentEntryText(pos=(5, 45), size=(570, 30), font=1, text=text)
		]
		
def opencontrol(session):
	bonjour.reloadConfig()
	session.open(BonjourScreen, bonjour.services, bonjour.files)
	print("[Bonjour.opencontrol] %s" %(bonjour.files))
	#TODO GUI-Stuff

	
def Plugins(**kwargs):
	return [ PluginDescriptor(
							name=_("Bonjour"), description=_("Control Bonjour (avahi-daemon)"),
							where=[PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=opencontrol)
			]
