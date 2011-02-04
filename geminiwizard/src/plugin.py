# -*- coding: utf-8 -*-
from enigma import quitMainloop
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Tools.HardwareInfo import HardwareInfo
from Components.Ipkg import IpkgComponent as OpkgComponent
from os import path as os_path, system as os_system

#-------------------------------------------------------------------------------------------------

def setFeed():
	def _createFeedConf(type):
		wfile = open("/etc/opkg/gemini-%s-feed.conf" % (type), 'w')
		wfile.write("src/gz gemini-%s http://download.blue-panel.com/gemini3/%s\n" % (type, type))
		wfile.close()
		
	device = HardwareInfo()
	_createFeedConf('mipsel')
	_createFeedConf(device.get_device_name())
	_createFeedConf('all')
	return 1

#-------------------------------------------------------------------------------------------------
def checkForUgly():
	for x in ["/etc/MultiQuickButton", "/etc/init.d/CCcam", "/usr/lib/enigma2/python/Plugins/Extensions/Quickbutton"]:
		if os_path.exists(x):
			if x == "/etc/MultiQuickButton":
				return "Multiquickbutton plugin"
			elif x == "/etc/init.d/CCcam":
				return "pimp plugin (CCcam)"
			elif x == "/usr/lib/enigma2/python/Plugins/Extensions/Quickbutton":
				return "Quickbutton plugin"
		return ""

#-------------------------------------------------------------------------------------------------

def main(session, **kwargs):
	list =[
		(_("Install") + " Gemini Plugin", {"package": "geminiplugin"}),
		(_("Install") + " Gemini Plugin " + " ( + " + _("Plugins") + ")", {"package": "g3install-full"})
		]
	session.STATE=-1
	session.GP3PACKAGE=None
	session.info = None
	session.opkg = OpkgComponent()
	ugly = checkForUgly()
	
	def Exit(arg):
		exit(None)
	
	if ugly != "":
		session.openWithCallback(Exit, MessageBox, _("Gemini3 Wizard Installation stoped\nPlease remove '%s' first!") % ugly, MessageBox.TYPE_ERROR, timeout=15)
		
	def _reboot(val=None):
		FINALE = "depmod -a && update-modules"
		if session.GP3PACKAGE["package"] == "g3install-full":
			FINALE +=" && opkg remove g3install-full"
		os_system(FINALE)
		quitMainloop(2)
		
	def _opkgCallback(event, param):
		if event == OpkgComponent.EVENT_DONE:
			if session.STATE == 0:
				session.STATE=1
				session.opkg.startCmd(OpkgComponent.CMD_INSTALL, session.GP3PACKAGE)
				
			elif session.STATE == 1:
				session.info.close(True)
				
		elif event == OpkgComponent.EVENT_ERROR:
			session.open(MessageBox, _("Gemini3 Wizard: %s") % param, MessageBox.TYPE_ERROR, timeout=5)
			
	session.opkg.addCallback(_opkgCallback)
	
	def _closeInfo(val=None):
		if val is not None:
			session.openWithCallback(_reboot, MessageBox, _("Restart"), MessageBox.TYPE_INFO, timeout=5)
	
	def _selectPackage(pack):
		if pack is not None:
			session.info = session.openWithCallback(_closeInfo, MessageBox, _("Install") + " Gemini plugin...", type = MessageBox.TYPE_INFO, enable_input = False)
			session.GP3PACKAGE = pack[1]
			if setFeed():
				session.STATE=0
				session.opkg.startCmd(OpkgComponent.CMD_UPDATE)
		
	session.openWithCallback(_selectPackage, ChoiceBox, title = "Gemini3 Wizard", list = list)

#-------------------------------------------------------------------------------------------------

def Plugins(**kwargs):
	return PluginDescriptor(
			name=_("Gemini3 Wizard"),
			description=_("the Gemini3 plugin Wizard"),
			where = [PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU],
			icon="gp3wizard.png",
			fnc=main)
