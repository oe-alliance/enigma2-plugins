from enigma import eTimer

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox

from Components.Scanner import openList

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel

from RSSList import RSSFeedList, RSSEntryList
from RSSSetup import RSSSetup

class RSSBaseView(Screen):
	"""Base Screen for all Screens used in SimpleRSS"""

	def __init__(self, session, poller, parent=None):
		Screen.__init__(self, session)
		self.rssPoller = poller
		self.pollDialog = None
		self.parent = parent

	def errorPolling(self, errmsg = ""):
		# An error occured while polling
		self.session.open(
			MessageBox,
			_("Error while parsing Feed, this usually means there is something wrong with it."),
			type = MessageBox.TYPE_ERROR,
			timeout = 3
		)

		# Don't show "we're updating"-dialog any longer
		if self.pollDialog:
			self.pollDialog.close()
			self.pollDialog = None

	def singleUpdate(self, feedid, errback = None):
		# Don't do anything if we have no poller
		if self.rssPoller is None:
			return

		# Default errorback to self.errorPolling
		# If an empty errorback is wanted the Screen needs to provide it
		if errback is None:
			errback = self.errorPolling

		# Tell Poller to poll
		self.rssPoller.singlePoll(feedid, callback=True, errorback=errback)

		# Open Dialog and save locally
		self.pollDialog = self.session.open(
			MessageBox,
			_("Update is being done in Background.\nContents will automatically be updated when it's done."),
			type = MessageBox.TYPE_INFO,
			timeout = 5
		)

	def selectEnclosure(self, enclosures):
		# Empty List
		if enclosures is None:
			return

		if not openList(self.session, enclosures):
			self.session.open(
				MessageBox,
				_("Found no Enclosure we can display."),
				type = MessageBox.TYPE_INFO, 
				timeout = 5
			)

class RSSEntryView(RSSBaseView):
	"""Shows a RSS Item"""
	skin = """
		<screen position="100,100" size="460,420" title="Simple RSS Reader" >
			<widget name="info" position="0,0" size="460, 20" halign="right" font="Regular; 18" />
			<widget name="content" position="0,20" size="460,400" font="Regular; 22" />
		</screen>"""

	def __init__(self, session, data, feedTitle="", cur_idx=None, entries=None, parent=None):
		RSSBaseView.__init__(self, session, None, parent)

		self.data = data
		self.feedTitle = feedTitle
		self.cur_idx = cur_idx
		self.entries = entries

		if cur_idx is not None and entries is not None:
			self["info"] = Label(_("Entry %s/%s") % (cur_idx+1, entries))
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
		if self.parent is not None:
			(self.data, self.cur_idx, self.entries) = self.parent.nextEntry()
			self.setContent()

	def previous(self):
		if self.parent is not None:
			(self.data, self.cur_idx, self.entries) = self.parent.previousEntry()
			self.setContent()

	def nextFeed(self):
		# Show next Feed
		if self.parent is not None:
			result = self.parent.next()
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
		if self.parent is not None:
			result = self.parent.previous()
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
			self["info"].setText(_("Entry %s/%s") % (self.cur_idx+1, self.entries))
		else:
			self["info"].setText("")
		if self.data is not None:
			self["content"].setText("\n\n".join([self.data[0], self.data[2], " ".join([str(len(self.data[3])), _("Enclosures")])]))
		else:
			self["content"].setText(_("No such Item."))

	def selectEnclosure(self):
		if self.data is not None:
			RSSBaseView.selectEnclosure(self, self.data[3])

