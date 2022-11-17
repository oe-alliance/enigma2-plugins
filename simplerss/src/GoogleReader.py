# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
from requests import get, exceptions
from six import ensure_binary
from six.moves.urllib.parse import urlencode
from twisted.internet.defer import Deferred
from twisted.internet.reactor import callInThread
from xml.etree.cElementTree import fromstring as cet_fromstring
from Tools.BoundFunction import boundFunction
from .RSSFeed import UniversalFeed


class GoogleReader:
	def __init__(self, username=None, password=None):
		self.username = ensure_binary(username)
		self.password = ensure_binary(password)
		self.token = None
		self.auth = None

	def sendRequest(self, url):
		print("[GoogleReader] sendRequest:", url)
		headers = {'Authorization': 'GoogleLogin auth=%s' % self.auth}
		callInThread(self.threadGetPage, boundFunction(url, headers=headers))

	def threadGetPage(self, link):
		link = ensure_binary(link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', ''))
		try:
			response = get(ensure_binary(link))
			response.raise_for_status()
			return response.content
		except exceptions.RequestException as error:
			return error

	def login(self):
		print("[GoogleReader] login")
		if not self.username or not self.password:
			return Deferred()

		headers = {b'Content-Type': b'application/x-www-form-urlencoded; charset=utf-8'}
		data = {
        	b'service': b'reader',
			b'Email': self.username,
			b'Passwd': self.password,
			b'source': b'enigma2-plugin-extensions-simplerss',
			b'continue': b'http://www.google.com/',
		}

		defer = Deferred()
		callInThread(self.threadGetPage, boundFunction(b'https://www.google.com/accounts/ClientLogin', method=b'POST', headers=headers, postdata=urlencode(data)), boundFunction(self.loginFinished, defer), boundFunction(self.loginFailed, defer))
		return defer

	def loginFinished(self, res=None, defer=None):
		pos_beg = res.find('Auth=')
		pos_end = res.find('\n', pos_beg)
		self.auth = res[pos_beg + 5:pos_end]
		if defer:
			defer.callback(self.auth)

	def loginFailed(self, res=None, defer=None):
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

	def gotToken(self, res=None, defer=None):
		self.token = res
		if defer:
			defer.callback(res)

	def errToken(self, res=None, defer=None):
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

	def gotSubscriptionList(self, res=None, defer=None):
		l = []
		if res:
			dom = cet_fromstring(res)
			for item in dom.getiterator():
				if item.tag == 'string':
					if item.get('name') == 'id' and item.text.startswith('feed/'):
						l.append(UniversalFeed(item.text[5:], True, True))
		if defer:
			defer.callback(l)

	def errSubscriptionList(self, res=None, defer=None):
		print("[GoogleReader] errSubscriptionList", res)
		if defer:
			# XXX: we might want to give some information here besides "we failed"
			defer.errback()


if __name__ == '__main__':
	from twisted.internet.reactor import stop as reactorstop, run as reactorrun
	import sys
	Deferred.debug = True

	googleReader = GoogleReader(sys.argv[1], sys.argv[2])

	def googleLoggedIn(sid=None):
		print("Got Token:", sid)
		googleReader.getSubscriptionList().addCallbacks(googleSubscriptionList, errback=googleSubscriptionFailed)

	def googleLoginFailed(res=None):
		print("Failed to login to Google Reader:", str(res))
		reactorstop()

	def googleSubscriptionList(subscriptions=None):
		print("Got Feeds:", subscriptions)
		reactorstop()

	def googleSubscriptionFailed(res=None):
		print("Failed to get subscriptions from Google Reader:", str(res))
		reactorstop()

	googleReader.login().addCallbacks(googleLoggedIn, errback=googleLoginFailed)
	reactorrun()
