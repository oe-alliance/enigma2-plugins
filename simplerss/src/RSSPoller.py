from Screens.MessageBox import MessageBox
from Components.config import config
from enigma import eTimer

from SimpleRSSScreens import SimpleRSSFeed
from TagStrip import TagStrip
from Feed import Feed

from httpclient import getPage
from urlparse import urlsplit
from xml.dom.minidom import parseString as minidom_parseString

class RSSPoller:
	def __init__(self, session):
		self.poll_timer = eTimer()
		self.poll_timer.timeout.get().append(self.poll)
		self.poll_timer.start(0, 1)

		self.stripper = TagStrip()

		self.update_callbacks = [ ]
		self.session = session
		self.dialog = None
		self.reloading = False
	
		self.feeds = [ ]
		for i in range(0, config.plugins.simpleRSS.feedcount.value):
			self.feeds.append(Feed(config.plugins.simpleRSS.feed[i].uri.value, config.plugins.simpleRSS.feed[i].autoupdate.value, self.stripper))
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
			self.session.open(MessageBox, "Sorry, failed to fetch feed.\n" + error, type = MessageBox.TYPE_INFO, timeout = 5)
			# Assume its just a temporary failure and jump over to next feed                          
			self.current_feed += 1                     
			self.poll_timer.start(1000, 1)

	def _gotPage(self, data, id = None, callback = False, errorback = None):
		# workaround: exceptions in gotPage-callback were ignored
		try:
			self.gotPage(data, id)
			if callback:
				self.doCallback(id)
		except NotImplementedError, errmsg:
			# TODO: Annoying with Multifeed?
			self.session.open(MessageBox, "Sorry, this type of feed is unsupported.\n"+ str(errmsg), type = MessageBox.TYPE_INFO, timeout = 5)
		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			# Errorback given, call it (asumme we don't need do restart timer!)
			if errorback is not None:
				errorback()
				return
			# Assume its just a temporary failure and jump over to next feed                          
			self.current_feed += 1                     
			self.poll_timer.start(1000, 1)
	
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
		else:
			new_items = self.feeds[self.current_feed].gotDom(dom)

		print "[SimpleRSS] feed parsed.."

		# Append new items to locally bound ones
		self.new_items.extend(new_items)

		# Start Timer so we can either fetch next feed or show new_items
		self.current_feed += 1
		self.poll_timer.start(1000, 1)

	def singlePoll(self, id, callback = False, errorback = None):
		from Tools.BoundFunction import boundFunction
		remote = urlsplit(self.feeds[id].uri)
		print "[SimpleRSS] updating", remote.geturl()
		hostname = remote.hostname
		port = remote.port or 80
		path = '?'.join([remote.path, remote.query])
		print "[SimpleRSS] hostname:", hostname, ", port:", port, ", path:", path
		getPage(hostname, port, path, callback=boundFunction(self._gotSinglePage, id, callback, errorback), errorback=errorback)

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
					self.dialog = self.session.instantiateDialog(SimpleRSSFeed, self.new_items, newItems=True)
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
			newfeeds.append(Feed(config.plugins.simpleRSS.feed[i].uri.value, config.plugins.simpleRSS.feed[i].autoupdate.value, self.stripper))

		self.feeds = newfeeds

		self.reloading = False