class RSSFeedView(RSSBaseView):
	"""Shows a RSS-Feed"""
	skin = """
		<screen position="100,100" size="460,415" title="Simple RSS Reader" >
			<widget name="info" position="0,0" size="460,20" halign="right" font="Regular; 18" />
			<widget name="content" position="0,20" size="460,300" scrollbarMode="showOnDemand" />
			<widget name="summary" position="0,320" size="460,95" font="Regular;16" />
		</screen>"""

	def __init__(self, session, feed=None, newItems=False, parent=None, rssPoller=None,id=None):
		RSSBaseView.__init__(self, session, rssPoller, parent)

		self.feed = feed
		self.newItems = newItems
		self.id = id

		self["content"] = RSSEntryList(self.feed.history)
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
			self.onLayoutFinish.append(self.__show)
			self.onClose.append(self.__close)

			self.timer = None
		else:
			self["actions"] = ActionMap([ "OkCancelActions" ], 
			{
				"cancel": self.close,
			})

			self.timer = eTimer()
			self.timer.callback.append(self.timerTick)
			self.onExecBegin.append(self.startTimer)

		self["content"].connectSelChanged(self.updateInfo)
		self.onLayoutFinish.extend([self.updateInfo, self.setConditionalTitle])

	def startTimer(self):
		self.timer.startLongTimer(5)

	def timerTick(self):
		self.timer.callback.remove(self.timerTick)
		self.timer = None

		self.close()

	def __show(self):
		self.rssPoller.addCallback(self.pollCallback)

	def __close(self):
		if self.timer is not None:
			self.timer.callback.remove(self.timerTick)
			self.timer = None
		self.rssPoller.removeCallback(self.pollCallback)

	def pollCallback(self, id = None):
		print "[SimpleRSS] SimpleRSSFeed called back"

		if id is None or id+1 == self.id:
			# TODO: do we really need this?
			current_entry = self["content"].getCurrentEntry()
			self["content"].moveToEntry(current_entry)

			self["content"].invalidate()
			self.setConditionalTitle()
			self.updateInfo()

	def setConditionalTitle(self):
		self.setTitle(': '.join(["Simple RSS Reader", self.feed.title]))

	def updateInfo(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry:
			self["summary"].setText(current_entry[2])

			cur_idx = self["content"].getCurrentIndex()
			self["info"].setText(_("Entry %s/%s") % (cur_idx+1, len(self.feed.history)))
		else:
			self["summary"].setText(_("Feed is empty."))
			self["info"].setText("")

	def menu(self):
		if self.id > 0:
			self.singleUpdate(self.id-1)

	def nextEntry(self):
		self["content"].moveDown()
		return (self["content"].getCurrentEntry(), self["content"].getCurrentIndex(), len(self.feed.history))

	def previousEntry(self):
		self["content"].moveUp()
		return (self["content"].getCurrentEntry(), self["content"].getCurrentIndex(), len(self.feed.history))

	# TODO: Fix moving back to previously marked entry (same goes for self.previous)
	def next(self):
		# Show next Feed
		if self.parent is not None:
			(self.feed, self.id) = self.parent.nextFeed()
			#current_entry = self["content"].getCurrentEntry()
			self["content"].l.setList(self.feed.history) # Update list
			self["content"].moveToIndex(0)
			#self["content"].moveToEntry(current_entry)
			self.updateInfo() # In case entry is no longer in history
			self.setConditionalTitle() # Update title
			return (self.feed.title, self.feed.history, self.id)
		return (self.feed.title, self.feed.history, self.id)

	def previous(self):
		# Show previous Feed
		if self.parent is not None:
			(self.feed, self.id) = self.parent.previousFeed()
			#current_entry = self["content"].getCurrentEntry()
			self["content"].l.setList(self.feed.history) # Update list
			self["content"].moveToIndex(0)
			#self["content"].moveToEntry(current_entry)
			self.updateInfo() # In case entry is no longer in history
			self.setConditionalTitle() # Update title
			return (self.feed.title, self.feed.history, self.id)
		return (self.feed.title, self.feed.history, self.id)

	def checkEmpty(self):
		if self.id > 0 and not len(self.feed.history):
			self.singleUpdate(self.id-1)

	def showCurrentEntry(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry is None: # empty list
			return

		self.session.openWithCallback(
			self.updateInfo,
			RSSEntryView,
			current_entry,
			cur_idx=self["content"].getCurrentIndex(),
			entries=len(self.feed.history),
			feedTitle=self.feed.title,
			parent=self
		)

	def selectEnclosure(self):
		current_entry = self["content"].getCurrentEntry()
		if current_entry is None: # empty list
			return

		RSSBaseView.selectEnclosure(self, current_entry[3])

class RSSOverview(RSSBaseView):
	"""Shows an Overview over all RSS-Feeds known to rssPoller"""
	skin = """
		<screen position="100,100" size="460,415" title="Simple RSS Reader" >
			<widget name="info" position="0,0" size="460,20" halign="right" font="Regular; 18" />
			<widget name="content" position="0,20" size="460,300" scrollbarMode="showOnDemand" />
			<widget name="summary" position="0,320" size="460,95" font="Regular;16" />
		</screen>"""

	def __init__(self, session, poller):
		RSSBaseView.__init__(self, session, poller)

		self["actions"] = ActionMap([ "OkCancelActions", "MenuActions", "ColorActions" ], 
		{
			"ok": self.showCurrentEntry,
			"cancel": self.close,
			"menu": self.menu,
			"yellow": self.selectEnclosure,
		})

		self.fillFeeds()

		# We always have at least "New Items"-Feed
		self["content"] = RSSFeedList(self.feeds)
		self["summary"] = Label(' '.join([str(len(self.feeds[0][0].history)), _("Entries")]))
		self["info"] = Label(_("Feed %s/%s") % (1, len(self.feeds)))

		self["content"].connectSelChanged(self.updateInfo)
		self.onLayoutFinish.append(self.__show)
		self.onClose.append(self.__close)

	def __show(self):
		self.rssPoller.addCallback(self.pollCallback)

	def __close(self):
		self.rssPoller.removeCallback(self.pollCallback)

	def fillFeeds(self):
		# Feedlist contains our virtual Feed and all real ones
		self.feeds = [(self.rssPoller.newItemFeed,)]
		self.feeds.extend([(feed,) for feed in self.rssPoller.feeds])

	def pollCallback(self, id = None):
		print "[SimpleRSS] SimpleRSS called back"
		self.updateInfo()
		self["content"].invalidate()

	def updateInfo(self):
		current_entry = self["content"].getCurrentEntry()
		self["summary"].setText(' '.join([str(len(current_entry.history)), _("Entries")]))
		self["info"].setText(_("Feed %s/%s") % (self["content"].getCurrentIndex()+1, len(self.feeds)))

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
				self.session.openWithCallback(
					self.refresh,
					RSSSetup,
					rssPoller=self.rssPoller
				)
			elif result[1] == "close":
				self.close()

	def refresh(self):
		current_entry = self["content"].getCurrentEntry()

		self.fillFeeds()
		self["content"].l.setList(self.feeds)

		self["content"].moveToEntry(current_entry)
		self.updateInfo()

	def nextFeed(self):
		self["content"].moveUp()
		return (self["content"].getCurrentEntry(), self["content"].getCurrentIndex())

	def previousFeed(self):
		self["content"].moveDown()
		return (self["content"].getCurrentEntry(), self["content"].getCurrentIndex())

	def showCurrentEntry(self):
		current_entry = self["content"].getCurrentEntry()
		self.session.openWithCallback(
			self.updateInfo,
			RSSFeedView,
			feed=current_entry,
			parent=self,
			rssPoller=self.rssPoller,
			id=self["content"].getCurrentIndex()
		)

	def selectEnclosure(self):
		# Build a list of all enclosures in this feed
		enclosures = []
		for entry in self["content"].getCurrentEntry().history:
				enclosures.extend(entry[3])
		RSSBaseView.selectEnclosure(self, enclosures)
