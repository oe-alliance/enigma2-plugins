from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText

from . import _

class MPHelp(Screen):
	skin = """
		<screen name="MPHelp" flags="wfNoBorder" position="0,0" size="720,576">
			<ePixmap pixmap="skin_default/buttons/red.png" position="75,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="215,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="355,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="495,10" size="140,40" alphatest="on" />
			<widget render="Label" source="key_red" position="75,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<!--<widget render="Label" source="key_green" position="215,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />-->
			<widget render="Label" source="key_yellow" position="355,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget render="Label" source="key_blue" position="495,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<widget render="Label" source="title" position="60,50" size="600,50" zPosition="5" valign="center" halign="left" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="detailtext" position="60,120" size="610,370" zPosition="10" font="Regular;21" transparent="1" halign="left" valign="top"/>
		</screen>"""

	def __init__(self, session, pages, title="", additionalSkin=""):
		Screen.__init__(self, session)
		if additionalSkin:
			self.skinName = [additionalSkin, "MPHelp"]
		self.designatedTitle = title

		self["key_red"] = StaticText(_("Close"))
		#self["key_green"] = StaticText()
		self["key_yellow"] = StaticText("<<")
		self["key_blue"] = StaticText(">>")
		self["title"] = StaticText()
		self["detailtext"] = ScrollLabel()

		self.pages = pages
		self.curPage = 0

		self["actions"] = ActionMap(["ShortcutActions", "WizardActions"],
		{
			"back": self.close,
			"red": self.close,
			"up": self.pageUp,
			"down":	self.pageDown,
			"left":	self.pageUp,
			"right": self.pageDown,
			"yellow": self.prevPage,
			"blue": self.nextPage,
		}, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		if self.designatedTitle:
			self.setTitle(self.designatedTitle)
		self.setPage(0)

	def setPage(self, newPage):
		try:
			title, text = self.pages[newPage]
		except IndexError:
			title = "Invalid Help Page"
			text = "You managed to jump to an invalid page. Stop it :-)"
			newPage = self.curPage
		self["title"].text = title
		self["detailtext"].setText(text)
		self.curPage = newPage
	
	def pageUp(self):
		self["detailtext"].pageUp()

	def pageDown(self):
		self["detailtext"].pageDown()

	def prevPage(self):
		if self.curPage > 0:
			self.setPage(self.curPage - 1)

	def nextPage(self):
		if self.curPage < len(self.pages) - 1:
			self.setPage(self.curPage + 1)

