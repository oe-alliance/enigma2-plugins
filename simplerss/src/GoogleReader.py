import urllib
from twisted.web.client import getPage
from RSSFeed import UniversalFeed
from twisted.internet.defer import Deferred
from xml.etree.cElementTree import fromstring as cet_fromstring

class GoogleReader:
	def __init__(self, username = None, password = None):
		self.username = username
		self.password = password
		self.token = None
		self.sid = None

	def sendRequest(self, url):
		print "[GoogleReader] sendRequest:", url
		cookies = {
			'Name': 'SID',
			'SID': self.sid,
			'Domain': '.google.com',
			'Path': '/',
			'Expires': '160000000000'
		}

		return getPage(url, cookies = cookies)

	def login(self):
		print "[GoogleReader] login"
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
		getPage('https://www.google.com/accounts/ClientLogin', method = 'POST', headers = headers, postdata = urllib.urlencode(data)).addCallback(self.loginFinished, defer).addErrback(self.loginFailed, defer)
		return defer

	def loginFinished(self, res = None, defer = None):
		print "[GoogleReader] loginFinished:", res
		pos_beg = res.find('SID=')
		pos_end = res.find('\n',pos_beg)
		self.sid = res[pos_beg+4:pos_end]
		if defer:
			defer.callback(self.sid)

	def loginFailed(self, res = None, defer = None):
		print "[GoogleReader] loginFailed:", res
		if defer:
			# XXX: we might want to give some information here besides "we failed"
			defer.errback()

	def getToken(self):
		print "[GoogleReader] getToken"
		if not self.sid:
			return

		defer = Deferred()
		self.sendRequest('http://www.google.com/reader/api/0/token').addCallback(self.gotToken, defer).addErrback(seld.errToken, defer)
		return defer

	def gotToken(self, res = None, defer = None):
		print "[GoogleReader] gotToken", res
		self.token = res
		if defer:
			defer.callback(res)

	def errToken(self, res = None, defer = None):
		print "[GoogleReader] errToken", res
		self.token = None
		if defer:
			# XXX: we might want to give some information here besides "we failed"
			defer.errback()

	def getSubscriptionList(self):
		print "[GoogleReader] getSubscriptionList"
		if not self.sid:
			return

		defer = Deferred()
		self.sendRequest('http://www.google.com/reader/api/0/subscription/list').addCallback(self.gotSubscriptionList, defer).addErrback(self.errSubscriptionList, defer)
		return defer

	def gotSubscriptionList(self, res = None, defer = None):
		print "[GoogleReader] gotSubscriptionList", res
		l = []
		if res:
			dom = cet_fromstring(res)
			for item in dom.getiterator():
				if item.tag == 'string':
					if item.get('name') == 'id':
						l.append(UniversalFeed(item.text[5:], True, True))
		if defer:
			defer.callback(l)

	def errSubscriptionList(self, res = None, defer = None):
		print "[GoogleReader] errSubscriptionList", res
		if defer:
			# XXX: we might want to give some information here besides "we failed"
			defer.errback()

