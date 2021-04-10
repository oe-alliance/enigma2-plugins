#######################################################################
#
#    Push Service for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=167779
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

import os

# Config
from Components.config import config

# XML
from xml.etree.cElementTree import ElementTree, tostring, parse

# Plugin internal
from . import _


def indent(elem, level=0):
	i = "\n" + level*"  "
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + "  "
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			indent(elem, level+1)
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i


class ConfigFile(object):

	def __init__(self):
		self.mtime = -1
		self.cache = ""

	def readXML(self):
		path = config.pushservice.xmlpath.value
		
		# Abort if no config found
		if not os.path.exists(path):
			print _("PushService No configuration file present")
			return None
		
		# Parse if mtime differs from whats saved
		mtime = os.path.getmtime(path)
		if mtime == self.mtime:
			# No changes in configuration, won't read again
			return self.cache
		
		# Parse XML
		try:
			etree = parse(path).getroot()
		except Exception, e:
			print _("PushService Exception in readXML: ") + str(e)
			etree = None
			mtime = -1
		
		# Save time and cache file content
		self.mtime = mtime
		self.cache = etree
		return self.cache

	def writeXML(self, etree):
		path = config.pushservice.xmlpath.value
		
		indent(etree)
		data = tostring(etree, 'utf-8')
		
		f = None
		try:
			f = open(path, 'w')
			if data:
				f.writelines(data)
		except Exception, e:
			print _("PushService Exception in writeXML: ") + str(e)
		finally:
			if f is not None:
				f.close()
		
		# Save time and cache file content
		self.mtime = os.path.getmtime(path)
		self.cache = etree

