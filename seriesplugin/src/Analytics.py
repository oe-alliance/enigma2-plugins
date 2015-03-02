# -*- coding: utf-8 -*-
import socket

from urllib import urlencode
#from urllib import quote_plus
from urllib2 import urlopen, URLError, Request
from urlparse import urlparse as parse   #urlparse module is renamed to urllib.parse in Python 3

from Logger import splog

from Components.config import *

import os, sys

from random import randint
from uuid import uuid1

my_uuid = uuid1()


class Analytics(object):
	def __init__(self):
		socket.setdefaulttimeout(5)
	
	def sendAnalytics(self, url, cached):
		
		if ( config.plugins.seriesplugin.ganalytics.value ):
			
			urlparts = parse(url)
			
			from plugin import VERSION,DEVICE
			parameter = urlencode(
				{
					'version' : VERSION,
					'cached'  : str(cached),
					'device'  : DEVICE
				}
			)
			
			if urlparts.query:
				url = urlparts.path + '?' + urlparts.query + '&' + parameter
			else:
				url = urlparts.path + '?' + parameter
			
			# https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters
			# v   = version 1
			# tid = Tracking ID / Web Property ID
			# aip = anomize ip
			# sc  = session start / end
			# ua  = User Agent
			# dr  = Document Referrer
			# t   = Hit type = 'pageview', 'screenview', 'event', 'transaction', 'item', 'social', 'exception', 'timing'
			# dl  = Document location URL
			# an  = Application Name
			# aid = Application Id
			# av  = Application Version
			# ec  = Event Category
			# ea  = Event Action
			# el  = Event Label
			# ev  = Event Value
			# cm[1-9][0-9]* = Custom Metric
			# z   = cache buster - random number
			#GET
			#http://www.google-analytics.com/collect?v=1&tid=UA-XXXX-Y&aip=1& TBD
			
			global my_uuid
			ua_parameter = urlencode(
				{
					'v'   : '1',
					'tid' : 'UA-31168065-1',
					'cid' : my_uuid,
					'aip' : '1',
					'sc'  : 'start',
					'ua'  : DEVICE + '_' + VERSION,
					't'   : 'pageview',
					'dp'  : url,
					'z'   : randint(1, 99999)
				}
			)
			
			try:
				req = Request( "http://www.google-analytics.com/collect" + '?' + ua_parameter )
				#splog("SP Analytics url: ", req.get_full_url())
				
				response = urlopen(req, timeout=5).read()
				#splog("SP Analytics respond: ", response) 
			
			except URLError as e:
				splog("SP Analytics error code: ", e.code)
				splog("SP Analytics error msg: ", e.msg)
			
			except socket.timeout as e:
				splog("SP Analytics socket timeout")
