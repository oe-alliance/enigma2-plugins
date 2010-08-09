#######################################################################
#
#
#    Ai-HD-Skins Control for Dreambox/Enigma-2
#    Coded by Vali (c)2009-2010
#    Support: www.dreambox-tools.info
#
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#  To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
#
#######################################################################



from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.Console import Console
from Screens.Standby import TryQuitMainloop
from Components.ActionMap import ActionMap
from Components.config import config, ConfigYesNo, ConfigSubsection, getConfigListEntry, ConfigSelection, ConfigText, ConfigInteger
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Tools.Directories import fileExists
from skin import parseColor
from os import system



config.plugins.vhd  = ConfigSubsection()
config.plugins.vhd.Style = ConfigSelection(default="dmm", choices = [
				("dmm", _("DMM-Board")),
				("shadow", _("Shadow")),
				("beyonddreams", _("BeyondDreams-HD")),
				("whiteline", _("WhiteLine"))
				])
config.plugins.vhd.ChannSelector = ConfigSelection(default="full", choices = [
				("full", _("Full")),
				("pig", _("mini TV"))
				])



def main(session, **kwargs):
	session.open(AIHDsetup)



def Plugins(**kwargs):
	return PluginDescriptor(name="Ai.HD Controler", description=_("Configuration tool for All.In HD skins"), where = PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main)



#######################################################################




class AIHDsetup(ConfigListScreen, Screen):
	skin = """
		<screen name="AIHDsetup" position="center,center" size="600,340" title="Ai.HD Controler">
			<eLabel font="Regular;20" foregroundColor="#00ff4A3C" halign="center" position="20,308" size="120,26" text="Cancel"/>
			<eLabel font="Regular;20" foregroundColor="#0056C856" halign="center" position="165,308" size="120,26" text="Save"/>
			<widget name="config" position="5,5" scrollbarMode="showOnDemand" size="590,300"/>
		</screen>"""

	def __init__(self, session):
		self.release = ".release4"
		Screen.__init__(self, session)
		self.session = session
		self.datei = "/usr/share/enigma2/Ai.HD/skin.xml"
		self.daten = "/usr/lib/enigma2/python/Plugins/Extensions/AiHDcontroler/data/"
		self.komponente = "/usr/lib/enigma2/python/Plugins/Extensions/AiHDcontroler/comp/"
		list = []
		list.append(getConfigListEntry(_("Infobar and Window Style:"), config.plugins.vhd.Style))
		#list.append(getConfigListEntry(_("Channel and EPG selectors Style:"), config.plugins.vhd.ChannSelector))
		ConfigListScreen.__init__(self, list)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], 
									{
									"red": self.exit, 
									"green": self.save,
									"cancel": self.exit
									}, -1)
		self.onLayoutFinish.append(self.UpdateComponents)

	def UpdateComponents(self):
		if not fileExists(self.datei + self.release):
			system("tar -xzvf " + self.komponente + "AiHD.tar.gz" + " -C /")
			system('cp ' + self.komponente + 'vhdRendVolumeText.py /usr/lib/enigma2/python/Components/Renderer/vhdRendVolumeText.py')
			system('cp ' + self.komponente + 'vhdRendChNumber.py /usr/lib/enigma2/python/Components/Renderer/vhdRendChNumber.py')
			system('cp ' + self.komponente + 'vhdRendVideoSize.py /usr/lib/enigma2/python/Components/Renderer/vhdRendVideoSize.py')
			system('cp ' + self.komponente + 'vhdRendMovieDirSize.py /usr/lib/enigma2/python/Components/Renderer/vhdRendMovieDirSize.py')
			system('cp ' + self.komponente + 'vhdRendMaxTemp.py /usr/lib/enigma2/python/Components/Renderer/vhdRendMaxTemp.py')
			system('cp ' + self.komponente + 'vhdRendNextEvent.py /usr/lib/enigma2/python/Components/Renderer/vhdRendNextEvent.py')
			system('cp ' + self.komponente + 'vhdConvSmartInfo.py /usr/lib/enigma2/python/Components/Converter/vhdConvSmartInfo.py')
			system('cp ' + self.komponente + 'vhdConvClockToText.py /usr/lib/enigma2/python/Components/Converter/vhdConvClockToText.py')
			system("touch " + self.datei + self.release)

	def save(self):
		if not fileExists(self.datei + self.release):
			for x in self["config"].list:
				x[1].cancel()
			self.close()
			return
		for x in self["config"].list:
			x[1].save()
		try:
			skin_lines = []
			head_file = self.daten + "head.xml"
			skFile = open(head_file, "r")
			head_lines = skFile.readlines()
			skFile.close()
			for x in head_lines:
				skin_lines.append(x)
			skn_file = self.daten + "skin-" + config.plugins.vhd.Style.value + ".xml"
			skFile = open(skn_file, "r")
			file_lines = skFile.readlines()
			skFile.close()
			for x in file_lines:
				skin_lines.append(x)
			skn_file = self.daten + "channelselector-"
			if config.plugins.vhd.ChannSelector.value=="pig":
				skn_file = skn_file + "pig.xml"
			else:
				skn_file = skn_file + "full.xml"
			skFile = open(skn_file, "r")
			file_lines = skFile.readlines()
			skFile.close()
			for x in file_lines:
				skin_lines.append(x)
			base_file = self.daten + "main.xml"
			skFile = open(base_file, "r")
			file_lines = skFile.readlines()
			skFile.close()
			for x in file_lines:
				skin_lines.append(x)
			xFile = open(self.datei, "w")
			for xx in skin_lines:
				xFile.writelines(xx)
			xFile.close()
		except:
			self.session.open(MessageBox, _("Error by processing the skin file !!!"), MessageBox.TYPE_ERROR)
		restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("GUI needs a restart to apply a new skin.\nDo you want to Restart the GUI now?"), MessageBox.TYPE_YESNO)
		restartbox.setTitle(_("Restart GUI now?"))

	def restartGUI(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()

	def exit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()







