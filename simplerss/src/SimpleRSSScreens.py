from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel

from RSSList import RSSList
from SimpleRSSSetup import SimpleRSSSetup

class SimpleRSSBase(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)

	def selectEnclosure(self, enclosures):
		if enclosures is None: # empty list
			return

		# Select stream in ChoiceBox if more than one present
		if len(enclosures) > 1:
			# TODO: beautify
			self.session.openWithCallback(self.enclosureSelected, ChoiceBox, "Select enclosure to play", [(x[0][x[0].rfind("/")+1:], x) for x in enclosures])
		# Play if one present
		elif len(enclosures):
			self.enclosureSelected((None, enclosures[0]))
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

class SimpleRSSEntry(SimpleRSSBase):
	skin = """
		<screen position="100,100" size="460,400" title="Simple RSS Reader" >
			<widget name="content" position="0,0" size="460,400" font="Regular; 22" />
		</screen>"""

	def __init__(self, session, data, feedTitle="", nextEntryCB=None, previousEntryCB=None, nextFeedCB=None, previousFeedCB=None):
		SimpleRSSBase.__init__(self, session)

		self.data = data
		self.feedTitle = feedTitle
		self.nextEntryCB = nextEntryCB
		self.previousEntryCB = previousEntryCB
		self.nextFeedCB = nextFeedCB
		self.previousFeedCB = previousFeedCB

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
			self.data = self.nextEntryCB()
			self.setContent()

	def previous(self):
		if self.previousEntryCB is not None:
			self.data = self.previousEntryCB()
			self.setContent()

	def nextFeed(self):
		# Show next Feed
		if self.nextFeedCB is not None:
			result = self.nextFeedCB()
			self.feedTitle = result[0]
			if len(result[1]):
				self.data = result[1][0]
			else:
				self.data = None
			self.setConditionalTitle()
			self.setContent()

	def previousFeed(self):
		# Show previous Feed
		if self.previousFeedCB is not None:
			result = self.previousFeedCB()
			self.feedTitle = result[0]
			if len(result[1]):
				self.data = result[1][0]
			else:
				self.data = None
			self.setConditionalTitle()
			self.setContent()

	def setContent(self):
		if self.data is not None:
			self["content"].setText("\n\n".join([self.data[0], self.data[2], " ".join([str(len(self.data[3])), "Enclosures"])]))
		else:
			self["content"].setText("No such Item.")

	def selectEnclosure(self):
		if self.data is not None:
			SimpleRSSBase.selectEnclosure(self, self.data[3])

