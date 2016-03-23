# -*- coding: utf-8 -*-
# by http://stackoverflow.com/questions/372365/set-timeout-for-xmlrpclib-serverproxy

import xmlrpclib
import socket

from time import time

from Components.config import config

# Internal
from Logger import log


from twisted.internet import reactor, defer
from twisted.python import failure
from threading import currentThread
import Queue

def blockingCallFromMainThread(f, *a, **kw):
	"""
	  Modified version of twisted.internet.threads.blockingCallFromThread
	  which waits 30s for results and otherwise assumes the system to be shut down.
	  This is an ugly workaround for a twisted-internal deadlock.
	  Please keep the look intact in case someone comes up with a way
	  to reliably detect from the outside if twisted is currently shutting
	  down.
	"""
	queue = Queue.Queue()
	def _callFromThread():
		result = defer.maybeDeferred(f, *a, **kw)
		result.addBoth(queue.put)
	reactor.callFromThread(_callFromThread)

	result = None
	while True:
		try:
			result = queue.get(True, int(config.plugins.seriesplugin.socket_timeout.value) + 3)
		except Queue.Empty as qe:
			if True: #not reactor.running: # reactor.running is only False AFTER shutdown, we are during.
				log.warning("Reactor no longer active, aborting.")
		else:
			break

	if isinstance(result, failure.Failure):
		result.raiseException()
	return result


skip_expiration = 5.0 * 60 	# in seconds
reduced_timeout = 3.0		# in seconds


class TimeoutServerProxy(xmlrpclib.ServerProxy):
	def __init__(self, *args, **kwargs):
		
		from Plugins.Extensions.SeriesPlugin.plugin import REQUEST_PARAMETER
		uri = config.plugins.seriesplugin.serienserver_url.value + REQUEST_PARAMETER
		
		xmlrpclib.ServerProxy.__init__(self, uri, verbose=False, *args, **kwargs)
		
		timeout = config.plugins.seriesplugin.socket_timeout.value
		socket.setdefaulttimeout( float(timeout) )
		
		self.skip = {}

	def getWebChannels(self):
		result = None
		try:
			result = self.sp.cache.getWebChannels()
		except Exception as e:
			log.exception("Exception in xmlrpc: " + str(e) + ' - ' + str(result))
		return result

	def getSeasonEpisode( self, name, webChannel, unixtime, max_time_drift ):
		result = None
		
		skipped = self.skip.get(name, None)
		if skipped:
			if ( time() - skipped ) < skip_expiration:
				#return _("Skipped")
				socket.setdefaulttimeout( reduced_timeout )
			else:
				del self.skip[name]
		
		if currentThread().getName() == 'MainThread':
			doBlockingCallFromMainThread = lambda f, *a, **kw: f(*a, **kw)
		else:
			doBlockingCallFromMainThread = blockingCallFromMainThread
		
		try:
			#result = self.sp.cache.getSeasonEpisode( name, webChannel, unixtime, max_time_drift )
			result = doBlockingCallFromMainThread( self.sp.cache.getSeasonEpisode, name, webChannel, unixtime, max_time_drift )
			log.debug("SerienServer getSeasonEpisode result:", result)
		except Exception as e:
			msg = "Exception in xmlrpc: \n" + str(e) + ' - ' + str(result) + "\n\nfor" + name + " (" + webChannel + ")"
			if not config.plugins.seriesplugin.autotimer_independent.value:
				log.exception(msg)
			else:
				# The independant mode could have a lot of non series entries
				log.debug(msg)
			self.skip[name] = time()
			result = str(e)
		
		if skipped:
			timeout = config.plugins.seriesplugin.socket_timeout.value
			socket.setdefaulttimeout( float(timeout) )
		
		return result
