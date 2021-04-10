#######################################################################
#
#    Vali-XD-Skins Control for Dreambox/Enigma-2
#    Coded by Vali (c)2009-2011
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#  To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
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



config.plugins.valiXDsetup  = ConfigSubsection()
config.plugins.valiXDsetup.ShowPicons = ConfigYesNo(default=False)
config.plugins.valiXDsetup.CenterMenus = ConfigYesNo(default=False)
config.plugins.valiXDsetup.Style = ConfigSelection(default="base", choices=[
				("base", _("Base")),
				("beyonddreams", _("Beyond Dreams")),
				("validator", _("Validator")),
				("shadow", _("Magic Shadow")),
				("shadow2", _("New Shadow")),
				("glas", _("Glas")),
				("metalpad", _("Metal Pad")),
				("vision", _("New Vision")),
				("atlantis", _("Atlantis")),
				("avalon", _("Avalon")),
				("blues", _("Blues of dream"))
				])
config.plugins.valiXDsetup.ChannSelector = ConfigSelection(default="simple", choices=[
				("simple", _("Simple")),
				("full", _("Full")),
				("full-vert", _("Full-vertical")),
				("full-hor", _("Full-horizontal")),
				("pig", _("with PiG"))
				])
config.plugins.valiXDsetup.dmType = ConfigSelection(default="800", choices=[
				("800", _("DM-800 Simple")),
				("8000", _("DM-8000 Full")),
				("7025", _("DM-7025")),
				("verysimple", _("Very simple"))
				])
config.plugins.valiXDsetup.BG = ConfigText(default="18111112", fixed_size=8)
config.plugins.valiXDsetup.FG = ConfigText(default="f0f0f0", fixed_size=6)
config.plugins.valiXDsetup.secondBG = ConfigText(default="18071230", fixed_size=8)
config.plugins.valiXDsetup.secondFG = ConfigText(default="fcc000", fixed_size=6)
config.plugins.valiXDsetup.selBG = ConfigText(default="08303240", fixed_size=8)
config.plugins.valiXDsetup.selFG = ConfigText(default="fcc000", fixed_size=6)
config.plugins.valiXDsetup.pollTime = ConfigInteger(default=15, limits=(3, 60))



def main(session, **kwargs):
	if fileExists("/usr/share/enigma2/Vali-XD/skin.xml"):
		session.open(XDsetup)
	else:
		#session.open(MessageBox,_("Vali-XD skin not installed.\nWe have nothing to control."), MessageBox.TYPE_INFO)
		pass



def Plugins(**kwargs):
	return PluginDescriptor(name="Vali-XD Skin Control", description=_("Configuration tool for Vali-XD skins"), where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main)



#######################################################################




