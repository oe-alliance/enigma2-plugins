# for localized messages
from . import _

# GUI (Screens)
from Screens.Screen import Screen

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList

class FTPQueueManager(Screen):
	skin = """
		<screen position="center,center" size="560,420" title="FTP Queue Manager" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="list" position="0,50" size="560,360" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, queue):
		Screen.__init__(self, session)
		self.queue = queue or []
		
		self["key_red"] = Label("")
		self["key_green"] = Label("")
		self["key_yellow"] = Label("")
		self["key_blue"] = Label("")
		self["list"] = MenuList([])

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.exit,
				"ok": self.ok,
			}, -1)
		
		self.onLayoutFinish.extend((
			self.layoutFinished,
			self.updateList,
		))

	def updateList(self, queue = None):
		if not queue:
			queue = self.queue

		list = []
		for item in queue:
			if item[0]:
				text = "DOWN "
			else:
				text = "UP   "

			text += item[1]
			text += " -> "
			text += item[2]

			list.append(text)

		self["list"].setList(list)

	def layoutFinished(self):
		self.setTitle(_("FTP Queue Manager"))

	def exit(self):
		self.close()

	def ok(self):
		pass

