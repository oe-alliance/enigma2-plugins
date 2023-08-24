# PYTHON IMPORTS
from requests import get, exceptions
from six import ensure_str, ensure_binary
from sys import stdout
from traceback import print_exc
from xml.etree.cElementTree import fromstring

# ENIGMA IMPORTS
from enigma import eTimer
from Components.config import config
from Screens.MessageBox import MessageBox
from Tools import Notifications
from Tools.Notifications import AddPopup, AddNotificationWithID, RemovePopup

# PLUGIN IMPORTS
from . import _  # for localized messages
from .RSSFeed import BaseFeed, UniversalFeed
from .RSSScreens import RSSFeedView
from .RSSTickerView import tickerView

MODULE_NAME = __name__.split(".")[-1]
NOTIFICATIONID = 'SimpleRSSUpdateNotification'
update_callbacks = []


class RSSPoller:
	"""Keeps all Feed and takes care of (automatic) updates"""

	def __init__(self, poll=True):
		# Timer
		self.poll_timer = eTimer()
		self.poll_timer.callback.append(self.poll)
		self.do_poll = poll
		# this indicates we're reloading the list of feeds
		self.reloading = False
		self.newItemFeed = BaseFeed("", _("New Items"), _("New Items since last Auto-Update"),)
		# Generate Feeds
		self.feeds = [UniversalFeed(x.uri.value, x.autoupdate.value) for x in config.plugins.simpleRSS.feed]
		if poll and self.poll_timer:
			self.poll_timer.start(0, 1)
		# Initialize Vars
		self.current_feed = 0

	def addCallback(self, callback):
		if callback not in update_callbacks:
			update_callbacks.append(callback)

	def removeCallback(self, callback):
		if callback in update_callbacks:
			update_callbacks.remove(callback)

	def doCallback(self, id=None):
		for callback in update_callbacks:
			try:
				callback(id)
			except Exception:
				pass

	def error(self, error=""):
		print("[SimpleRSS] failed to fetch feed:", error)
		# Assume its just a temporary failure and jump over to next feed
		self.next_feed()

	def _gotPage(self, id=None, callback=False, errorback=None, data=None):
		# workaround: exceptions in gotPage-callback were ignored
		try:
			self.gotPage(data, id)
			if callback:
				self.doCallback(id)
		except NotImplementedError as errmsg:
			# Don't show this error when updating in background
			if id is not None:
				AddPopup(_("Sorry, this type of feed is unsupported:\n%s") % str(errmsg), MessageBox.TYPE_INFO, 5,)
			else:
				# We don't want to stop updating just because one feed is broken
				self.next_feed()
		except Exception:
			print_exc(file=stdout)
			# Errorback given, call it (asumme we don't need do restart timer!)
			if errorback is not None:
				errorback()
				return
			# Assume its just a temporary failure and jump over to next feed
			self.next_feed()

	def singlePoll(self, feedid, errorback=None):
		self.pollXml(self.feeds[feedid].uri, errorback)

	def pollXml(self, feeduri, errorback=None):
		headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0", "Accept": "text/xml"}
		if feeduri:
			response = get
			try:
				response = get(ensure_binary(feeduri), headers=headers, timeout=(3.05, 6))
				response.raise_for_status()
			except exceptions.RequestException as err:
				print("[%s] ERROR in module 'pollXml': '%s" % (MODULE_NAME, str(err)))
				if errorback:
					errorback(str(err))
			try:
				xmlData = response.content
				if xmlData:
					self.gotPage(xmlData)
				print("[%s] ERROR in module 'pollXml': server access failed." % MODULE_NAME)
			except Exception as err:
				print("[%s] ERROR in module 'pollXml': invalid json data from server. %s" % (MODULE_NAME, str(err)))
		else:
			print("[%s] ERROR in module 'pollXml': missing link." % MODULE_NAME)

	def gotPage(self, data, id=None):
		feed = fromstring(ensure_str(data))
		# For Single-Polling
		if id is not None:
			self.feeds[id].gotFeed(feed)
			print("[SimpleRSS] single feed parsed...")
			return
		new_items = self.feeds[self.current_feed].gotFeed(feed)
		print("[SimpleRSS] feed parsed...")
		# Append new items to locally bound ones
		if new_items is not None:
			self.newItemFeed.history.extend(new_items)
		# Start Timer so we can either fetch next feed or show new_items
		self.next_feed()

	def poll(self):
		# Reloading, reschedule
		if self.reloading:
			print("[SimpleRSS] timer triggered while reloading, rescheduling")
			if self.poll_timer:
				self.poll_timer.start(10000, 1)
		# End of List
		elif len(self.feeds) <= self.current_feed:
			# New Items
			if self.newItemFeed.history:
				print("[SimpleRSS] got new items, calling back")
				self.doCallback()
				# Inform User
				update_notification_value = config.plugins.simpleRSS.update_notification.value
				if update_notification_value == "preview":
					RemovePopup(NOTIFICATIONID)
					AddNotificationWithID(NOTIFICATIONID, RSSFeedView, self.newItemFeed, newItems=True)
				elif update_notification_value == "notification":
					AddPopup(_("Received %d new news item(s).") % (len(self.newItemFeed.history)), MessageBox.TYPE_INFO, 5, NOTIFICATIONID)
				elif update_notification_value == "ticker":
					if not tickerView:
						print("[SimpleRSS] missing ticker instance, something with my code is wrong :-/")
					else:
						tickerView.display(self.newItemFeed)
			# No new Items
			else:
				print("[SimpleRSS] no new items")
			self.current_feed = 0
			if self.poll_timer:
				self.poll_timer.startLongTimer(config.plugins.simpleRSS.interval.value * 60)
		# It's updating-time
		else:
			# Assume we're cleaning history if current feed is 0
			clearHistory = self.current_feed == 0
			if config.plugins.simpleRSS.update_notification.value != "none":
				if hasattr(Notifications.notifications, 'Notifications.notificationQueue'):
					Xnotifications = Notifications.notificationQueue.queue
					Xcurrent_notifications = Notifications.notificationQueue.current
					handler = lambda note: (note.fnc, note.screen, note.args, note.kwargs, note.id)
					handler_current = lambda note: (note[0].id,)
				else:
					Xnotifications = Notifications.notifications
					Xcurrent_notifications = Notifications.current_notifications
					handler_current = handler = lambda note: note
				for x in Xcurrent_notifications:
					if handler_current(x)[0] == NOTIFICATIONID:
						print("[SimpleRSS] timer triggered while preview on screen, rescheduling")
						if self.poll_timer:
							self.poll_timer.start(10000, 1)
				if clearHistory:
					for x in Xnotifications:
						if handler(x)[4] == NOTIFICATIONID:
							print("[SimpleRSS] wont wipe history because it was never read")
							clearHistory = False
							break
			if clearHistory:
				del self.newItemFeed.history[:]
			# Feed supposed to autoupdate
			feed = self.feeds[self.current_feed]
			if feed.autoupdate:
				self.pollXml(feed.uri, self.error)
			# Go to next feed
			else:
				print("[SimpleRSS] passing feed sucessfully")
				self.next_feed()

	def next_feed(self):
		self.current_feed += 1
		if self.poll_timer:
			self.poll_timer.start(1000, 1)

	def shutdown(self):
		if self.poll_timer:
			self.poll_timer.callback.remove(self.poll)
			self.poll_timer = None
			self.do_poll = False

	def triggerReload(self):
		self.reloading = True
		newfeeds = []
		oldfeeds = self.feeds
		found = False
		for x in config.plugins.simpleRSS.feed:
			for feed in oldfeeds:
				if x.uri.value == feed.uri:
					# Update possibly different autoupdate value
					feed.autoupdate = x.autoupdate.value
					newfeeds.append(feed)  # Append to new Feeds
					oldfeeds.remove(feed)  # Remove from old Feeds
					found = True
					break
			if not found:
				newfeeds.append(UniversalFeed(x.uri.value, x.autoupdate.value))
			found = False
		self.feeds = newfeeds
		self.reloading = False
