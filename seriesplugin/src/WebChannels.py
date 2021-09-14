# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .__init__ import _

from Components.config import config

# Internal
from .Logger import log
from .TimeoutServerProxy import TimeoutServerProxy


class WebChannels(object):
	def __init__(self):

		self.server = TimeoutServerProxy()

	def getWebChannels(self):

		log.debug("SerienServer getWebChannels()")

		result = self.server.getWebChannels()
		log.debug("SerienServer getWebChannels result:", result)

		return result
