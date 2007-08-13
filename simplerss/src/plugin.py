# warning, this is work in progress.
# plus, the error handling sucks.
#
# TODO:
#  - inline todos
#  - all that stuff I forgot...
#
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText
from Components.Button import Button
from Plugins.Plugin import PluginDescriptor
from enigma import eTimer, eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_WRAP

from httpclient import getPage
from urlparse import urlsplit
import xml.dom.minidom

from sets import Set

from Components.config import config, configfile, ConfigSubsection, ConfigSubList, ConfigEnableDisable, ConfigInteger, ConfigText, getConfigListEntry
from Components.ConfigList import ConfigListScreen

config.plugins.simpleRSS = ConfigSubsection()
config.plugins.simpleRSS.show_new = ConfigEnableDisable(default=True)
config.plugins.simpleRSS.interval = ConfigInteger(default=10, limits=(5, 300))
config.plugins.simpleRSS.feedcount = ConfigInteger(default=0)
config.plugins.simpleRSS.feed = ConfigSubList()
for i in range(0, config.plugins.simpleRSS.feedcount.value):
	config.plugins.simpleRSS.feed.append(ConfigSubsection())
	config.plugins.simpleRSS.feed[i].uri = ConfigText(default="http://", fixed_size = False)
	config.plugins.simpleRSS.feed[i].autoupdate = ConfigEnableDisable(default=True)

class SimpleRSSEdit(ConfigListScreen, Screen):
	skin = """
		<screen name="SimpleRSSEdit" position="100,100" size="550,120" title="Simple RSS Reader Setup" >
			<widget name="config" position="20,10" size="510,75" scrollbarMode="showOnDemand" />
			<ePixmap name="red"    position="0,75"   zPosition="4" size="140,40" pixmap="key_red-fs8.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="140,75" zPosition="4" size="140,40" pixmap="key_green-fs8.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,75" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,75" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, id):
		Screen.__init__(self, session)

		self.list = [ getConfigListEntry(_("Autoupdate: "), config.plugins.simpleRSS.feed[id].autoupdate), getConfigListEntry(_("Feed URI: "), config.plugins.simpleRSS.feed[id].uri) ]

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

class SimpleRSS(ConfigListScreen, Screen):
	skin = """
		<screen name="SimpleRSS" position="100,100" size="550,400" title="Simple RSS Reader Setup" >
			<widget name="config"  position="20,10" size="510,350" scrollbarMode="showOnDemand" />
			<ePixmap name="red"    position="0,360"   zPosition="4" size="140,40" pixmap="key_red-fs8.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="140,360" zPosition="4" size="140,40" pixmap="key_green-fs8.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,360" zPosition="4" size="140,40" pixmap="key_yellow-fs8.png" transparent="1" alphatest="on" />
			<ePixmap name="blue"   position="420,360" zPosition="4" size="140,40" pixmap="key_blue-fs8.png" transparent="1" alphatest="on" />
			<widget name="key_red"    position="0,360" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green"  position="140,360" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="280,360" zPosition="5" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue"   position="420,360" zPosition="5" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)

		self.onClose.append(self.abort)

		# nun erzeugen wir eine liste von elementen fuer die menu liste.
		self.list = [ ]
		for i in range(0, config.plugins.simpleRSS.feedcount.value):
			self.list.append(getConfigListEntry(_("Feed: "), config.plugins.simpleRSS.feed[i].uri))

		self.list.append(getConfigListEntry(_("Show new Messages: "), config.plugins.simpleRSS.show_new))
		self.list.append(getConfigListEntry(_("Update Interval (min): "), config.plugins.simpleRSS.interval))

		# die liste selbst
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
	
	def delete(self):
		self.session.openWithCallback(self.deleteConfirm, MessageBox, "Really delete this entry?\nIt cannot be recovered!")

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
		self.session.openWithCallback(self.refresh, SimpleRSSEdit, id)

	def refresh(self):
		pass

	def new(self):
		id = len(config.plugins.simpleRSS.feed)
		config.plugins.simpleRSS.feed.append(ConfigSubsection())
		config.plugins.simpleRSS.feed[id].uri = ConfigText(default="http://", fixed_size = False)
		config.plugins.simpleRSS.feed[id].autoupdate = ConfigEnableDisable(default=True)
		self.session.openWithCallback(self.conditionalNew, SimpleRSSEdit, id)

	def conditionalNew(self):
		id = len(config.plugins.simpleRSS.feed)-1
		# Check if new feed differs from default
		if config.plugins.simpleRSS.feed[id].uri.value == "http://":
			del config.plugins.simpleRSS.feed[id]
		else:
			self.list.insert(id, getConfigListEntry(_("Feed: "), config.plugins.simpleRSS.feed[id].uri))
			config.plugins.simpleRSS.feedcount.value = id+1

	def keySave(self):
		global rssPoller
		rssPoller.triggerReload()
		ConfigListScreen.keySave(self)

	def abort(self):
		print "[SimpleRSS] Closing Setup Dialog"
		# Keep feedcount sane
		config.plugins.simpleRSS.feedcount.value = len(config.plugins.simpleRSS.feed)
		config.plugins.simpleRSS.feedcount.save()

