# -*- coding: utf-8 -*-
from __future__ import absolute_import
from requests import get, exceptions
from six.moves.urllib.parse import urlencode
from twisted.internet.reactor import callInThread
from Tools.BoundFunction import boundFunction
from .GrowleeConnection import emergencyDisable


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
		callInThread(self.threadGetPage, boundFunction(b'https://prowl.weks.net/publicapi/add/', method='POST', headers=headers, postdata=urlencode(data)), emergencyDisable)

	def threadGetPage(self, link, fail=None):
		link = link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', '')
		try:
			response = get(link)
			response.raise_for_status()
		except exceptions.RequestException as error:
			if fail is not None:
				fail(error)

	def stop(self):
		defer = Deferred()
		reactor.callLater(1, defer.callback, True)
		return defer
