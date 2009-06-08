from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Screens.Screen import Screen

class SimpleMenu(Screen):
	skin = """
	<screen position="130,90" size="460,380" title="Select..." >
		<widget name="list" position="1,1" size="458,378" transparent="1" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session, list):
		Screen.__init__(self, session)
		
		self.list = []
		self.completeList = list
		
		for x in list:
			self.list.append(x[0])
		
		self["list"] = MenuList(self.list)
		
		self["actions"] = ActionMap(["OkCancelActions"], {"cancel": self.exit, "ok": self.okClicked}, -1)

	def exit(self):
		self.close(None)

	def okClicked(self):
		selected = self["list"].l.getCurrentSelection()
		if selected is not None:
			for x in self.completeList:
				if x[0] == selected:
					self.close(x[1])
