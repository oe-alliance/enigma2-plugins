# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Screens.ChannelSelection import SimpleChannelSelection

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button

# Configuration
from Components.config import getConfigListEntry, ConfigSelection

# Show ServiceName instead of ServiceReference
from ServiceReference import ServiceReference

class SimpleBouquetSelection(SimpleChannelSelection):
	def __init__(self, session, title):
		SimpleChannelSelection.__init__(self, session, title)
		self.skinName = "SimpleChannelSelection"

	def channelSelected(self): # just return selected service
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.close(ref)
		else:
			# TODO: we could just accept the current path here....
			print "[BouquetSelector] Dunno what to do, no directory selected:", ref," :-/"

class EPGRefreshServiceEditor(Screen, ConfigListScreen):
	"""Edit Services to be refreshed by EPGRefresh"""

	skin = """<screen name="EPGRefreshServiceEditor" title="Edit Services to refresh" position="75,150" size="565,245">
		<widget name="config" position="5,5" size="555,200" scrollbarMode="showOnDemand" />
		<ePixmap position="5,205" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
		<ePixmap position="145,205" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
		<ePixmap position="285,205" zPosition="4" size="140,40" pixmap="skin_default/key-yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="425,205" zPosition="4" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="5,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="145,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="285,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="425,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, services):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = "EPGRefresh Services"
		self.onChangedEntry = []

		# We need to copy the list to be able to ignore changes
		self.services = (
			services[0][:],
			services[1][:]
		)

		self.typeSelection = ConfigSelection(choices = [("channels", _("Channels")), ("bouquets", _("Bouquets"))])
		self.typeSelection.addNotifier(self.refresh, initial_call = False)

		self.reloadList()

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button(_("delete"))
		self["key_blue"] = Button(_("New"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.removeService,
				"blue": self.newService
			}
		)

		# Trigger change
		self.changed()

	def saveCurrent(self):
		del self.services[self.idx][:]
		
		# Warning, accessing a ConfigListEntry directly might be considered evil!

		myl = self["config"].getList()
		myl.pop(0)
		for item in myl:
			self.services[self.idx].append(item[1].value)

	def refresh(self, value):
		self.saveCurrent()

		self.reloadList()
		self["config"].setList(self.list)

	def reloadList(self):
		self.list = [
			getConfigListEntry(_("Editing"), self.typeSelection)
		]
		
		if self.typeSelection.value == "channels":
			self.idx = 0
		else: # self.typeSelection.value == "bouquets":
			self.idx = 1

		self.list.extend([
			getConfigListEntry(_("Refreshing"), ConfigSelection(choices = [(str(x), ServiceReference(str(x)).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''))]))
				for x in self.services[self.idx]
		])

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except:
				pass

	def getCurrentEntry(self):
		cur = self["config"].getCurrent()
		if cur:
			return cur[0]
		return ""

	def getCurrentValue(self):
		cur = self["config"].getCurrent()
		if cur:
			return str(cur[1].getText())
		return ""

	def createSummary(self):
		return SetupSummary

	def removeService(self):
		cur = self["config"].getCurrent()
		if cur:
			list = self["config"].getList()
			list.remove(cur)
			self["config"].setList(list)

	def newService(self):
		if self.typeSelection.value == "channels":
			self.session.openWithCallback(
				self.finishedServiceSelection,
				SimpleChannelSelection,
				_("Select channel to refresh")
			)
		else: # self.typeSelection.value == "bouquets":
			self.session.openWithCallback(
				self.finishedServiceSelection,
				SimpleBouquetSelection,
				_("Select bouquet to refresh")
			)

	def finishedServiceSelection(self, *args):
		if len(args):
			list = self["config"].getList()
			list.append(getConfigListEntry(
				_("Refreshing"),
				ConfigSelection(choices = [(args[0].toString(), ServiceReference(args[0]).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''))])
			))
			self["config"].setList(list)

	def cancel(self):
		self.close(None)

	def save(self):
		self.saveCurrent()

		self.close(self.services)
