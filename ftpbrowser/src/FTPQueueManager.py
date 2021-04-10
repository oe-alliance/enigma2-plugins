# for localized messages
from . import _

# GUI (Screens)
from Screens.Screen import Screen

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText

# Tools
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

class FTPQueueManagerSummary(Screen):
	skin = """
	<screen position="0,0" size="132,64">
		<widget source="parent.Title" render="Label" position="6,4" size="120,21" font="Regular;18" />
		<widget source="parent.list" render="Label" position="6,25" size="120,21" font="Regular;16">
			<convert type="StringListSelection" />
		</widget>
		<widget source="global.CurrentTime" render="Label" position="56,46" size="82,18" font="Regular;16" >
			<convert type="ClockToText">WithSeconds</convert>
		</widget>
	</screen>"""

class FTPQueueManager(Screen):
	skin = """
		<screen position="center,center" size="560,420" title="FTP Queue Manager" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_blue" render="Label"  position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="list" render="Listbox" position="0,50" size="560,360" scrollbarMode="showAlways">
				<convert type="TemplatedMultiContent">
					{"template": [
							MultiContentEntryText(pos=(35,1), size=(510,19), text = 0, font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
							MultiContentEntryText(pos=(35,20), size=(510,18), text = 1, font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
							MultiContentEntryPixmapAlphaTest(pos=(2,2), size=(32,32), png = 2),
						],
					  "fonts": [gFont("Regular", 18)],
					  "itemHeight": 37
					 }
				</convert>
			</widget>
		</screen>"""

	def __init__(self, session, queue):
		Screen.__init__(self, session)
		self.queue = queue or []
		
		self["key_red"] = StaticText("")
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText("")
		self['list'] = List([])

		self.pixmaps = (
			LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/FTPBrowser/images/up.png")),
			LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/FTPBrowser/images/down.png"))
		)

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.exit,
				"ok": self.ok,
			}, -1)
		
		self.onLayoutFinish.extend((
			self.layoutFinished,
			self.updateList,
		))

	def createSummary(self):
		return FTPQueueManagerSummary

	def updateList(self, queue=None):
		if not queue:
			queue = self.queue

		pixmaps = self.pixmaps

		list = [(item[1], "-> " + item[2], pixmaps[item[0]]) for item in queue]

		# XXX: this is a little ugly but this way we have the least
		# visible distortion :-)
		index = min(self['list'].index, len(list)-1)
		self['list'].setList(list)
		self['list'].index = index

	def layoutFinished(self):
		self.setTitle(_("FTP Queue Manager"))

	def exit(self):
		self.close()

	def ok(self):
		pass

