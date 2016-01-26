# -*- coding: utf-8 -*-
from __init__ import _

import xmlrpclib

from Components.config import config

# Internal
from Logger import logDebug, logInfo
from TimeoutServerProxy import TimeoutServerProxy


class WebChannels(object):
	def __init__(self):
		
		self.server = TimeoutServerProxy()

	def getWebChannels(self):
		
		logDebug("SerienServer getWebChannels()")
		
		result = self.server.sp.cache.getWebChannels()
		logDebug("SerienServer getWebChannels result:", result)
		
		return result
