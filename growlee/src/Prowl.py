# -*- coding: utf-8 -*-
from twisted.web.client import getPage
from twisted.internet.defer import Deferred
from twisted.internet import reactor
try:
	from urllib import urlencode
except ImportError as ie:
	from urllib.parse import urlencode

from GrowleeConnection import emergencyDisable
from . import NOTIFICATIONID

class ProwlAPI:
	def __init__(self, host):
		self.enable_outgoing = host.enable_outgoing.value
		self.api_key = host.password.value

	def sendNotification(self, title='No title.', description='No message.', priority=0, timeout=-1):
		if not self.enable_outgoing:
			return

		headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
		data = {
			'apikey': self.api_key,
			'application': "growlee",
			'event': title,
			'description': description,
			'priority': priority,
		}

		getPage('https://prowl.weks.net/publicapi/add/', method = 'POST', headers = headers, postdata = urlencode(data)).addErrback(emergencyDisable)

	def stop(self):
		defer = Deferred()
		reactor.callLater(1, defer.callback, True)
		return defer

