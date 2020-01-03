# -*- coding: utf-8 -*-
from __future__ import print_function
try:
	from urllib import urlencode
except ImportError as ie:
	from urllib.parse import urlencode

from twisted.web.client import getPage
from RSSFeed import UniversalFeed
from twisted.internet.defer import Deferred
from xml.etree.cElementTree import fromstring as cet_fromstring

class GoogleReader:
	def __init__(self, username = None, password = None):
		self.username = username
		self.password = password
		self.token = None
		self.auth = None

	def sendRequest(self, url):
		print("[GoogleReader] sendRequest:", url)
		headers = {
			'Authorization': 'GoogleLogin auth='+self.auth,
		}

		return getPage(url, headers=headers)

	def login(self):
		print("[GoogleReader] login")
		if not self.username or not self.password:
			return

		headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
		data = {
			'service': 'reader',
			'Email': self.username,
			'Passwd': self.password,
			'source': 'enigma2-plugin-extensions-simplerss',
			'continue': 'http://www.google.com/',
		}

		defer = Deferred()
		getPage('https://www.google.com/accounts/ClientLogin', method = 'POST', headers = headers, postdata = urlencode(data)).addCallback(self.loginFinished, defer).addErrback(self.loginFailed, defer)
		return defer

	def loginFinished(self, res = None, defer = None):
		pos_beg = res.find('Auth=')
		pos_end = res.find('\n',pos_beg)
		self.auth = res[pos_beg+5:pos_end]
		if defer:
			defer.callback(self.auth)

	def loginFailed(self, res = None, defer = None):
		print("[GoogleReader] loginFailed:", res)
		if defer:
			# XXX: we might want to give some information here besides "we failed"
			defer.errback()

	def getToken(self):
		if not self.auth:
			return

		defer = Deferred()
		self.sendRequest('http://www.google.com/reader/api/0/token').addCallback(self.gotToken, defer).addErrback(seld.errToken, defer)
		return defer

	def gotToken(self, res = None, defer = None):
		self.token = res
		if defer:
			defer.callback(res)

	def errToken(self, res = None, defer = None):
		print("[GoogleReader] errToken", res)
		self.token = None
		if defer:
			# XXX: we might want to give some information here besides "we failed"
			defer.errback()

	def getSubscriptionList(self):
		if not self.auth:
			return

		defer = Deferred()
		self.sendRequest('http://www.google.com/reader/api/0/subscription/list?output=xml').addCallback(self.gotSubscriptionList, defer).addErrback(self.errSubscriptionList, defer)
		return defer

	def gotSubscriptionList(self, res = None, defer = None):
		l = []
		if res:
			dom = cet_fromstring(res)
			for item in dom.getiterator():
				if item.tag == 'string':
					if item.get('name') == 'id' and item.text.startswith('feed/'):
						l.append(UniversalFeed(item.text[5:], True, True))
		if defer:
			defer.callback(l)

	def errSubscriptionList(self, res = None, defer = None):
		print("[GoogleReader] errSubscriptionList", res)
		if defer:
			# XXX: we might want to give some information here besides "we failed"
			defer.errback()

if __name__ == '__main__':
	from twisted.internet import reactor
	import sys
	Deferred.debug = True

	googleReader = GoogleReader(sys.argv[1], sys.argv[2])
	def googleLoggedIn(sid = None):
		print("Got Token:", sid)
		googleReader.getSubscriptionList().addCallbacks(googleSubscriptionList, errback=googleSubscriptionFailed)

	def googleLoginFailed(res = None):
		print("Failed to login to Google Reader:", str(res))
		reactor.stop()

	def googleSubscriptionList(subscriptions = None):
		print("Got Feeds:", subscriptions)
		reactor.stop()

	def googleSubscriptionFailed(res = None):
		print("Failed to get subscriptions from Google Reader:", str(res))
		reactor.stop()

	googleReader.login().addCallbacks(googleLoggedIn, errback=googleLoginFailed)
	reactor.run()
