from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel

from RSSList import RSSList
from RSSSetup import RSSSetup

class RSSBaseView(Screen):
	"""Base Screen for all Screens used in SimpleRSS"""

	def __init__(self, session):
		Screen.__init__(self, session)

	def errorPolling(self):
		self.session.open(
			MessageBox,
			"Error while parsing Feed, this usually means there is something wrong with it.",
			type = MessageBox.TYPE_ERROR,
			timeout = 5
		)

	def singleUpdate(self, feedid, errback = None):
		# Default errorback to self.errorPolling
		# If an empty errorback is wanted the Screen needs to provide it
		if errback is None:
			errback = self.errorPolling
		self.rssPoller.singlePoll(feedid, callback=True, errorback=errback)
		self.session.open(
			MessageBox,
			"Update is being done in Background.\nContents will automatically be updated when it's done.",
			type = MessageBox.TYPE_INFO,
			timeout = 5
		)

	def selectEnclosure(self, enclosures):
		# Empty List
		if enclosures is None:
			return
		# Select stream in ChoiceBox if more than one present
		elif len(enclosures) > 1:
			self.session.openWithCallback(
				self.enclosureSelected,
				ChoiceBox,
				"Select enclosure to play",
				[(x[0][x[0].rfind("/")+1:].replace('%20', ' '), x) for x in enclosures]
			)
		# Play if one present
		else:
			self.enclosureSelected((None, enclosures[0]))

	def enclosureSelected(self, enclosure):
		if enclosure:
			(url, type) = enclosure[1]

			print "[SimpleRSS] Trying to play back enclosure: url=%s, type=%s" % (url, type)

			# TODO: other types? (showing images wouldn't be hard if the source was local)
			if type in ["video/mpeg", "audio/mpeg"]:
				# We should launch a Player here, but the MediaPlayer gets angry about our non-local sources
				from enigma import eServiceReference
				self.session.nav.playService(eServiceReference(4097, 0, url))

class RSSEntryView(RSSBaseView):
	"""Shows a RSS Item"""
	skin = """
		<screen position="100,100" size="460,420" title="Simple RSS Reader" >
			<widget name="info" position="0,0" size="460, 20" halign="right" font="Regular; 18" />
			<widget name="content" position="0,20" size="460,420" font="Regular; 22" />
		</screen>"""

	def __init__(self, session, data, feedTitle="", cur_idx=None, entries=None, nextEntryCB=None, previousEntryCB=None, nextFeedCB=None, previousFeedCB=None):
		RSSBaseView.__init__(self, session)

		self.data = data
		self.feedTitle = feedTitle
		self.nextEntryCB = nextEntryCB
		self.previousEntryCB = previousEntryCB
		self.nextFeedCB = nextFeedCB
		self.previousFeedCB = previousFeedCB
		self.cur_idx = cur_idx
		self.entries = entries

		if cur_idx is not None and entries is not None:
			self["info"] = Label("Entry %s/%s" % (cur_idx+1, entries))
		else:
			self["info"] = Label()

		if data is not None:
			self["content"] = ScrollLabel("\n\n".join([data[0], data[2], " ".join([str(len(data[3])), "Enclosures"])]))
		else:
			self["content"] = ScrollLabel()

		self["actions"] = ActionMap([ "OkCancelActions", "ChannelSelectBaseActions", "ColorActions", "DirectionActions" ],
		{
			"cancel": self.close,
			"ok": self.selectEnclosure,
			"yellow": self.selectEnclosure,
			"up": self.up,
			"down": self.down,
			"right": self.next,
			"left": self.previous,
			"nextBouquet": self.nextFeed,
			"prevBouquet": self.previousFeed,
		})

		self.onLayoutFinish.append(self.setConditionalTitle)

	def setConditionalTitle(self):
		self.setTitle(': '.join(["Simple RSS Reader", self.feedTitle]))

	def up(self):
		self["content"].pageUp()

	def down(self):
		self["content"].pageDown()

	def next(self):
		if self.nextEntryCB is not None:
			(self.data, self.cur_idx, self.entries) = self.nextEntryCB()
			self.setContent()

	def previous(self):
		if self.previousEntryCB is not None:
			(self.data, self.cur_idx, self.entries) = self.previousEntryCB()
			self.setContent()

	def nextFeed(self):
		# Show next Feed
		if self.nextFeedCB is not None:
			result = self.nextFeedCB()
			self.feedTitle = result[0]
			self.entries = len(result[1])
			if self.entries:
				self.cur_idx = 0
				self.data = result[1][0]
			else:
				self.cur_idx = None
				self.data = None
			self.setConditionalTitle()
			self.setContent()

	def previousFeed(self):
		# Show previous Feed
		if self.previousFeedCB is not None:
			result = self.previousFeedCB()
			self.feedTitle = result[0]
			self.entries = len(result[1])
			if self.entries:
				self.cur_idx = 0
				self.data = result[1][0]
			else:
				self.cur_idx = None
				self.data = None
			self.setConditionalTitle()
			self.setContent()

	def setContent(self):
		if self.cur_idx is not None and self.entries is not None:
			self["info"].setText("Entry %s/%s" % (self.cur_idx+1, self.entries))
		else:
			self["info"].setText("")
		if self.data is not None:
			self["content"].setText("\n\n".join([self.data[0], self.data[2], " ".join([str(len(self.data[3])), "Enclosures"])]))
		else:
			self["content"].setText("No such Item.")

	def selectEnclosure(self):
		if self.data is not None:
			RSSBaseView.selectEnclosure(self, self.data[3])

