from __future__ import print_function
from __future__ import absolute_import

# for localized messages
from . import _

from Components.config import config
from enigma import eTimer

from Tools.Notifications import AddPopup
from Screens.MessageBox import MessageBox

from .RSSFeed import BaseFeed, UniversalFeed

from twisted.web.client import getPage
from xml.etree.cElementTree import fromstring as cElementTree_fromstring
import six

from .GoogleReader import GoogleReader

NOTIFICATIONID = 'SimpleRSSUpdateNotification'

update_callbacks = []

class RSSPoller:
	"""Keeps all Feed and takes care of (automatic) updates"""

	def __init__(self, poll = True):
		# Timer
		self.poll_timer = eTimer()
		self.poll_timer.callback.append(self.poll)
		self.do_poll = poll

		# this indicates we're reloading the list of feeds
		self.reloading = False

		self.newItemFeed = BaseFeed(
			"",
			_("New Items"),
			_("New Items since last Auto-Update"),
		)

		# Generate Feeds
		self.feeds = [
			UniversalFeed(
				x.uri.value,
				x.autoupdate.value
			)
				for x in config.plugins.simpleRSS.feed
		]

		if not config.plugins.simpleRSS.enable_google_reader.value:
			if poll:
				self.poll_timer.start(0, 1)
		else:
			self.googleReader = GoogleReader(config.plugins.simpleRSS.google_username.value, config.plugins.simpleRSS.google_password.value)
			self.googleReader.login().addCallback(self.googleLoggedIn).addErrback(self.googleLoginFailed)

		# Initialize Vars
		self.current_feed = 0

	def googleLoggedIn(self, sid = None):
		self.googleReader.getSubscriptionList().addCallback(self.googleSubscriptionList).addErrback(self.googleSubscriptionFailed)

	def googleLoginFailed(self, res = None):
		AddPopup(
			_("Failed to login to Google Reader."),
			MessageBox.TYPE_ERROR,
			5,
		)

		self.reloading = False
		if self.do_poll:
			self.poll_timer.start(0, 1)

	def googleSubscriptionList(self, subscriptions = None):
		self.feeds.extend(subscriptions)

		self.reloading = False
		if self.do_poll:
			self.doCallback()
			self.poll_timer.start(0, 1)

	def googleSubscriptionFailed(self, res = None):
		AddPopup(
			_("Failed to get subscriptions from Google Reader."),
			MessageBox.TYPE_ERROR,
			5,
		)

		self.reloading = False
		if self.do_poll:
			self.poll_timer.start(0, 1)

	def addCallback(self, callback):
		if callback not in update_callbacks:
			update_callbacks.append(callback)

	def removeCallback(self, callback):
		if callback in update_callbacks:
			update_callbacks.remove(callback)

	def doCallback(self, id = None):
		for callback in update_callbacks:
			try:
				callback(id)
			except Exception:
				pass

	def error(self, error = ""):
		print("[SimpleRSS] failed to fetch feed:", error)

		# Assume its just a temporary failure and jump over to next feed
		self.next_feed()

	def _gotPage(self, data, id = None, callback = False, errorback = None):
		# workaround: exceptions in gotPage-callback were ignored
		try:
			self.gotPage(data, id)
			if callback:
				self.doCallback(id)
		except NotImplementedError as errmsg:
			# Don't show this error when updating in background
			if id is not None:
				AddPopup(
					_("Sorry, this type of feed is unsupported:\n%s") % (str(errmsg)),
					MessageBox.TYPE_INFO,
					5,
				)
			else:
				# We don't want to stop updating just because one feed is broken
				self.next_feed()
		except Exception:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			# Errorback given, call it (asumme we don't need do restart timer!)
			if errorback is not None:
				errorback()
				return
			# Assume its just a temporary failure and jump over to next feed
			self.next_feed()

	def gotPage(self, data, id = None):
		feed = cElementTree_fromstring(data)

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

	def singlePoll(self, id, callback = False, errorback = None):
		getPage(six.ensure_binary(self.feeds[id].uri)).addCallback(self._gotPage, id, callback, errorback).addErrback(errorback)

	def poll(self):
		# Reloading, reschedule
		if self.reloading:
			print("[SimpleRSS] timer triggered while reloading, rescheduling")
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
					from .RSSScreens import RSSFeedView

					from Tools.Notifications import AddNotificationWithID, RemovePopup

					RemovePopup(NOTIFICATIONID)

					AddNotificationWithID(
						NOTIFICATIONID,
						RSSFeedView,
						self.newItemFeed,
						newItems = True
					)
				elif update_notification_value == "notification":
					AddPopup(
						_("Received %d new news item(s).") % (len(self.newItemFeed.history)),
						MessageBox.TYPE_INFO,
						5,
						NOTIFICATIONID
					)
				elif update_notification_value == "ticker":
					from .RSSTickerView import tickerView
					if not tickerView:
						print("[SimpleRSS] missing ticker instance, something with my code is wrong :-/")
					else:
						tickerView.display(self.newItemFeed)
			# No new Items
			else:
				print("[SimpleRSS] no new items")

			self.current_feed = 0
			self.poll_timer.startLongTimer(config.plugins.simpleRSS.interval.value*60)
		# It's updating-time
		else:
			# Assume we're cleaning history if current feed is 0
			clearHistory = self.current_feed == 0
			if config.plugins.simpleRSS.update_notification.value != "none":
				from Tools import Notifications
				if hasattr(Notifications, 'notificationQueue'):
					notifications = Notifications.notificationQueue.queue
					current_notifications = Notifications.notificationQueue.current
					handler = lambda note: (note.fnc, note.screen, note.args, note.kwargs, note.id)
					handler_current = lambda note: (note[0].id,)
				else:
					notifications = Notifications.notifications
					current_notifications = Notifications.current_notifications
					handler_current = handler = lambda note: note

				for x in current_notifications:
					if handler_current(x)[0] == NOTIFICATIONID:
						print("[SimpleRSS] timer triggered while preview on screen, rescheduling")
						self.poll_timer.start(10000, 1)
						return

				if clearHistory:
					for x in notifications:
						if handler(x)[4] == NOTIFICATIONID:
							print("[SimpleRSS] wont wipe history because it was never read")
							clearHistory = False
							break

			if clearHistory:
				del self.newItemFeed.history[:]

			# Feed supposed to autoupdate
			feed = self.feeds[self.current_feed]

			if feed.autoupdate:
				getPage(six.ensure_binary(feed.uri)).addCallback(self._gotPage).addErrback(self.error)
			# Go to next feed
			else:
				print("[SimpleRSS] passing feed")
				self.next_feed()

	def next_feed(self):
		self.current_feed += 1
		self.poll_timer.start(1000, 1)

	def shutdown(self):
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
					newfeeds.append(feed) # Append to new Feeds
					oldfeeds.remove(feed) # Remove from old Feeds
					found = True
					break
			if not found:
				newfeeds.append(
					UniversalFeed(
						x.uri.value,
						x.autoupdate.value
				))
			found = False

		self.feeds = newfeeds

		if config.plugins.simpleRSS.enable_google_reader.value:
			self.googleReader = GoogleReader(config.plugins.simpleRSS.google_username.value, config.plugins.simpleRSS.google_password.value)
			self.googleReader.login().addCallback(self.googleLoggedIn).addErrback(self.googleLoginFailed)
		else:
			self.reloading = False

