from Screens.MessageBox import MessageBox
from Components.config import config
from enigma import eTimer

from RSSScreens import RSSFeedView
from TagStrip import TagStrip
from RSSFeed import UniversalFeed

from httpclient import getPage
from xml.dom.minidom import parseString as minidom_parseString

class RSSPoller:
	"""Keeps all Feed and takes care of (automatic) updates"""
	def __init__(self, session):
		# Timer
		self.poll_timer = eTimer()
		self.poll_timer.timeout.get().append(self.poll)
		self.poll_timer.start(0, 1)

		# Stripper
		self.stripper = TagStrip()

		# Functions to call when updates happened
		self.update_callbacks = [ ]

		# Save Session, Initialize Var to identify triggered Reload
		self.session = session
		self.reloading = False

		# Generate Feeds
		self.feeds = [
			UniversalFeed(
				config.plugins.simpleRSS.feed[i].uri.value,
				config.plugins.simpleRSS.feed[i].autoupdate.value,
				self.stripper
			)
				for i in range(0, config.plugins.simpleRSS.feedcount.value)
		]

		# Initialize Vars
		self.new_items = [ ]
		self.current_feed = 0

	def addCallback(self, callback):
		if callback not in self.update_callbacks:
			self.update_callbacks.append(callback)

	def removeCallback(self, callback):
		if callback in self.update_callbacks:
			self.update_callbacks.remove(callback)

	def doCallback(self, id = None):
		for callback in self.update_callbacks:
			try:
				callback(id)
			except:
				pass

	# Wrap boundFunction over real function
	def _gotSinglePage(self, id, callback, errorback, data):
		self._gotPage(data, id, callback, errorback)

	def error(self, error = ""):
		if not self.session:
			print "[SimpleRSS] error polling"
		else:
			self.session.open(
				MessageBox,
				"Sorry, failed to fetch feed.\n" + error,
				type = MessageBox.TYPE_INFO,
				timeout = 5
			)
			# Assume its just a temporary failure and jump over to next feed                          
			self.next_feed()

	def _gotPage(self, data, id = None, callback = False, errorback = None):
		# workaround: exceptions in gotPage-callback were ignored
		try:
			self.gotPage(data, id)
			if callback:
				self.doCallback(id)
		except NotImplementedError, errmsg:
			# TODO: Annoying with Multifeed?
			self.session.open(
				MessageBox,
				"Sorry, this type of feed is unsupported.\n"+ str(errmsg),
				type = MessageBox.TYPE_INFO,
				timeout = 5
			)
		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			# Errorback given, call it (asumme we don't need do restart timer!)
			if errorback is not None:
				errorback()
				return
			# Assume its just a temporary failure and jump over to next feed                          
			self.next_feed()
	
	def gotPage(self, data, id = None):
		print "[SimpleRSS] parsing.."

		# sometimes activates spinner :-/
		dom = minidom_parseString(data)

		print "[SimpleRSS] xml parsed.."

		# For Single-Polling
		if id is not None:
			self.feeds[id].gotDom(dom)
			print "[SimpleRSS] single feed parsed.."
			return

		new_items = self.feeds[self.current_feed].gotDom(dom)

		print "[SimpleRSS] feed parsed.."

		# Append new items to locally bound ones
		self.new_items.extend(new_items)

		# Start Timer so we can either fetch next feed or show new_items
		self.next_feed()

	def singlePoll(self, id, callback = False, errorback = None):
		from Tools.BoundFunction import boundFunction
		getPage(
			self.feeds[id].hostname,
			self.feeds[id].port,
			self.feeds[id].path,
			callback=boundFunction(self._gotSinglePage, id, callback, errorback),
			errorback=errorback
		)

	def poll(self):
		# Reloading, reschedule
		if self.reloading:
			print "[SimpleRSS] timer triggered while reloading, rescheduling"
			self.poll_timer.start(10000, 1)
		# End of List
		elif len(self.feeds) <= self.current_feed:
			# New Items
			if len(self.new_items):
				print "[SimpleRSS] got", len(self.new_items), "new items"
				print "[SimpleRSS] calling back"
				self.doCallback()
				# Inform User
				if config.plugins.simpleRSS.show_new.value:
					self.session.open(RSSFeedView, self.new_items, newItems=True)
			# No new Items
			else:
				print "[SimpleRSS] no new items"
			self.current_feed = 0
			self.poll_timer.startLongTimer(config.plugins.simpleRSS.interval.value*60)
		# It's updating-time
		else:
			# Id is 0 -> empty out new items
			if self.current_feed == 0:
				self.new_items = [ ]
			# Feed supposed to autoupdate
			feed = self.feeds[self.current_feed]
			if feed.autoupdate:
				getPage(
					feed.hostname,
					feed.port,
					feed.path,
					callback=self._gotPage,
					errorback=self.error
				)
			# Go to next feed
			else:
				print "[SimpleRSS] passing feed"
				self.next_feed()

	def next_feed(self):
		self.current_feed += 1
		self.poll_timer.start(1000, 1)

	def shutdown(self):
		self.poll_timer.timeout.get().remove(self.poll)
		self.poll_timer = None

	def triggerReload(self):
		self.reloading = True

		newfeeds = []
		found = False
		for i in range(0, config.plugins.simpleRSS.feedcount.value):
			for feed in self.feeds:
				if config.plugins.simpleRSS.feed[i].uri.value == feed.uri:
					# Update possibly different autoupdate value
					feed.autoupdate = config.plugins.simpleRSS.feed[i].autoupdate.value
					newfeeds.append(feed) # Append to new Feeds
					self.feeds.remove(feed) # Remove from old Feeds
					found = True
					break
			if not found:
				newfeeds.append(
					UniversalFeed(
						config.plugins.simpleRSS.feed[i].uri.value,
						config.plugins.simpleRSS.feed[i].autoupdate.value,
						self.stripper
				))
			found = False

		self.feeds = newfeeds

		self.reloading = False