class RSSFeedView(RSSBaseView):
	"""Shows a RSS-Feed"""
	skin = """
		<screen position="100,100" size="460,420" title="Simple RSS Reader" >
			<widget name="info" position="0,0" size="460,20" halign="right" font="Regular; 18" />
			<widget name="content" position="0,20" size="460,324" scrollbarMode="showOnDemand" />
			<widget name="summary" position="0,325" size="460,95" font="Regular;16" />
		</screen>"""

	def __init__(self, session, data, feedTitle = "", newItems=False, nextFeedCB=None, previousFeedCB=None, rssPoller=None, id = None):
		RSSBaseView.__init__(self, session)

		self.data = data
		self.feedTitle = feedTitle
		self.newItems = newItems
		self.id = id
		self.nextFeedCB=nextFeedCB
		self.previousFeedCB=previousFeedCB
		self.rssPoller=rssPoller

		self["content"] = RSSList(data)
		self["summary"] = Label()
		self["info"] = Label()

		if not newItems:
			self["actions"] = ActionMap([ "OkCancelActions", "ChannelSelectBaseActions", "MenuActions", "ColorActions" ], 
			{
				"ok": self.showCurrentEntry,
				"cancel": self.close,
				"nextBouquet": self.next,
				"prevBouquet": self.previous,
				"menu": self.menu,
				"yellow": self.selectEnclosure,
			})
			self.onShown.append(self.__show)
			self.onClose.append(self.__close)
		
		self["content"].connectSelChanged(self.updateInfo)
		self.onLayoutFinish.extend([self.updateInfo, self.setConditionalTitle])

	def __show(self):
		self.rssPoller.addCallback(self.pollCallback)

	def __close(self):
		self.rssPoller.removeCallback(self.pollCallback)

	def pollCallback(self, id = None):
		print "[SimpleRSS] SimpleRSSFeed called back"
		current_entry = self["content"].getCurrentEntry()

		if id is not None and self.id == id+1:
			print "[SimpleRSS] pollCallback recieved local feed", self.id
			self.feedTitle = self.rssPoller.feeds[id].title
			self.data = self.rssPoller.feeds[id].history
		elif self.id == 0:
			print "[SimpleRSS] pollCallback recieved all or non-local feed, updating active view (new_items)"
			self.data = self.rssPoller.new_items
		else:
			print "[SimpleRSS] pollCallback recieved all or non-local feed, updating", self.id
			self.feedTitle = self.rssPoller.feeds[self.id-1].title
			self.data = self.rssPoller.feeds[self-id-1].history

		self["content"].l.setList(self.data)
		self["content"].moveToEntry(current_entry)

		self.setConditionalTitle()
		self.updateInfo()

	def setConditionalTitle(self):
		if not self.newItems:
			self.setTitle(': '.join(["Simple RSS Reader", self.feedTitle]))
		else:
			self.setTitle("Simple RSS Reader: New Items")

	def updateInfo(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry:
			self["summary"].setText(current_entry[2])

			cur_idx = self["content"].getCurrentIndex()
			self["info"].setText("Entry %s/%s" % (cur_idx+1, len(self.data)))
		else:
			self["summary"].setText("Feed is empty.")
			self["info"].setText("")

	def menu(self):
		if self.id > 0:
			self.singleUpdate(self.id-1)

	def nextEntryCB(self):
		self["content"].moveDown()
		return (self["content"].getCurrentEntry(), self["content"].getCurrentIndex(), len(self.data))

	def previousEntryCB(self):
		self["content"].moveUp()
		return (self["content"].getCurrentEntry(), self["content"].getCurrentIndex(), len(self.data))

	# TODO: Fix moving back to previously marked entry (same goes for self.previous)
	def next(self):
		# Show next Feed
		if self.nextFeedCB is not None:
			result = self.nextFeedCB()
			(self.feedTitle, self.data, self.id) = result
			#current_entry = self["content"].getCurrentEntry()
			self["content"].l.setList(self.data) # Update list
			self["content"].moveToIndex(0)
			#self["content"].moveToEntry(current_entry)
			self.updateInfo() # In case entry is no longer in history
			self.setConditionalTitle() # Update title
			return result
		return (self.feedTitle, self.data, self.id)

	def previous(self):
		# Show previous Feed
		if self.previousFeedCB is not None:
			result = self.previousFeedCB()
			(self.feedTitle, self.data, self.id) = result
			#current_entry = self["content"].getCurrentEntry()
			self["content"].l.setList(self.data) # Update list
			self["content"].moveToIndex(0)
			#self["content"].moveToEntry(current_entry)
			self.updateInfo() # In case entry is no longer in history
			self.setConditionalTitle() # Update title
			return result
		return (self.feedTitle, self.data, self.id)

	def showCurrentEntry(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry is None: # empty list
			return

		self.session.openWithCallback(
			self.updateInfo,
			RSSEntryView,
			current_entry,
			cur_idx=self["content"].getCurrentIndex(),
			entries=len(self.data),
			feedTitle=self.feedTitle,
			nextEntryCB=self.nextEntryCB,
			previousEntryCB=self.previousEntryCB,
			nextFeedCB=self.next,
			previousFeedCB=self.previous
		)

	def selectEnclosure(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry is None: # empty list
			return

		RSSBaseView.selectEnclosure(self, current_entry[3])

class RSSOverview(RSSBaseView):
	"""Shows an Overview over all RSS-Feeds known to rssPoller"""
	skin = """
		<screen position="100,100" size="460,400" title="Simple RSS Reader" >
			<widget name="content" position="0,0" size="460,304" scrollbarMode="showOnDemand" />
			<widget name="summary" position="0,305" size="460,95" font="Regular;16" />
		</screen>"""

	def __init__(self, session, poller):
		RSSBaseView.__init__(self, session)

		self.rssPoller = poller
		
		self["actions"] = ActionMap([ "OkCancelActions", "MenuActions", "ColorActions" ], 
		{
			"ok": self.showCurrentEntry,
			"cancel": self.close,
			"menu": self.menu,
			"yellow": self.selectEnclosure,
		})

		self.fillFeeds()

		# We always have at least "New Items"-Feed
		self["content"] = RSSList(self.feeds)
		self["summary"] = Label(self.feeds[0][2])

		self["content"].connectSelChanged(self.updateSummary)
		self.onShown.append(self.__show)
		self.onClose.append(self.__close)

	def __show(self):
		self.rssPoller.addCallback(self.pollCallback)

	def __close(self):
		self.rssPoller.removeCallback(self.pollCallback)

	def fillFeeds(self):
		self.feeds = [(
			"New Items",
			"New Items since last Auto-Update",
			' '.join([str(len(self.rssPoller.new_items)), "Entries"]),
			self.rssPoller.new_items
		)]
		self.feeds.extend([
			(
				feed.title,
				feed.description,
				' '.join([str(len(feed.history)), "Entries"]),
				feed.history
			)
				for feed in self.rssPoller.feeds
		])

	def pollCallback(self, id = None):
		print "[SimpleRSS] SimpleRSS called back"
		current_entry = self["content"].getCurrentEntry()

		if id is not None:
			print "[SimpleRSS] pollCallback updating feed", id
			self.feeds[id+1] = (
				self.rssPoller.feeds[id].title,
				self.rssPoller.feeds[id].description,
				' '.join([str(len(self.rssPoller.feeds[id].history)), "Entries"]),
				self.rssPoller.feeds[id].history
			)
		else:
			print "[SimpleRSS] pollCallback updating all feeds"
			self.fillFeeds()

		self["content"].l.setList(self.feeds)
		self["content"].moveToEntry(current_entry)

		self.updateSummary()

	def updateSummary(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry:
			self["summary"].setText(current_entry[2])
		else:
			self["summary"].setText("")

	def menu(self):
		cur_idx = self["content"].getCurrentIndex()
		if cur_idx > 0:
			possible_actions = [
				(_("Update Feed"), "update"),
				(_("Setup"), "setup"),
				(_("Close"), "close")
			]
		else:
			possible_actions = [
				(_("Setup"), "setup"),
				(_("Close"), "close")
			]
		self.session.openWithCallback(
			self.menuChoice,
			ChoiceBox,
			"What to do?",
			possible_actions
		)

	def menuChoice(self, result):
		if result:
			if result[1] == "update":
				cur_idx = self["content"].getCurrentIndex()
				if cur_idx > 0:
					self.singleUpdate(cur_idx-1)
			elif result[1] == "setup":
				self.session.openWithCallback(self.refresh, RSSSetup, rssPoller=self.rssPoller)
			elif result[1] == "close":
				self.close()

	def refresh(self):
		current_entry = self["content"].getCurrentEntry()

		self.fillFeeds()
		self["content"].l.setList(self.feeds)

		self["content"].moveToEntry(current_entry)
		self.updateSummary()

	def nextFeedCB(self):
		self["content"].moveUp()
		current_entry = self["content"].getCurrentEntry()
		return (current_entry[0], current_entry[3], self["content"].getCurrentIndex())

	def previousFeedCB(self):
		self["content"].moveDown()
		current_entry = self["content"].getCurrentEntry()
		return (current_entry[0], current_entry[3], self["content"].getCurrentIndex())

	def showCurrentEntry(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry is None: # empty list
			return

		self.session.openWithCallback(
			self.refresh,
			RSSFeedView,
			current_entry[3],
			feedTitle=current_entry[0],
			nextFeedCB=self.nextFeedCB,
			previousFeedCB=self.previousFeedCB,
			rssPoller=self.rssPoller,
			id=self["content"].getCurrentIndex()
		)

	def selectEnclosure(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry is None: # empty list
			return

		# Build a list of all enclosures in this feed
		enclosures = []
		for entry in current_entry[3]:
				enclosures.extend(entry[3])
		RSSBaseView.selectEnclosure(self, enclosures)