from twisted.web.client import getPage
from twisted.internet.defer import Deferred
from twisted.internet import reactor
from urllib import urlencode

from Components.config import config

from GrowleeConnection import emergencyDisable
from . import NOTIFICATIONID

class ProwlAPI:
	def sendNotification(self, title='No title.', description='No message.', priority=0, timeout=-1):
		if not config.plugins.growlee.enable_outgoing.value:
			return

		headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
		data = {
			'apikey': config.plugins.growlee.prowl_api_key.value,
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

