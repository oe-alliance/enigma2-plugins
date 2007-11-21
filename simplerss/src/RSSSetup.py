from Screens.Screen import Screen
from Components.config import config, ConfigSubsection, ConfigEnableDisable, ConfigText, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Button import Button
from Components.ActionMap import ActionMap

class RSSFeedEdit(ConfigListScreen, Screen):
	"""Edit an RSS-Feed"""
	skin = """
		<screen name="RSSFeedEdit" position="100,100" size="550,120" title="Simple RSS Reader Setup" >
			<widget name="config" position="20,10" size="510,75" scrollbarMode="showOnDemand" />
			<ePixmap name="red"    position="0,75"   zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="140,75" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,75" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,75" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, id):
		Screen.__init__(self, session)

		self.list = [
			getConfigListEntry(_("Autoupdate"), config.plugins.simpleRSS.feed[id].autoupdate),
			getConfigListEntry(_("Feed URI"), config.plugins.simpleRSS.feed[id].uri)
		]

		ConfigListScreen.__init__(self, self.list, session)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))

		self["setupActions"] = ActionMap(["SetupActions"],
		{
			"save": self.save,
			"cancel": self.keyCancel
		}, -1)

		self.id = id

	def save(self):
		config.plugins.simpleRSS.feed[self.id].save()
		config.plugins.simpleRSS.feed.save()
		self.close()

class RSSSetup(ConfigListScreen, Screen):
	"""Setup for SimpleRSS, quick-edit for Feed-URIs and settings present."""
	skin = """
		<screen name="RSSSetup" position="100,100" size="550,400" title="Simple RSS Reader Setup" >
			<widget name="config"  position="20,10" size="510,350" scrollbarMode="showOnDemand" />
			<ePixmap name="red"    position="0,360"   zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="140,360" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,360" zPosition="4" size="140,40" pixmap="skin_default/key-yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue"   position="420,360" zPosition="4" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
			<widget name="key_red"    position="0,360" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green"  position="140,360" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="280,360" zPosition="5" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue"   position="420,360" zPosition="5" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, rssPoller = None):
		Screen.__init__(self, session)

		self.onClose.append(self.abort)

		self.rssPoller = rssPoller

		# Create List of all Feeds
		self.list = [
			getConfigListEntry(_("Feed"), config.plugins.simpleRSS.feed[i].uri)
				for i in range(0, config.plugins.simpleRSS.feedcount.value)
		]

		# Attach notifier to autostart and append ConfigListEntry to List
		config.plugins.simpleRSS.autostart.addNotifier(self.autostartChanged, initial_call = False)
		self.list.append(getConfigListEntry(_("Start automatically with Enigma2"), config.plugins.simpleRSS.autostart))

		# Save keep_running in instance as we want to dynamically add/remove it
		self.keep_running = getConfigListEntry(_("Keep running in background"), config.plugins.simpleRSS.keep_running)
		if not config.plugins.simpleRSS.autostart.value:
			self.list.append(self.keep_running)

		# Append Last two config Elements
		self.list.append(getConfigListEntry(_("Show new Messages"), config.plugins.simpleRSS.show_new))
		self.list.append(getConfigListEntry(_("Update Interval (min)"), config.plugins.simpleRSS.interval))

		# Initialize ConfigListScreen
		ConfigListScreen.__init__(self, self.list, session)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button(_("New"))
		self["key_blue"] = Button(_("Delete"))

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"blue": self.delete,
			"yellow": self.new,
			"save": self.keySave,
			"cancel": self.keyCancel,
			"ok": self.ok
		}, -1)

	def autostartChanged(self, instance):
		# Remove keep_running from list if autostart is active
		if instance.value:
			self.list.remove(self.keep_running)
		# Otherwise add it at third position from behind
		else:
			self.list.insert(-2, self.keep_running)

		# Assign new List to ConfigList
		self["config"].setList(self.list)

	def delete(self):
		self.session.openWithCallback(
			self.deleteConfirm,
			MessageBox,
			_("Really delete this entry?\nIt cannot be recovered!")
		)

	def deleteConfirm(self, result):
		if result:
			id = self["config"].instance.getCurrentIndex()
			del config.plugins.simpleRSS.feed[id]
			config.plugins.simpleRSS.feedcount.value -= 1
			self.list.pop(id)
			# redraw list
			self["config"].setList(self.list)

	def ok(self):
		id = self["config"].instance.getCurrentIndex()
		self.session.openWithCallback(self.refresh, RSSFeedEdit, id)

	def refresh(self):
		# TODO: anything to be done here?
		pass

	def new(self):
		id = len(config.plugins.simpleRSS.feed)
		config.plugins.simpleRSS.feed.append(ConfigSubsection())
		config.plugins.simpleRSS.feed[id].uri = ConfigText(default="http://", fixed_size = False)
		config.plugins.simpleRSS.feed[id].autoupdate = ConfigEnableDisable(default=True)
		self.session.openWithCallback(self.conditionalNew, RSSFeedEdit, id)

	def conditionalNew(self):
		id = len(config.plugins.simpleRSS.feed)-1
		# Check if new feed differs from default
		if config.plugins.simpleRSS.feed[id].uri.value == "http://":
			del config.plugins.simpleRSS.feed[id]
		else:
			self.list.insert(id, getConfigListEntry(_("Feed"), config.plugins.simpleRSS.feed[id].uri))
			config.plugins.simpleRSS.feedcount.value = id+1

	def keySave(self):
		# Tell Poller to recreate List if present
		if self.rssPoller is not None:
			self.rssPoller.triggerReload()
		ConfigListScreen.keySave(self)

	def abort(self):
		print "[SimpleRSS] Closing Setup Dialog"

		# Remove Notifier
		config.plugins.simpleRSS.autostart.notifiers.remove(self.autostartChanged)

		# Keep feedcount sane
		config.plugins.simpleRSS.feedcount.value = len(config.plugins.simpleRSS.feed)
		config.plugins.simpleRSS.feedcount.save()

def addFeed(address, auto = False):
	# Read out ID
	id = len(config.plugins.simpleRSS.feed)

	# Create new Item
	config.plugins.simpleRSS.feed.append(ConfigSubsection())
	config.plugins.simpleRSS.feed[id].uri = ConfigText(default="http://", fixed_size = False)
	config.plugins.simpleRSS.feed[id].autoupdate = ConfigEnableDisable(default=True)

	# Set values
	config.plugins.simpleRSS.feed[id].uri = address
	config.plugins.simpleRSS.feed[id].autoupdate = auto

	# Save (needed?)
	config.plugins.simpleRSS.feed.save()