class XDsetup(ConfigListScreen, Screen):
	skin = """
		<screen name="XDsetup" position="center,center" size="600,340" title="Vali-XD-Skin Control">
			<eLabel font="Regular;20" foregroundColor="#00ff4A3C" halign="center" position="20,308" size="120,26" text="Cancel"/>
			<eLabel font="Regular;20" foregroundColor="#0056C856" halign="center" position="165,308" size="120,26" text="Save"/>
			<eLabel font="Regular;20" foregroundColor="#00ffc000" halign="center" position="300,308" size="140,26" text="Test colors"/>
			<eLabel font="Regular;20" foregroundColor="#00879ce1" halign="center" position="455,308" size="120,26" text="ToolBox"/>
			<widget name="config" position="5,5" scrollbarMode="showOnDemand" size="590,300"/>
			<widget name="myTestLabel" position="1000,1000" size="2,2"/>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.datei = "/usr/share/enigma2/Vali-XD/skin.xml"
		self.daten = "/usr/lib/enigma2/python/Plugins/Extensions/ValiXDControl/data/"
		self.komponente = "/usr/lib/enigma2/python/Plugins/Extensions/ValiXDControl/comp/"
		self["myTestLabel"] = Label(_("t"))
		list = []
		list.append(getConfigListEntry(_("Infobar and Window Style:"), config.plugins.valiXDsetup.Style))
		list.append(getConfigListEntry(_("Channel and EPG selectors Style:"), config.plugins.valiXDsetup.ChannSelector))
		list.append(getConfigListEntry(_("Show Picons (Reference):"), config.plugins.valiXDsetup.ShowPicons))
		list.append(getConfigListEntry(_("Center Mainmenu and Plugins-list:"), config.plugins.valiXDsetup.CenterMenus))
		list.append(getConfigListEntry(_("OLED Layout like:"), config.plugins.valiXDsetup.dmType))
		list.append(getConfigListEntry(_("Base background:"), config.plugins.valiXDsetup.BG))
		#list.append(getConfigListEntry(_("Base foreground:"), config.plugins.valiXDsetup.FG))
		list.append(getConfigListEntry(_("Second background:"), config.plugins.valiXDsetup.secondBG))
		list.append(getConfigListEntry(_("Second foreground:"), config.plugins.valiXDsetup.secondFG))
		list.append(getConfigListEntry(_("Selected background:"), config.plugins.valiXDsetup.selBG))
		list.append(getConfigListEntry(_("Selected foreground:"), config.plugins.valiXDsetup.selFG))
		#list.append(getConfigListEntry(_("SmartInfo update time:"), config.plugins.valiXDsetup.pollTime))
		ConfigListScreen.__init__(self, list)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], 
									{
									"red": self.exit, 
									"green": self.save, 
									"yellow": self.colortest,
									"blue": self.toolBox,
									"cancel": self.exit
									}, -1)
		self.onLayoutFinish.append(self.UpdateComponents)
	
	def UpdateComponents(self):
		system('cp ' + self.komponente + 'vRendVolumeText.py /usr/lib/enigma2/python/Components/Renderer/vRendVolumeText.py')
		system('cp ' + self.komponente + 'vRendMaxTemp.py /usr/lib/enigma2/python/Components/Renderer/vRendMaxTemp.py')
		system('cp ' + self.komponente + 'vRendChNumber.py /usr/lib/enigma2/python/Components/Renderer/vRendChNumber.py')
		system('cp ' + self.komponente + 'vRendVideoSize.py /usr/lib/enigma2/python/Components/Renderer/vRendVideoSize.py')
		system('cp ' + self.komponente + 'vRendMovieDirSize.py /usr/lib/enigma2/python/Components/Renderer/vRendMovieDirSize.py')
		system('cp ' + self.komponente + 'vConvSmartInfo.py /usr/lib/enigma2/python/Components/Converter/vConvSmartInfo.py')
		system('cp ' + self.komponente + 'vConvClockToText.py /usr/lib/enigma2/python/Components/Converter/vConvClockToText.py')

	def save(self):
		CompsAreOK = False
		if fileExists("/usr/lib/enigma2/python/Components/Renderer/vRendChNumber.py") \
			and fileExists("/usr/lib/enigma2/python/Components/Renderer/vRendMaxTemp.py") \
			and fileExists("/usr/lib/enigma2/python/Components/Renderer/vRendVolumeText.py") \
			and fileExists("/usr/lib/enigma2/python/Components/Renderer/vRendVideoSize.py") \
			and fileExists("/usr/lib/enigma2/python/Components/Renderer/vRendMovieDirSize.py") \
			and fileExists("/usr/lib/enigma2/python/Components/Converter/vConvSmartInfo.py") \
			and fileExists("/usr/lib/enigma2/python/Components/Converter/vConvClockToText.py"):
			CompsAreOK = True
		if not(CompsAreOK):
			self.session.open(MessageBox,_("Vali-XD converters and renderers are not installed!!!"), MessageBox.TYPE_ERROR)
			self.close()
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
			skn_file = self.daten + "skin-" + config.plugins.valiXDsetup.Style.value
			if config.plugins.valiXDsetup.ShowPicons.value:
				skn_file = skn_file + "-picon.xml"
			else:
				skn_file = skn_file + ".xml"
			if (config.plugins.valiXDsetup.Style.value=='base'):
				if self.checkUserColors():
					skin_lines.append('  <!--  ##### Colors ##### -->\n')
					skin_lines.append('  <colors>\n')
					skin_lines.append('      <color name="background" value="#'+config.plugins.valiXDsetup.BG.value+'"/>\n')
					skin_lines.append('      <color name="foreground" value="#00f0f0f0"/>\n')
					skin_lines.append('      <color name="secondBG" value="#'+config.plugins.valiXDsetup.secondBG.value+'"/>\n')
					skin_lines.append('      <color name="secondFG" value="#00'+config.plugins.valiXDsetup.secondFG.value+'"/>\n')
					skin_lines.append('      <color name="selectedBG" value="#'+config.plugins.valiXDsetup.selBG.value+'"/>\n')
					skin_lines.append('      <color name="selectedFG" value="#00'+config.plugins.valiXDsetup.selFG.value+'"/>\n')
				else:
					skin_lines.append('  <!--  ##### Colors ##### -->\n')
					skin_lines.append('  <colors>\n')
					skin_lines.append('      <color name="background" value="#18111112"/>\n')
					skin_lines.append('      <color name="foreground" value="#00f0f0f0"/>\n')
					skin_lines.append('      <color name="secondBG" value="#18071230"/>\n')
					skin_lines.append('      <color name="secondFG" value="#00fcc000"/>\n')
					skin_lines.append('      <color name="selectedBG" value="#08303240"/>\n')
					skin_lines.append('      <color name="selectedFG" value="#00fcc000"/>\n')
			skFile = open(skn_file, "r")
			file_lines = skFile.readlines()
			skFile.close()
			for x in file_lines:
				skin_lines.append(x)
			skn_file = self.daten + "channelselector-"
			if config.plugins.valiXDsetup.ChannSelector.value=="pig":
				skn_file = skn_file + "pig.xml"
			elif config.plugins.valiXDsetup.ChannSelector.value=="full":
				skn_file = skn_file + "full.xml"
			elif config.plugins.valiXDsetup.ChannSelector.value=="full-vert":
				skn_file = skn_file + "full-vert.xml"
			elif config.plugins.valiXDsetup.ChannSelector.value=="full-hor":
				skn_file = skn_file + "full-hor.xml"
			else:
				skn_file = skn_file + "simple.xml"
			skFile = open(skn_file, "r")
			file_lines = skFile.readlines()
			skFile.close()
			for x in file_lines:
				skin_lines.append(x)
			mnu_file = self.daten + "menu-"
			if config.plugins.valiXDsetup.CenterMenus.value:
				mnu_file = mnu_file + "center.xml"
			else:
				mnu_file = mnu_file + "right.xml"
			skFile = open(mnu_file, "r")
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
			if config.plugins.valiXDsetup.dmType.value == "8000":
				oled_file = self.daten + "oled-8000.xml"
			elif config.plugins.valiXDsetup.dmType.value == "7025":
				oled_file = self.daten + "oled-7025.xml"                                
			elif config.plugins.valiXDsetup.dmType.value == "verysimple":
				oled_file = self.daten + "oled-VerySymple.xml"
			else:
				oled_file = self.daten + "oled-800.xml"
			skFile = open(oled_file, "r")
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

	def toolBox(self):
		contextFileList = [(_("Help information"), "INFO"),
						(_("Install round buttons"), "ROUNDBUTT"),
						(_("Install magic buttons"), "MAGICBUTT"),
						(_("Suomipoeka-Movielist patch"), "PATCHSUOMI"),
						(_("Colored icons patch"), "PATCHCONSTABLE")]
		self.session.openWithCallback(self.toolExec, ChoiceBox, title=_("Vali-XD Tool Box..."), list=contextFileList)
	
	def toolExec(self, answer):
		answer = answer and answer[1]
		if answer == "INFO":
			hilfeText = _("Color format: TTRRGGBB (hexadecimal)\nTT=Transparenty RR=Red GG=Green BB=Blue\nSee more colors by www.colorpicker.com\n\nSupport: www.dreambox-tools.info")
			self.session.open(MessageBox, hilfeText, MessageBox.TYPE_INFO)
		elif answer == "PATCHSUOMI":
			self.session.open(Console, cmdlist=[("chmod 755 " + self.komponente + "suomi_patch"), (self.komponente + "suomi_patch")])
		elif answer == "PATCHCONSTABLE":
			self.session.open(Console, cmdlist=[("tar -xzvf " + self.komponente + "spetial_icons.tar.gz" + " -C /")])
		elif answer == "ROUNDBUTT":
			self.session.open(Console, cmdlist=[("tar -xzvf " + self.komponente + "round_buttons.tar.gz" + " -C /")])
		elif answer == "MAGICBUTT":
			self.session.open(Console, cmdlist=[("tar -xzvf " + self.komponente + "magic_buttons.tar.gz" + " -C /")])

	def checkUserColors(self):
		if (config.plugins.valiXDsetup.Style.value=='base'):
			try:
				self["myTestLabel"].instance.setBackgroundColor(parseColor('#'+config.plugins.valiXDsetup.BG.value))
				self["myTestLabel"].instance.setBackgroundColor(parseColor('#'+config.plugins.valiXDsetup.FG.value))
				self["myTestLabel"].instance.setBackgroundColor(parseColor('#'+config.plugins.valiXDsetup.secondBG.value))
				self["myTestLabel"].instance.setBackgroundColor(parseColor('#'+config.plugins.valiXDsetup.secondFG.value))
				self["myTestLabel"].instance.setBackgroundColor(parseColor('#'+config.plugins.valiXDsetup.selBG.value))
				self["myTestLabel"].instance.setBackgroundColor(parseColor('#'+config.plugins.valiXDsetup.selFG.value))
				config.plugins.valiXDsetup.BG.save()
				config.plugins.valiXDsetup.FG.save()
				config.plugins.valiXDsetup.secondBG.save()
				config.plugins.valiXDsetup.secondFG.save()
				config.plugins.valiXDsetup.selBG.save()
				config.plugins.valiXDsetup.selFG.save()
				return True
			except:
				self.session.open(MessageBox, _("There are errors in the color-strings!\nThe PlugIn will use default colors."), MessageBox.TYPE_ERROR)
				return False
		else:
			self.session.open(MessageBox, _("Colors setup are only for Base-Style possible."), MessageBox.TYPE_INFO)

	def colortest(self):
		if self.checkUserColors():
			PreviewString='<screen backgroundColor="#'+config.plugins.valiXDsetup.BG.value+'" flags="wfNoBorder" position="0,433" size="1024,176" title="Preview">\n'
			PreviewString=PreviewString+'<ePixmap alphatest="off" pixmap="Vali-XD/border/up-shadow.png" position="0,0" size="1024,8" zPosition="0"/>\n'
			PreviewString=PreviewString+'<eLabel backgroundColor="#'+config.plugins.valiXDsetup.secondBG.value+'" font="Regular;22" foregroundColor="#'+config.plugins.valiXDsetup.secondFG.value
			PreviewString=PreviewString+'" halign="center" position="0,8" size="152,168" text="Second foreground" valign="center" zPosition="1"/>\n<eLabel backgroundColor="#'+config.plugins.valiXDsetup.secondBG.value
			PreviewString=PreviewString+'" font="Regular;22" foregroundColor="#'+config.plugins.valiXDsetup.secondFG.value+'" halign="center" position="872,8" size="152,168" text="Second foreground" valign="center" zPosition="1"/>\n'
			PreviewString=PreviewString+'<eLabel font="Regular;22" foregroundColor="#'+'00f0f0f0'+'" halign="center" position="275,45" size="457,30" text="Main element" valign="center" transparent="1" zPosition="2"/>\n'
			PreviewString=PreviewString+'<eLabel backgroundColor="#'+config.plugins.valiXDsetup.selBG.value+'" font="Regular;22" foregroundColor="#'+config.plugins.valiXDsetup.selFG.value
			PreviewString=PreviewString+'" halign="center" position="275,80" size="457,30" text="Selected element" valign="center" zPosition="2"/>\n</screen>'
			self.session.open(UserStylePreview, PreviewString)







#######################################################################



class UserStylePreview(Screen):
	def __init__(self, session, prvScreen='<screen position="80,150" size="560,310" title="Template">\n</screen>'):
		self.skin = prvScreen
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.close, "cancel": self.close}, -1)







