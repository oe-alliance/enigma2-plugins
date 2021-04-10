# -*- coding: utf-8 -*-
#######################################################################
#
#    Series Plugin for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=TBD
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

import sys
from time import time

from Components.config import *

from Logger import log


# Global cache
# Do we have to cleanup it
cache = {}


def clearCache():
	global cache
	cache = {}


class Cacher(object):
	def __init__(self):
		# This dict structure will be the following:
		# { 'URL': (TIMESTAMP, value) }
		#self.cache = {}
		#global cache
		#cache = {}

		# Max Age (in seconds) of each feed in the cache
		self.expiration = config.plugins.seriesplugin.caching_expiration.value * 60 * 60

	def getCached(self, url):
		#pullCache
		global cache

		if not config.plugins.seriesplugin.caching.value:
			return

		# Try to get the tuple (TIMESTAMP, FEED_STRUCT) from the dict if it has
		# already been downloaded. Otherwise assign None to already_got
		already_got = cache.get(url, None)

		# Ok guys, we got it cached, let's see what we will do
		if already_got:
			# Well, it's cached, but will it be recent enough?
			elapsed_time = time() - already_got[0]

			# Woooohooo it is, elapsed_time is less than INTER_QUERY_TIME so I
			# can get the page from the memory, recent enough
			if elapsed_time < self.expiration:
				#log.debug("####SPCACHE GET ", already_got)
				return already_got[1]

			else:
				# Uhmmm... actually it's a bit old, I'm going to get it from the
				# Net then, then I'll parse it and then I'll try to memoize it
				# again
				return None

		else:
			# Well... We hadn't it cached in, so we need to get it from the Net
			# now, It's useless to check if it's recent enough, it's not there.
			return None

	def doCachePage(self, url, page):
		global cache

		if not page:
			log.debug("Cache: Got empty page")
			return

		if not config.plugins.seriesplugin.caching.value:
			return

		cache[url] = (time(), page)

	def doCacheList(self, url, list):
		global cache

		if not list:
			log.debug("Cache: Got empty list")
			return

		if not config.plugins.seriesplugin.caching.value:
			return

		cache[url] = (time(), list)
