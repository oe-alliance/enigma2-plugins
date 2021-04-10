# -*- coding: utf-8 -*-
# by betonme @2015

import os
import re

# Config
from Components.config import config

# XML
from xml.etree.cElementTree import ElementTree, parse, Element, SubElement, Comment
from Tools.XMLTools import stringToXML

# Plugin internal
from . import _
from XMLFile import XMLFile, indent
from Logger import log


class XMLTVBase(object):
	
	def __init__(self):
		
		self.epgimport = None
		self.epgimportversion = "0"
		self.xmltvimport = None
		self.xmltvimportversion = "0"
		
		# Check if xmltvimport exists
		if os.path.exists("/etc/epgimport"):
			log.debug("readXMLTV: Found epgimport")
			path = "/etc/epgimport/wunschliste.sources.xml"
			self.epgimport = XMLFile(path)
		
		# Check if xmltvimport exists
		elif os.path.exists("/etc/xmltvimport"):
			log.debug("readXMLTV: Found xmltvimport")
			path = "/etc/xmltvimport/wunschliste.sources.xml"
			self.xmltvimport = XMLFile(path)
		
		self.readXMLTVConfig()

	def readXMLTVConfig(self):
		
		if self.epgimport:
			etree = self.epgimport.readXML()
			if etree:
				self.epgimportversion = etree.getroot().get("version", "1")
				log.debug("readXMLTVConfig: EPGImport Version " + self.epgimportversion)
		
		if self.xmltvimport:
			etree = self.xmltvimport.readXML()
			if etree:
				self.xmltvimportversion = etree.getroot().get("version", "1")
				log.debug("readXMLTVConfig: XMLTVImport Version " + self.xmltvimportversion)
		
	
	def writeXMLTVConfig(self):
		
		if int(self.epgimportversion[0]) >= 5 and int(self.xmltvimportversion[0]) >= 5:
			return
		
		if self.epgimport is None and self.xmltvimport is None:
			return
		
		if config.plugins.seriesplugin.epgimport.value == False and config.plugins.seriesplugin.xmltvimport.value == False:
			return
		
		# Build Header
		from plugin import NAME, VERSION
		root = Element("sources")
		root.set('version', VERSION)
		root.set('created_by', NAME)
		root.append(Comment(_("Don't edit this manually unless you really know what you are doing")))
		
		element = SubElement( root, "source", type="gen_xmltv", channels="wunschliste.channels.xml" )
		
		SubElement( element, "description" ).text = "Wunschliste XMLTV"
		SubElement( element, "url" ).text = config.plugins.seriesplugin.xmltv_url.value
		
		etree = ElementTree( root )
		
		indent(etree.getroot())
		
		if config.plugins.seriesplugin.epgimport.value:
			log.debug("Write: xml channels for epgimport")
			try:
				self.epgimport.writeXML( etree )
			except Exception as e:
				log.exception("Exception in write XML: " + str(e))
		
		if config.plugins.seriesplugin.xmltvimport.value:
			log.debug("Write: xml channels for xmltvimport")
			try:
				self.xmltvimport.writeXML( etree )
			except Exception as e:
				log.exception("Exception in write XML: " + str(e))
