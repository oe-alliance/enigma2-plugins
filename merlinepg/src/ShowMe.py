#######################################################################
#
#    ShowMe-Tool for Dreambox-Enigma2
#    Coded by Vali (c)2010
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


from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from enigma import ePicLoad, getDesktop


class ShowMe(Screen):
	if (getDesktop(0).size().width()) == 1280:
		skin = """
			<screen flags="wfNoBorder" position="0,0" size="1280,720" title="Show..." backgroundColor="#ffffffff">
				<widget name="Picture" position="0,0" size="1280,720" zPosition="1"/>
			</screen>"""
	elif (getDesktop(0).size().width()) == 1024:
		skin = """
			<screen flags="wfNoBorder" position="0,0" size="1024,576" title="Show..." backgroundColor="#ffffffff">
				<widget name="Picture" position="0,0" size="1024,576" zPosition="1"/>
			</screen>"""
	else:
		skin = """
			<screen flags="wfNoBorder" position="0,0" size="720,576" title="Show..." backgroundColor="#ffffffff">
				<widget name="Picture" position="0,0" size="720,576" zPosition="1"/>
			</screen>"""

	def __init__(self, session, whatPic=None):
		self.skin = ShowMe.skin
		Screen.__init__(self, session)
		self.whatPic = whatPic
		self.EXpicload = ePicLoad()
		self["Picture"] = Pixmap()
		self["actions"] = ActionMap(["WizardActions"],
		{
			"ok": self.close,
			"back": self.close
		}, -1)
		self.EXpicload.PictureData.get().append(self.DecodeAction)
		self.onLayoutFinish.append(self.Show_Picture)

	def Show_Picture(self):
		if self.whatPic is not None:
			self.EXpicload.setPara([self["Picture"].instance.size().width(), self["Picture"].instance.size().height(), 1, 1, 0, 1, "#121214"])
			self.EXpicload.startDecode(self.whatPic)

	def DecodeAction(self, pictureInfo=" "):
		if self.whatPic is not None:
			ptr = self.EXpicload.getData()
			self["Picture"].instance.setPixmap(ptr)
