##
## RS Downloader
## by AliAbdul
##
from Components.ActionMap import ActionMap
from Components.FileList import FileList
from Screens.Screen import Screen

##############################################################################

class RSListBrowser(Screen):
	skin = """
		<screen position="80,100" size="560,400" title="RS Downloader">
			<widget name="list" position="0,0" size="560,395" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, path):
		Screen.__init__(self, session)
		self["list"] = FileList(path, False, True, "^.*\.(txt)")
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.close}, -1)

	def okClicked(self):
		pass #don't do anything... only a small browser to view the lists atm!
