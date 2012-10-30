##############################################################################
#                          <<< ViX Tuner Server >>>                           
#                                                                            
#                      2012 meo <lupomeo@hotmail.com>          
#                                                                            
#  This file is open source software; you can redistribute it and/or modify  
#     it under the terms of the GNU General Public License version 2 as      
#               published by the Free Software Foundation. 
#
#                    Modified for ViX Image by rossi2000                  
#                                                                            
##############################################################################

# This plugin implement the Tuner Server feature included in the ViX image
# Author: meo / rossi2000
# Please Respect credits

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Network import iNetwork
from Tools.Directories import fileExists
from os import system, rename as os_rename, remove as os_remove, chdir
from os.path import isdir
from enigma import eServiceCenter, eServiceReference, eTimer

class ViXTunerServer(Screen):
	skin = """
	<screen position="center,center" size="800,505" title="Tuner Server Setup">
		<widget name="lab1" position="10,4" size="780,400" font="Regular;20" transparent="1"/>
		<widget name="lab2" position="20,400" size="300,30" font="Regular;20" valign="center" transparent="1"/>
		<widget name="labstop" position="320,400" size="260,30" font="Regular;20" valign="center" halign="center" backgroundColor="red"/>
		<widget name="labrun" position="320,400" size="260,30" zPosition="1" font="Regular;20" valign="center" halign="center" backgroundColor="green"/>
		<ePixmap pixmap="skin_default/buttons/red.png" position="95,450" size="140,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/green.png" position="330,450" size="140,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="565,450" size="140,40" alphatest="on" />
		<widget name="key_red" position="95,450" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="transpBlack" transparent="1"/>
		<widget name="key_green" position="330,450" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="transpBlack" transparent="1"/>
		<widget name="key_yellow" position="565,450" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		mytext = """
This plugin implements the Tuner Server feature included in the ViX image. It will allow you to share the tuners of this box with another STB, PC and/or another compatible device in your home network.
The server will build a virtual channels list in the folder /media/hdd/tuner on this box.
You can access the tuner(s) of this box from clients on your internal lan using nfs, cifs, UPnP or any other network mountpoint.
The tuner of the server (this box) has to be avaliable. This means that if you have ony one tuner in your box you can only stream the channel you are viewing (or any channel you choose if your box is in standby).
Remember to select the correct audio track in the audio menu if there is no audio or the wrong language is streaming.
NOTE: The server is built, based on your current ip and the current channel list of this box. If you change your ip or your channel list is updated, you will need to rebuild the server database.

		"""
		self["lab1"] = Label(mytext)
		self["lab2"] = Label(_("Current Status:"))
		self["labstop"] = Label(_("Server Disabled"))
		self["labrun"] = Label(_("Server Enabled"))
		self["key_red"] = Label("Build Server")
		self["key_green"] = Label("Disable Server")
		self["key_yellow"] = Label("Close")
		self.my_serv_active = False
		self.ip = "0.0.0.0"

		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"ok": self.close,
			"back": self.close,
			"red": self.ServStart,
			"green": self.ServStop,
			"yellow": self.close
		})
		self.activityTimer = eTimer()
		self.activityTimer.timeout.get().append(self.doServStart)
		self.onClose.append(self.delTimer)
		self.onLayoutFinish.append(self.updateServ)



	def ServStart(self):
		self["lab1"].setText("Your Server Is Now Building\nPlease Wait ...")
		self.activityTimer.start(10)

	def doServStart(self):
		self.activityTimer.stop()
		ret = system("rm -rf /media/hdd/tuner")
		ifaces = iNetwork.getConfiguredAdapters()
		for iface in ifaces:
			ip = iNetwork.getAdapterAttribute(iface, "ip")
			ipm = "%d.%d.%d.%d" % (ip[0], ip[1], ip[2], ip[3])
			if ipm != "0.0.0.0":
				self.ip = ipm

		ret = system("mkdir /media/hdd/tuner")
		chdir("/media/hdd/tuner")
		s_type = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 22) || (type == 25) || (type == 134) || (type == 195)'
		serviceHandler = eServiceCenter.getInstance()
		services = serviceHandler.list(eServiceReference('%s FROM BOUQUET "bouquets.tv" ORDER BY bouquet'%(s_type)))
		bouquets = services and services.getContent("SN", True)
		count = 1
		for bouquet in bouquets:
			self.poPulate(bouquet, count)
			count += 1

		chdir("/home/root")
		mytext = """
Server avaliable on ip %s
To access this box's tuners you can connect via Lan or UPnP.

1) To connect via lan you have to mount the /media/hdd folder of this box in the client /media/hdd folder. Then you can access the tuners server channel list from the client Media player -> Harddisk -> tuner.
2) To connect via UPnP you need an UPnP server that can manage .m3u files like Mediatomb.
		""" % (self.ip)
		self["lab1"].setText(mytext)
		self.session.open(MessageBox, "Build Complete!", MessageBox.TYPE_INFO)
		self.updateServ()

	def poPulate(self, bouquet, count):
		n = "%03d_" % (count)
		name = n + self.cleanName(bouquet[1])
		path = "/media/hdd/tuner/" + name
		cmd = "mkdir \'" + path + "\'"
		system(cmd)
		serviceHandler = eServiceCenter.getInstance()
		services = serviceHandler.list(eServiceReference(bouquet[0]))
		channels = services and services.getContent("SN", True)
		count2 = 1
		for channel in channels:
			if not int(channel[0].split(":")[1]) & 64:
				n2 = "%03d_" % (count2)
				filename = path + "/" + n2 + self.cleanName(channel[1]) + ".m3u"
				try: 
					out = open(filename, "w")
				except:
					continue
				out.write("#EXTM3U\n")
				out.write("#EXTINF:-1," + channel[1] + "\n")
				out.write("http://" + self.ip + ":8001/" + channel[0]+ "\n\n")
				out.close()
				count2 += 1




	def cleanName(self, name):
		name = name.replace(" ", "_")
		name = name.replace('\xc2\x86', '').replace('\xc2\x87', '')
		name = name.replace(".", "_")
		name = name.replace("<", "")
		name = name.replace("<", "")
		name = name.replace("/", "")
		return name


	def ServStop(self):
		if self.my_serv_active == True:	
			ret = system("rm -rf /media/hdd/tuner")
			mybox = self.session.open(MessageBox, "Tuner Server Disabled.", MessageBox.TYPE_INFO)
			mybox.setTitle("Info")
			rc = system("sleep 1")
			self.updateServ()


	def updateServ(self):
		self["labrun"].hide()
		self["labstop"].hide()
		self.my_serv_active = False

		if isdir("/media/hdd/tuner"):
			self.my_serv_active = True
			self["labstop"].hide()
			self["labrun"].show()
		else:
			self["labstop"].show()
			self["labrun"].hide()

	def delTimer(self):
		del self.activityTimer


def settings(menuid, **kwargs):
	if menuid != "network":
		return []
	return [(_("Tuner Server Setup"), main, "tuner_server_setup", None)]

def main(session, **kwargs):
	session.open(ViXTunerServer)	

def Plugins(**kwargs):
	return PluginDescriptor(name="Tuner Server Setup", description="Allow Streaming From Box Tuners", where = PluginDescriptor.WHERE_MENU, fnc=settings)