class RSSList(GUIComponent):
	def __init__(self, entries):
		GUIComponent.__init__(self)
		self.list = entries
		self.l = eListboxPythonMultiContent()
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setList(entries)
		
		self.onSelectionChanged = [ ]
		
	def connectSelChanged(self, fnc):
		if not fnc in self.onSelectionChanged:
			self.onSelectionChanged.append(fnc)

	def disconnectSelChanged(self, fnc):
		if fnc in self.onSelectionChanged:
			self.onSelectionChanged.remove(fnc)

	def selectionChanged(self):
		for x in self.onSelectionChanged:
			x()

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.setItemHeight(100)
		instance.selectionChanged.get().append(self.selectionChanged)

	def buildListboxEntry(self, title, link, summary, enclosures):
		res = [ None ]
		width = self.l.getItemSize().width()
		res.append(MultiContentEntryText(pos=(0, 0), size=(width, 75), font=0, flags = RT_HALIGN_LEFT|RT_WRAP, text = title))
		res.append(MultiContentEntryText(pos=(0, 75), size=(width, 20), font=1, flags = RT_HALIGN_LEFT, text = link))
		return res

	def getCurrentEntry(self):
		return self.l.getCurrentSelection()

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def moveToEntry(self, entry):
		if entry is None:
			return

		count = 0
		for x in self.list:
			if entry[0] == x[0]:
				self.instance.moveSelectionTo(count)
				break
			count += 1

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)

	def moveUp(self):
		self.instance.moveSelection(self.instance.moveUp)

class RSSView(Screen):
	skin = """
		<screen position="100,100" size="460,400" title="Simple RSS Reader" >
			<widget name="content" position="0,0" size="460,400" font="Regular; 22" />
		</screen>"""

	def __init__(self, session, data, enclosureCB=None, nextCB=None, previousCB=None):
		Screen.__init__(self, session)

		self.enclosureCB = enclosureCB
		self.nextCB = nextCB
		self.previousCB = previousCB

		self.data = data
		if data is not None:
			self["content"] = ScrollLabel("\n\n".join([data[0], data[2], " ".join([str(len(data[3])), "Enclosures"])]))
		else:
			self["content"] = ScrollLabel()

		self["actions"] = ActionMap([ "OkCancelActions", "ColorActions", "DirectionActions" ],
		{
			"cancel": self.close,
			"ok": self.selectEnclosure,
			"up": self.up,
			"down": self.down,
			"right": self.next,
			"left": self.previous,
		})

	def up(self):
		self["content"].pageUp()

	def down(self):
		self["content"].pageDown()

	def next(self):
		if self.nextCB is not None:
			self.data = self.nextCB()
			self.setContent()

	def previous(self):
		if self.previousCB is not None:
			self.data = self.previousCB()
			self.setContent()

	def setContent(self):
		if self.data is not None:
			self["content"].setText("\n\n".join([self.data[0], self.data[2], " ".join([str(len(self.data[3])), "Enclosures"])]))
		else:
			self["content"].setText("")

	def selectEnclosure(self):
		if self.data is not None and self.enclosureCB is not None:
			self.enclosureCB(self.data)

