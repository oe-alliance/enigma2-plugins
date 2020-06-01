# -*- coding: utf-8 -*-
# by http://stackoverflow.com/questions/372365/set-timeout-for-xmlrpc_client-serverproxy

import socket

from time import time

from Components.config import config

# Internal
from Logger import log


from six.moves import xmlrpc_client


skip_expiration = 5.0 * 60 	# in seconds
reduced_timeout = 3.0		# in seconds


class TimeoutServerProxy(xmlrpc_client.ServerProxy):
	def __init__(self, *args, **kwargs):
		
		from Plugins.Extensions.SeriesPlugin.plugin import REQUEST_PARAMETER
		uri = config.plugins.seriesplugin.serienserver_url.value + REQUEST_PARAMETER
		
		xmlrpc_client.ServerProxy.__init__(self, uri, verbose=False, *args, **kwargs)
		
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
		
		try:
			result = self.sp.cache.getSeasonEpisode( name, webChannel, unixtime, max_time_drift )
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
