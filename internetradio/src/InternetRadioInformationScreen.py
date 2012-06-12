#
# InternetRadio E2
#
# Coded by Dr.Best (c) 2012
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Multimedia GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Multimedia GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Multimedia GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from enigma import getDesktop

class InternetRadioInformationScreen(Screen):

	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:
		skin = """
			<screen name="InternetRadioInformationScreen" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#00000000" title="Streaming Information">

				<ePixmap position="50,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="200,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap position="350,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="500,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<widget render="Label" source="key_red" position="50,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="headertext" position="50,77" zPosition="1" size="1180,26" font="Regular;22" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
				<widget name="text" position="50,120" size="1180,550" font="Regular;20" transparent="1"  backgroundColor="#00000000" />
			</screen>"""
	elif sz_w == 1024:
		skin = """
			<screen name="InternetRadioInformationScreen" position="0,0" size="1024,576" flags="wfNoBorder" backgroundColor="#00000000" title="Streaming Information">
				<ePixmap position="50,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="200,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap position="350,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="500,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<widget render="Label" source="key_red" position="50,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="headertext" position="50,77" zPosition="1" size="620,26" font="Regular;22" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
				<widget name="text" position="50,120" size="620,406" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000" />
			</screen>"""
	else:
		skin = """
			<screen name="InternetRadioInformationScreen" position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="#00000000" title="Streaming Information">
				<ePixmap position="50,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="210,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap position="370,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="530,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<widget render="Label" source="key_red" position="50,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="headertext" position="50,77" zPosition="1" size="620,26" font="Regular;22" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
				<widget name="text" position="50,120" size="620,406" font="Regular;20" transparent="1"  backgroundColor="#00000000" />
			</screen>"""

	def __init__(self, session, meta):
		Screen.__init__(self, session)
		self["key_red"] = StaticText(_("Close"))
		self["headertext"] = StaticText(_("Streaming Information"))
		self["text"] =  ScrollLabel(meta)
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions", "InfobarActions"],
		{
			"ok": self.close,
			"back": self.close,
			"red": self.close,
			"upUp": self.pageUp,
			"downUp": self.pageDown,
		}, -1)

	def pageUp(self):
		self["text"].pageUp()

	def pageDown(self):
		self["text"].pageDown()
