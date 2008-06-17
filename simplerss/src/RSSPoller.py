from Components.config import config
from enigma import eTimer

from RSSFeed import BaseFeed, UniversalFeed

from twisted.web.client import getPage
from xml.dom.minidom import parseString as minidom_parseString

NOTIFICATIONID = 'SimpleRSSUpdateNotification'

class RSSPoller:
	"""Keeps all Feed and takes care of (automatic) updates"""

	def __init__(self, session, poll = True):
		# Timer
		self.poll_timer = eTimer()
		self.poll_timer.callback.append(self.poll)
		if poll:
			self.poll_timer.start(0, 1)

		# Functions to call when updates happened
		self.update_callbacks = [ ]

		# Save Session, Initialize Var to identify triggered Reload
		self.session = session
		self.reloading = False

		self.newItemFeed = BaseFeed(
			"",
			False,
			_("New Items"),
			_("New Items since last Auto-Update"),
		)

		# Generate Feeds
		self.feeds = [
			UniversalFeed(
				config.plugins.simpleRSS.feed[i].uri.value,
				config.plugins.simpleRSS.feed[i].autoupdate.value
			)
				for i in range(0, config.plugins.simpleRSS.feedcount.value)
		]

		# Initialize Vars
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

	def error(self, error = ""):
		print "[SimpleRSS] failed to fetch feed:", error 

		# Assume its just a temporary failure and jump over to next feed                          
		self.next_feed()

	def _gotPage(self, data, id = None, callback = False, errorback = None):
		# workaround: exceptions in gotPage-callback were ignored
		try:
			self.gotPage(data, id)
			if callback:
				self.doCallback(id)
		except NotImplementedError, errmsg:
			# Don't show this error when updating in background
			if id is not None:
				from Screens.MessageBox import MessageBox

				self.session.open(
					MessageBox,
					_("Sorry, this type of feed is unsupported:\n%s") % (str(errmsg)),
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
		if new_items is not None:
			self.newItemFeed.history.extend(new_items)

		# Start Timer so we can either fetch next feed or show new_items
		self.next_feed()

	def singlePoll(self, id, callback = False, errorback = None):
		getPage(self.feeds[id].uri).addCallback(self._gotPage, id, callback, errorback).addErrback(errorback)

	def poll(self):
		# Reloading, reschedule
		if self.reloading:
			print "[SimpleRSS] timer triggered while reloading, rescheduling"
			self.poll_timer.start(10000, 1)
		# End of List
		elif len(self.feeds) <= self.current_feed:
			# New Items
			if len(self.newItemFeed.history):
				print "[SimpleRSS] got new items, calling back"
				self.doCallback()

				# Inform User
				if config.plugins.simpleRSS.update_notification.value == "preview":
					from RSSScreens import RSSFeedView

					from Tools.Notifications import AddNotificationWithID, RemovePopup

					RemovePopup(NOTIFICATIONID)

					AddNotificationWithID(
						NOTIFICATIONID,
						RSSFeedView,
						self.newItemFeed,
						newItems = True
					)
				elif config.plugins.simpleRSS.update_notification.value == "notification":
					from Tools.Notifications import AddPopup
					from Screens.MessageBox import MessageBox

					AddPopup(
						_("Received %d new news item(s).") % (len(self.newItemFeed.history)),
						MessageBox.TYPE_INFO,
						5,
						NOTIFICATIONID
					)
			# No new Items
			else:
				print "[SimpleRSS] no new items"

			self.current_feed = 0
			self.poll_timer.startLongTimer(config.plugins.simpleRSS.interval.value*60)
		# It's updating-time
		else:
			# Assume we're cleaning history if current feed is 0
			clearHistory = self.current_feed == 0
			if config.plugins.simpleRSS.update_notification.value != "none":
				from Tools.Notifications import current_notifications, notifications
				for x in current_notifications:
					if x[0] == NOTIFICATIONID:
						print "[SimpleRSS] timer triggered while preview on screen, rescheduling"
						self.poll_timer.start(10000, 1)
						return

				if clearHistory:
					for x in notifications:
						if x[4] and x[4] == NOTIFICATIONID:
							print "[SimpleRSS] wont wipe history because it was never read"
							clearHistory = False
							break

			if clearHistory:
				del self.newItemFeed.history[:]

			# Feed supposed to autoupdate
			feed = self.feeds[self.current_feed]

			if feed.autoupdate:
				getPage(feed.uri).addCallback(self._gotPage).addErrback(self.error)
			# Go to next feed
			else:
				print "[SimpleRSS] passing feed"
				self.next_feed()

	def next_feed(self):
		self.current_feed += 1
		self.poll_timer.start(1000, 1)

	def shutdown(self):
		self.poll_timer.callback.remove(self.poll)
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
						config.plugins.simpleRSS.feed[i].autoupdate.value
				))
			found = False

		self.feeds = newfeeds

		self.reloading = False