class RSSDisplay(Screen):
	skin = """
		<screen position="100,100" size="460,400" title="Simple RSS Reader" >
			<widget name="content" position="0,0" size="460,304" scrollbarMode="showOnDemand" />
			<widget name="summary" position="0,305" size="460,95" font="Regular;16" />
		</screen>"""

	MENU_UPDATE = 1
	MENU_CONFIG = 2

	def __init__(self, session, data, interactive = False, poller = None):
		Screen.__init__(self, session)

		if interactive:
			self["actions"] = ActionMap([ "OkCancelActions", "ChannelSelectBaseActions", "MenuActions" ], 
			{
				"ok": self.showCurrentEntry,
				"cancel": self.conditionalClose,
				"nextBouquet": self.next,
				"prevBouquet": self.previous,
				"menu": self.menu
			})
			self.onShown.append(self.__show)
			self.onClose.append(self.__close)

		self.rssPoller = poller
		self.feedview = False
		self.feeds = None
		self.feedid = None
		if len(data):
			if isinstance(data[0], Feed):
				self.feedview = True
				# TODO: find better way to solve this
				self.feeds = ([(feed.title, feed.description, ' '.join([str(len(feed.history)), "Entries"]), feed.history) for feed in data])
				self["content"] = RSSList(self.feeds)
				self["summary"] = Label(self.feeds[0][2])
			else:
				self["content"] = RSSList(data)
				self["summary"] = Label(data[0][2])
		else:
			self["content"] = RSSList(data)
			self["summary"] = Label("")

		self["content"].connectSelChanged(self.updateSummary)
		self.onLayoutFinish.append(self.setConditionalTitle)

	def __show(self):
		if rssPoller is not None:
			self.rssPoller.addCallback(self.pollCallback)

	def __close(self):
		if rssPoller is not None:
			self.rssPoller.removeCallback(self.pollCallback)

	def pollCallback(self, id = None):
		print "[SimpleRSS] RSSDisplay called back"
		current_entry = self["content"].getCurrentEntry()

		if self.feeds:
			if id is not None:
				print "[SimpleRSS] pollCallback updating feed", id
				self.feeds[id] = (self.rssPoller.feeds[id].title, self.rssPoller.feeds[id].description, ' '.join([str(len(self.rssPoller.feeds[id].history)), "Entries"]), self.rssPoller.feeds[id].history)
			else:
				print "[SimpleRSS] pollCallback updating all feeds"
				self.feeds = ([(feed.title, feed.description, ' '.join([str(len(feed.history)), "Entries"]), feed.history) for feed in self.rssPoller.feeds])

		if self.feedview:
			print "[SimpleRSS] pollCallback updating Feedlist"
			self["content"].l.setList(self.feeds)
		elif self.feedid:
			print "[SimpleRSS] pollCallback updating Itemlist"
			self["content"].l.setList(self.feeds[self.feedid][3])

		self["content"].moveToEntry(current_entry)
		self.setConditionalTitle()
		self.updateSummary()

	def setConditionalTitle(self):
		# Feedview: Overview, has feeds
		if self.feedview:
			self.setTitle("Simple RSS Reader")
		# Feedid: Feed, has feeds
		elif self.feedid is not None:
			self.setTitle(''.join(["Simple RSS Reader: ", self.feeds[self.feedid][0]]))
		# None: new_items
		else:
			self.setTitle("Simple RSS Reader: New Items")

	def updateSummary(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry:
			self["summary"].setText(current_entry[2])
		else:
			self["summary"].setText("")

	def menu(self):
		self.session.openWithCallback(self.menuChoice, ChoiceBox, "What to do?", [(_("Update Feed"), self.MENU_UPDATE), (_("Setup"), self.MENU_CONFIG)])

	def menuChoice(self, result):
		if result:
			if result[1] == self.MENU_UPDATE:
				self.rssPoller.singlePoll(self.feedid or self["content"].getCurrentIndex(), self.pollCallback)
				self.session.open(MessageBox, "Update is being done in Background.\nContents will automatically be updated when it's done.", type = MessageBox.TYPE_INFO, timeout = 5)
			elif result[1] == self.MENU_CONFIG:
				self.session.openWithCallback(self.menuClosed, SimpleRSS)

	def menuClosed(self):
		if self.feeds:
			current_entry = self["content"].getCurrentEntry()

			self.rssPoller.triggerReload()

			# TODO: fix this, its still as evil as some lines above
			self.feeds = ([(feed.title, feed.description, ' '.join([str(len(feed.history)), " Entries"]), feed.history) for feed in rssPoller.feeds])
			if self.feedview:
				self["content"].l.setList(self.feeds)

			self["content"].moveToEntry(current_entry)

	def nextEntryCB(self):
		self["content"].moveDown()
		return self["content"].getCurrentEntry()

	def previousEntryCB(self):
		self["content"].moveUp()
		return self["content"].getCurrentEntry()

	def next(self):
		if not self.feedview and self.feeds:
			self.feedid += 1
			if self.feedid == len(self.feeds):
				self.feedid = 0
			self["content"].l.setList(self.feeds[self.feedid][3])
			self["content"].moveToIndex(0)
			self.updateSummary()
			self.setConditionalTitle()

	def previous(self):
		if not self.feedview and self.feeds:
			if self.feedid == 0:
				self.feedid = len(self.feeds)
			self.feedid -= 1
			self["content"].l.setList(self.feeds[self.feedid][3])
			self["content"].moveToIndex(0)
			self.updateSummary()
			self.setConditionalTitle()

	def conditionalClose(self):
		if not self.feedview and self.feeds:
			self["content"].l.setList(self.feeds)
			self["content"].moveToIndex(self.feedid)
			self.feedview = True
			self.feedid = None
			self.updateSummary()
			self.setConditionalTitle()
		else:
			self.close()

	def showCurrentEntry(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry is None: # empty list
			return

		# If showing feeds right now show items of marked feed
		if self.feedview:
			self.feedid = self["content"].getCurrentIndex()
			self["content"].l.setList(current_entry[3])
			self["content"].moveToIndex(0)
			self.feedview = False
			self.updateSummary()
			self.setConditionalTitle()
		# Else we're showing items -> show marked item
		else:
			self.session.open(RSSView, current_entry, enclosureCB=self.selectEnclosure, nextCB=self.nextEntryCB, previousCB=self.previousEntryCB)

	def selectEnclosure(self, current_entry = None):
		if current_entry is None: # no entry given
			current_entry = self["content"].getCurrentEntry()

		if current_entry is None: # empty list
			return

		# Select stream in ChoiceBox if more than one present
		if len(current_entry[3]) > 1:
			# TODO: beautify
			self.session.openWithCallback(self.enclosureSelected, ChoiceBox, "Select enclosure to play", [(x[0][x[0].rfind("/")+1:], x) for x in current_entry[3]])
		# Play if one present
		elif len(current_entry[3]):
			self.enclosureSelected((None, current_entry[3][0]))
		# Nothing if none present

	def enclosureSelected(self, enclosure):
		if enclosure:
			(url, type) = enclosure[1]

			print "[SimpleRSS] Trying to play back enclosure: url=%s, type=%s" % (url, type)

			# TODO: other types? (showing images wouldn't be hard if the source was local)
			if type in ["video/mpeg", "audio/mpeg"]:
				# We should launch a Player here, but the MediaPlayer gets angry about our non-local sources
				from enigma import eServiceReference
				self.session.nav.playService(eServiceReference(4097, 0, url))

class Feed:
	MAX_HISTORY_ELEMENTS = 100

	RSS = 1
	ATOM = 2

	def __init__(self, uri, autoupdate):
		self.uri = uri
		self.autoupdate = autoupdate
		self.type = None
		self.title = uri.encode("UTF-8")
		self.description = ""
		self.last_update = None
		self.last_ids = set()
		self.history = []

	def gotDom(self, dom):
		if self.type is None:
			# RSS 2.0
			if dom.documentElement.getAttribute("version") in ["2.0", "0.94", "0.93", "0.92", "0.91"]:
				self.type = self.RSS
				try:
					self.title = dom.getElementsByTagName("channel")[0].getElementsByTagName("title")[0].childNodes[0].data.encode("UTF-8")
					self.description = dom.getElementsByTagName("channel")[0].getElementsByTagName("description")[0].childNodes[0].data.encode("UTF-8")
				except:
					pass
			# RSS 1.0 (NS: http://www.w3.org/1999/02/22-rdf-syntax-ns#)
			elif dom.documentElement.localName == "RDF":
				self.type = self.RSS
				try:
					self.title = dom.getElementsByTagName("channel")[0].getElementsByTagName("title")[0].childNodes[0].data.encode("UTF-8")
					self.description = dom.getElementsByTagName("channel")[0].getElementsByTagName("description")[0].childNodes[0].data.encode("UTF-8")
				except:
					pass
			# Atom (NS: http://www.w3.org/2005/Atom)
			elif dom.documentElement.localName == "feed":
				self.type = self.ATOM
				try:
					self.title = dom.getElementsByTagName("title")[0].childNodes[0].data.encode("UTF-8")
					self.description = dom.getElementsByTagName("subtitle")[0].childNodes[0].data.encode("UTF-8")
				except:
					pass
			else:
				raise NotImplementedError, 'Unsupported Feed: %s' % dom.documentElement.localName
		if self.type == self.RSS:
			print "[SimpleRSS] type is rss"
			return self.gotRSSDom(dom)
		elif self.type == self.ATOM:
			print "[SimpleRSS] type is atom"
			return self.gotAtomDom(dom)

	def gotRSSDom(self, dom):
		# Try to read when feed was last updated, if time equals return empty list. else fetch new items
		try:
			updated = dom.getElementsByTagName("lastBuildDate")[0].childNodes[0].data
			if not self.last_update == updated:
				self.last_update = updated
				return self.parseRSS(dom.getElementsByTagName("item"))
			else:
				return [ ]
		except:
			return self.parseRSS(dom.getElementsByTagName("item"))

	def parseRSS(self, items):
		new_items = []
		for item in items:
			enclosure = []

			# Try to read title, continue if none found
			try:
				title = item.getElementsByTagName("title")[0].childNodes[0].data
			except:
				continue

			# Try to read link, empty if none
			try:
				link = item.getElementsByTagName("link")[0].childNodes[0].data
			except:
				link = ""
			
			# Try to read guid, link if none (RSS 1.0 or invalid RSS 2.0)
			try:
				guid = item.getElementsByTagName("guid")[0].childNodes[0].data
			except:
				guid = link

			# Continue if item is to be excluded
			if guid in self.last_ids:
				continue

			# Try to read summary (description element), empty if none
			try:
				summary = item.getElementsByTagName("description")[0].childNodes[0].data
			except:
				summary = ""

			# Read out enclosures
			for current in item.getElementsByTagName("enclosure"):
				enclosure.append((current.getAttribute("url").encode("UTF-8"), current.getAttribute("type").encode("UTF-8")))

			# Update Lists
			new_items.append((title.encode("UTF-8").strip(), link.encode("UTF-8").strip(), summary.encode("UTF-8").strip(), enclosure))
			self.last_ids.add(guid)

		# Append known Items to new Items and evenentually cut it
		self.history = new_items + self.history
		self.history[:self.MAX_HISTORY_ELEMENTS]
		
		return new_items

	def gotAtomDom(self, dom):
		try:
			# Try to read when feed was last updated, if time equals return empty list. else fetch new items
			updated = dom.getElementsByTagName("updated")[0].childNodes[0].data
			if not self.last_update == updated:
				self.last_update = updated
				return self.parseAtom(dom.getElementsByTagName("entry"))
			else:
				return [ ]
		except:
			return self.parseAtom(dom.getElementsByTagName("entry"))

	def parseAtom(self, items):
		new_items = []
		for item in items:
			enclosure = []
			link = ""
			
			# Try to read title, continue if none found
			try:
				title = item.getElementsByTagName("title")[0].childNodes[0].data
			except:
				continue

			# Try to read id, continue if none found (invalid feed, should be handled differently) or to be excluded
			try:
				id = item.getElementsByTagName("id")[0].childNodes[0].data
				if id in self.last_ids:
					continue
			except:
				continue

			# Read out enclosures and link
			for current in item.getElementsByTagName("link"):
				# Enclosure
				if current.getAttribute("rel") == "enclosure":
					enclosure.append((current.getAttribute("href").encode("UTF-8"), current.getAttribute("type").encode("UTF-8")))
				# No Enclosure, assume its a link to the item
				else:
					link = current.getAttribute("href")
			
			# Try to read summary, empty if none
			try:
				summary = item.getElementsByTagName("summary")[0].childNodes[0].data
			except:
				summary = ""

			# Update Lists
			new_items.append((title.encode("UTF-8").strip(), link.encode("UTF-8").strip(), summary.encode("UTF-8").strip(), enclosure))
			self.last_ids.add(id)

		 # Append known Items to new Items and evenentually cut it
		self.history = new_items + self.history
		self.history[:self.MAX_HISTORY_ELEMENTS]

		return new_items

class RSSPoller:
	def __init__(self, session):
		self.poll_timer = eTimer()
		self.poll_timer.timeout.get().append(self.poll)
		self.poll_timer.start(0, 1)
		self.update_callbacks = [ ]
		self.last_links = Set()
		self.session = session
		self.dialog = None
		self.reloading = False
	
		self.feeds = [ ]
		for i in range(0, config.plugins.simpleRSS.feedcount.value):
			self.feeds.append(Feed(config.plugins.simpleRSS.feed[i].uri.value, config.plugins.simpleRSS.feed[i].autoupdate.value))
		self.new_items = [ ]
		self.current_feed = 0

	def addCallback(self, callback):
		if callback not in self.update_callbacks:
			self.update_callbacks.append(callback)

	def removeCallback(self, callback):
		if callback in self.update_callbacks:
			self.update_callbacks.remove(callback)

	def doCallback(self):
		for callback in self.update_callbacks:
			try:
				callback()
			except:
				pass

	# Single Functions are here to wrap
	def _gotSinglePage(self, id, callback, errorback, data):
		self._gotPage(data, id, callback, errorback)

	def singleError(self, errorback, error):
		self.error(error, errorback)

	def error(self, error, errorback = None):
		if not self.session:
			print "[SimpleRSS] error polling"
		elif errorback:
			errorback(error)
		else:
			self.session.open(MessageBox, "Sorry, failed to fetch feed.\n" + error, type = MessageBox.TYPE_INFO, timeout = 5)
			# Assume its just a temporary failure and jump over to next feed                          
			self.current_feed += 1                     
			self.poll_timer.start(1000, 1)

	def _gotPage(self, data, id = None, callback = None, errorback = None):
		# workaround: exceptions in gotPage-callback were ignored
		try:
			self.gotPage(data, id)
			if callback is not None:
				callback(id)
		except NotImplementedError, errmsg:
			# TODO: Annoying with Multifeed?
			self.session.open(MessageBox, "Sorry, this type of feed is unsupported.\n"+ str(errmsg), type = MessageBox.TYPE_INFO, timeout = 5)
		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			if errorback is not None:
				errorback()
			# Assume its just a temporary failure and jump over to next feed
			self.current_feed += 1
			self.poll_timer.start(1000, 1)
	
	def gotPage(self, data, id = None):
		print "[SimpleRSS] parsing.."

		# sometimes activates spinner :-/
		dom = xml.dom.minidom.parseString(data)

		print "[SimpleRSS] xml parsed.."

		# For Single-Polling
		if id is not None:
			self.feeds[id].gotDom(dom)
			print "[SimpleRSS] single feed parsed.."
			return
		else:
			new_items = self.feeds[self.current_feed].gotDom(dom)

		print "[SimpleRSS] feed parsed.."

		# Append new items to locally bound ones
		self.new_items.extend(new_items)

		# Start Timer so we can either fetch next feed or show new_items
		self.current_feed += 1
		self.poll_timer.start(1000, 1)


	def singlePoll(self, id, callback = None, errorback = None):
		from Tools.BoundFunction import boundFunction
		remote = urlsplit(self.feeds[id].uri)
		print "[SimpleRSS] updating", remote.geturl()
		hostname = remote.hostname
		port = remote.port or 80
		path = '?'.join([remote.path, remote.query])
		print "[SimpleRSS] hostname:", hostname, ", port:", port, ", path:", path
		getPage(hostname, port, path, callback=boundFunction(self._gotSinglePage, id, callback, errorback), errorback=boundFunction(self.error, errorback))

	def poll(self):
		# Reloading, reschedule
		if self.reloading:
			print "[SimpleRSS] timer triggered while reloading, rescheduling"
			self.poll_timer.start(10000, 1)
		# Dialog shown, hide
		elif self.dialog:
			print "[SimpleRSS] hiding"
			self.dialog.hide()
			self.dialog = None
			self.new_items = [ ]
			self.current_feed = 0
			self.poll_timer.startLongTimer(config.plugins.simpleRSS.interval.value*60)
		# End of List
		elif len(self.feeds) <= self.current_feed:
			# New Items
			if len(self.new_items):
				print "[SimpleRSS] got", len(self.new_items), "new items"
				print "[SimpleRSS] calling back"
				self.doCallback()
				# Inform User
				if config.plugins.simpleRSS.show_new.value:
					self.dialog = self.session.instantiateDialog(RSSDisplay, self.new_items, poller = self)
					self.dialog.show()
					self.poll_timer.startLongTimer(5)
			# No new Items
			else:
				print "[SimpleRSS] no new items"
				self.new_items = [ ]
				self.current_feed = 0
				self.poll_timer.startLongTimer(config.plugins.simpleRSS.interval.value*60)
		# Feed is supposed to auto-update
		elif self.feeds[self.current_feed].autoupdate:
			remote = urlsplit(self.feeds[self.current_feed].uri)
			hostname = remote.hostname
			port = remote.port or 80
			path = '?'.join([remote.path, remote.query])
			print "[SimpleRSS] hostname:", hostname, ", port:", port, ", path:", path
			self.d = getPage(hostname, port, path, callback=self._gotPage, errorback=self.error)
		# Go to next feed in 100ms
		else:
			print "[SimpleRSS] passing feed"
			self.current_feed += 1
			self.poll_timer.start(100, 1)

	def shutdown(self):
		self.poll_timer.timeout.get().remove(self.poll)
		self.poll_timer = None

	def triggerReload(self):
		self.reloading = True

		# TODO: Fix this evil way of updating feeds
		newfeeds = []
		for i in range(0, config.plugins.simpleRSS.feedcount.value):
			newfeeds.append(Feed(config.plugins.simpleRSS.feed[i].uri.value, config.plugins.simpleRSS.feed[i].autoupdate.value))

		self.feeds = newfeeds

		self.reloading = False

def main(session, **kwargs):
	print "[SimpleRSS] Displaying SimpleRSS-Setup"
	session.open(SimpleRSS)

rssPoller = None

def autostart(reason, **kwargs):
	global rssPoller
	
	# not nice (?), but works
	if kwargs.has_key("session") and reason == 0:
		rssPoller = RSSPoller(kwargs["session"])
	elif reason == 1:
		rssPoller.shutdown()
		rssPoller = None

def showCurrent(session, **kwargs):
	global rssPoller
	if rssPoller is None:
		return
	session.open(RSSDisplay, rssPoller.feeds, interactive = True, poller = rssPoller)

def Plugins(**kwargs):
 	return [ PluginDescriptor(name="RSS Reader", description="A (really) simple RSS reader", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
 		PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart),
 		PluginDescriptor(name="View RSS", description="Let's you view current RSS entries", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=showCurrent) ]
