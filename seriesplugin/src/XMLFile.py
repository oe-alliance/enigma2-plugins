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

import os
import re

# Config
from Components.config import config


# XML
from xml.etree.cElementTree import ElementTree, parse, Element, SubElement, Comment
from Tools.XMLTools import stringToXML

# Plugin internal
from . import _
from Logger import log


def indent(elem, level=0):
	i = "\n" + level * "  "
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + "  "
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			indent(elem, level + 1)
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i


class XMLFile(object):
	def __init__(self, path):
		self.__cache = ""
		self.__mtime = -1
		self.__path = path

	def getPath(self):	
		return self.__path
	
	def setPath(self, path):	
		self.__path = path
	
	def readXML(self):
		
		path = self.__path
		log.debug("Read XML from " + str(path))
		
		if not path:
			log.debug("No configuration file given")
			return None
		
		# Abort if no config found
		if not os.path.exists(path):
			log.debug("Configuration file does not exist")
			return None
		
		# Parse if mtime differs from whats saved
		mtime = os.path.getmtime(path)
		if mtime == self.__mtime:
			# No changes in configuration, won't read again
			return self.__cache
		
		# Parse XML
		try:
			etree = parse(path)
		except Exception as e:
			log.exception("Exception in read XML: " + str(e))
			etree = None
			mtime = -1
		
		# Save time and cache file content
		self.__mtime = mtime
		self.__cache = etree
		return self.__cache

	def writeXML(self, etree):
		
		path = self.__path
		log.debug("Write XML to " + path)
		
		try:
			etree.write(path, encoding='utf-8', xml_declaration=True) 
		except Exception as e:
			log.exception("Exception in write XML: " + str(e))
			etree = None
			mtime = -1
		
		# Save time and cache file content
		self.__mtime = os.path.getmtime(path)
		self.__cache = etree