class SimpleRSSFeed(SimpleRSSBase):
	skin = """
		<screen position="100,100" size="460,400" title="Simple RSS Reader" >
			<widget name="content" position="0,0" size="460,304" scrollbarMode="showOnDemand" />
			<widget name="summary" position="0,305" size="460,95" font="Regular;16" />
		</screen>"""

	def __init__(self, session, data, feedTitle = "", newItems=False, nextFeedCB=None, previousFeedCB=None, rssPoller=None, id = None):
		SimpleRSSBase.__init__(self, session)

		self.data = data
		self.feedTitle = feedTitle
		self.newItems = newItems
		self.id = id
		self.nextFeedCB=nextFeedCB
		self.previousFeedCB=previousFeedCB
		self.rssPoller=rssPoller

		if len(data):
			self["content"] = RSSList(data)
			self["summary"] = Label(data[0][2])
		else:
			self["content"] = RSSList([])
			self["summary"] = Label("Feed is empty.")

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
		
		self["content"].connectSelChanged(self.updateSummary)
		self.onLayoutFinish.append(self.setConditionalTitle)

	def __show(self):
		self.rssPoller.addCallback(self.pollCallback)

	def __close(self):
		self.rssPoller.removeCallback(self.pollCallback)

	def pollCallback(self, id = None):
		print "[SimpleRSS] SimpleRSSFeed called back"
		current_entry = self["content"].getCurrentEntry()

		if id is not None and self.id == id:
			print "[SimpleRSS] pollCallback recieved local feed", self.id
			self.feedTitle = self.rssPoller.feeds[id].title
			self.data = self.rssPoller.feeds[id].history
		else:
			print "[SimpleRSS] pollCallback recieved all feeds, updating", self.id
			self.feedTitle = self.rssPoller.feeds[id].title
			self.data = self.rssPoller.feeds[id].history

		self["content"].l.setList(self.data)
		self["content"].moveToEntry(current_entry)

		self.setConditionalTitle()
		self.updateSummary()

	def setConditionalTitle(self):
		if not self.newItems:
			self.setTitle(': '.join(["Simple RSS Reader", self.feedTitle]))
		else:
			self.setTitle("Simple RSS Reader: New Items")

	def updateSummary(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry:
			self["summary"].setText(current_entry[2])
		else:
			self["summary"].setText("Feed is empty.")

	def errorPolling(self):
		self.session.open(MessageBox, "Error while parsing Feed, this usually means there is something wrong with it.", type = MessageBox.TYPE_ERROR, timeout = 5)

	def menu(self):
		self.rssPoller.singlePoll(self.id, callback=True, errorback=self.errorPolling)
		self.session.open(MessageBox, "Update is being done in Background.\nContents will automatically be updated when it's done.", type = MessageBox.TYPE_INFO, timeout = 5)

	def nextEntryCB(self):
		self["content"].moveDown()
		return self["content"].getCurrentEntry()

	def previousEntryCB(self):
		self["content"].moveUp()
		return self["content"].getCurrentEntry()

	def next(self):
		# Show next Feed
		if self.nextFeedCB is not None:
			result = self.nextFeedCB()
			(self.feedTitle, self.data, self.id) = result
			current_entry = self["content"].getCurrentEntry()
			self["content"].l.setList(self.data) # Update list
			self["content"].moveToEntry(current_entry)
			self.updateSummary() # In case entry is no longer in history
			self.setConditionalTitle() # Update title
			return result
		return (self.feedTitle, self.data, self.id)

	def previous(self):
		# Show previous Feed
		if self.previousFeedCB is not None:
			result = self.previousFeedCB()
			(self.feedTitle, self.data, self.id) = result
			current_entry = self["content"].getCurrentEntry()
			self["content"].l.setList(self.data) # Update list
			self["content"].moveToEntry(current_entry)
			self.updateSummary() # In case entry is no longer in history
			self.setConditionalTitle() # Update title
			return result
		return (self.feedTitle, self.data, self.id)

	def showCurrentEntry(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry is None: # empty list
			return

		self.session.openWithCallback(self.updateSummary, SimpleRSSEntry, current_entry, feedTitle=self.feedTitle, nextEntryCB=self.nextEntryCB, previousEntryCB=self.previousEntryCB, nextFeedCB=self.next, previousFeedCB=self.previous)

	def selectEnclosure(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry is None: # empty list
			return

		SimpleRSSBase.selectEnclosure(self, current_entry[3])

class SimpleRSS(SimpleRSSBase):
	skin = """
		<screen position="100,100" size="460,400" title="Simple RSS Reader" >
			<widget name="content" position="0,0" size="460,304" scrollbarMode="showOnDemand" />
			<widget name="summary" position="0,305" size="460,95" font="Regular;16" />
		</screen>"""

	def __init__(self, session, poller):
		SimpleRSSBase.__init__(self, session)

		self.rssPoller = poller
		
		self["actions"] = ActionMap([ "OkCancelActions", "MenuActions", "ColorActions" ], 
		{
			"ok": self.showCurrentEntry,
			"cancel": self.close,
			"menu": self.menu,
			"yellow": self.selectEnclosure,
		})

		self.feeds = ([(feed.title, feed.description, ' '.join([str(len(feed.history)), "Entries"]), feed.history) for feed in self.rssPoller.feeds])
		if len(self.feeds):
			self["content"] = RSSList(self.feeds)
			self["summary"] = Label(self.feeds[0][2])
		else:
			self["content"] = RSSList(self.feeds)
			self["summary"] = Label("")

		self["content"].connectSelChanged(self.updateSummary)
		self.onShown.append(self.__show)
		self.onClose.append(self.__close)

	def __show(self):
		self.rssPoller.addCallback(self.pollCallback)

	def __close(self):
		self.rssPoller.removeCallback(self.pollCallback)

	def pollCallback(self, id = None):
		print "[SimpleRSS] SimpleRSS called back"
		current_entry = self["content"].getCurrentEntry()

		if id is not None:
			print "[SimpleRSS] pollCallback updating feed", id
			self.feeds[id] = (self.rssPoller.feeds[id].title, self.rssPoller.feeds[id].description, ' '.join([str(len(self.rssPoller.feeds[id].history)), "Entries"]), self.rssPoller.feeds[id].history)
		else:
			print "[SimpleRSS] pollCallback updating all feeds"
			self.feeds = ([(feed.title, feed.description, ' '.join([str(len(feed.history)), "Entries"]), feed.history) for feed in self.rssPoller.feeds])

		self["content"].l.setList(self.feeds)
		self["content"].moveToEntry(current_entry)

		self.updateSummary()

	def updateSummary(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry:
			self["summary"].setText(current_entry[2])
		else:
			self["summary"].setText("")

	def errorPolling(self):
		self.session.open(MessageBox, "Error while parsing Feed, this usually means there is something wrong with it.", type = MessageBox.TYPE_ERROR, timeout = 5)

	def menu(self):
		self.session.openWithCallback(self.menuChoice, ChoiceBox, "What to do?", [(_("Update Feed"), "update"), (_("Setup"), "setup"), (_("Close"), "close")])

	def menuChoice(self, result):
		if result:
			if result[1] == "update":
				self.rssPoller.singlePoll(self["content"].getCurrentIndex(), callback=True, errorback=self.errorPolling)
				self.session.open(MessageBox, "Update is being done in Background.\nContents will automatically be updated when it's done.", type = MessageBox.TYPE_INFO, timeout = 5)
			elif result[1] == "setup":
				self.session.openWithCallback(self.menuClosed, SimpleRSSSetup, rssPoller=self.rssPoller)
			elif result[1] == "close":
				self.close()

	def menuClosed(self):
		current_entry = self["content"].getCurrentEntry()

		self.rssPoller.triggerReload()

		self.feeds = ([(feed.title, feed.description, ' '.join([str(len(feed.history)), " Entries"]), feed.history) for feed in self.rssPoller.feeds])
		self["content"].l.setList(self.feeds)

		self["content"].moveToEntry(current_entry)
	
	# Same as menuClosed but without triggering a reload
	def refresh(self):
		current_entry = self["content"].getCurrentEntry()

		self.feeds = ([(feed.title, feed.description, ' '.join([str(len(feed.history)), " Entries"]), feed.history) for feed in self.rssPoller.feeds])
		self["content"].l.setList(self.feeds)

		self["content"].moveToEntry(current_entry)

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

		self.session.openWithCallback(self.refresh, SimpleRSSFeed, current_entry[3], feedTitle=current_entry[0], nextFeedCB=self.nextFeedCB, previousFeedCB=self.previousFeedCB, rssPoller=self.rssPoller, id=self["content"].getCurrentIndex())

	def selectEnclosure(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry is None: # empty list
			return

		# Build a list of all enclosures in this feed
		enclosures = []
		for entry in current_entry[3]:
				enclosures.extend(entry[3])
		SimpleRSSBase.selectEnclosure(self, enclosures)