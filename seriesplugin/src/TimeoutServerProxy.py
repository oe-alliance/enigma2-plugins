# -*- coding: utf-8 -*-
# by http://stackoverflow.com/questions/372365/set-timeout-for-xmlrpclib-serverproxy

import xmlrpclib
import httplib
import socket

from Components.config import config


class TimeoutServerProxy(xmlrpclib.ServerProxy):
	def __init__(self, *args, **kwargs):
		
		from Plugins.Extensions.SeriesPlugin.plugin import REQUEST_PARAMETER
		uri = config.plugins.seriesplugin.serienserver_url.value + REQUEST_PARAMETER
		
		timeout = config.plugins.seriesplugin.socket_timeout.value		# socket._GLOBAL_DEFAULT_TIMEOUT or None
		
		xmlrpclib.ServerProxy.__init__(self, uri, verbose=False, *args, **kwargs)
		
		socket.setdefaulttimeout( float(timeout) ) 
