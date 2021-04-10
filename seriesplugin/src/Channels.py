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

from enigma import eServiceReference, eServiceCenter
from ServiceReference import ServiceReference

from Tools.BoundFunction import boundFunction

# XML
from xml.etree.cElementTree import ElementTree, parse, Element, SubElement, Comment
from Tools.XMLTools import stringToXML

# Plugin internal
from . import _
from XMLFile import XMLFile, indent
from Logger import log

try:
	#Python >= 2.7
	from collections import OrderedDict
except:
	from OrderedDict import OrderedDict


ChannelReplaceDict = OrderedDict([
	('\(S\)', ''),
	(' HD', ''),
	(' TV', ''),
	(' Television', ''),
	(' Channel', ''),
	('III', 'drei'),
	('II', 'zwei'),
	#('I',   'eins'),
	('ARD', 'daserste'),
	('\+', 'plus'),
	('0', 'null'),
	('1', 'eins'),
	('2', 'zwei'),
	('3', 'drei'),
	('4', 'vier'),
	('5', 'fuenf'),
	('6', 'sechs'),
	('7', 'sieben'),
	('8', 'acht'),
	('9', 'neun'),
	('\xc3\xa4', 'ae'),
	('\xc3\xb6', 'oe'),
	('\xc3\xbc', 'ue'),
	('\xc3\x84', 'ae'),
	('\xc3\x96', 'oe'),
	('\xc3\x9c', 'ue'),
	('\xc3\x9f', 'ss'),
])
CompiledRegexpChannelUnify = re.compile('|'.join(ChannelReplaceDict))
CompiledRegexpChannelRemoveSpecialChars = re.compile('[^a-zA-Z0-9]')


def unifyChannel(text):
	def translate(match):
		m = match.group(0)
		return ChannelReplaceDict.get(m, m)
	
	text = CompiledRegexpChannelUnify.sub(translate, text)
	try:
		text = text.decode("utf-8").encode("latin1")
	except:
		pass
	text = CompiledRegexpChannelRemoveSpecialChars.sub('', text)
	return text.strip().lower()


def getServiceList(ref):
	root = eServiceReference(str(ref))
	serviceHandler = eServiceCenter.getInstance()
	return serviceHandler.list(root).getContent("SN", True)


def getTVBouquets():
	from Screens.ChannelSelection import service_types_tv
	return getServiceList(service_types_tv + ' FROM BOUQUET "bouquets.tv" ORDER BY bouquet')


def getServicesOfBouquet(bouquet):
	bouquetlist = getServiceList(bouquet)
	chlist = []
	for (serviceref, servicename) in bouquetlist:
		
		if (eServiceReference(serviceref).flags & eServiceReference.isDirectory):
			# handle directory services
			log.debug("SPC: found directory %s" % (serviceref))
			chlist.extend(getServicesOfBouquet(serviceref))
		
		elif (eServiceReference(serviceref).flags & eServiceReference.isGroup):
			# handle group services
			log.debug("SPC: found group %s" % (serviceref))
			chlist.extend(getServicesOfBouquet(serviceref))
		
		elif not (eServiceReference(serviceref).flags & eServiceReference.isMarker):
			# playable
			log.debug("SPC: found playable service %s" % (serviceref))
			chlist.append((servicename, re.sub('::.*', ':', serviceref), unifyChannel(servicename)))
		
	return chlist


def buildSTBchannellist(BouquetName=None):
	chlist = []
	tvbouquets = getTVBouquets()
	log.debug("SPC: found %s bouquet: %s" % (len(tvbouquets), tvbouquets))

	if not BouquetName:
		for bouquet in tvbouquets:
			chlist.extend(getServicesOfBouquet(bouquet[0]))
	else:
		for bouquet in tvbouquets:
			if bouquet[1] == BouquetName:
				chlist.extend(getServicesOfBouquet(bouquet[0]))
	
	return chlist


def getChannel(ref):
	if isinstance(ref, eServiceReference):
		servicereference = ServiceReference(ref)
	elif isinstance(ref, ServiceReference):
		servicereference = ref
	else:
		servicereference = ServiceReference(str(ref))
	if servicereference:
		return servicereference.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
	return ""


def compareChannels(ref, remote):
	log.debug("compareChannels", ref, remote)
	remote = remote.lower()
	if ref in ChannelsBase.channels:
		(name, alternatives) = ChannelsBase.channels[ref]
		for altname in alternatives:
			if altname.lower() in remote or remote in altname.lower():
				return True
		
	return False


def lookupChannelByReference(ref):
	if ref in ChannelsBase.channels:
		(name, alternatives) = ChannelsBase.channels[ref]
		altnames = []
		for altname in alternatives:
			if altname:
				log.debug("lookupChannelByReference", ref, altname)
				altnames.append(altname)
		return altnames
	log.debug("lookupChannelByReference: Failed for", ref)
	return False


class ChannelsBase(XMLFile):

	channels = {}  # channels[reference] = ( name, [ name1, name2, ... ] )
	channels_changed = False
	
	def __init__(self):
		
		path = config.plugins.seriesplugin.channel_file.value
		XMLFile.__init__(self, path)
		
		self.resetChannels()
	
	def channelsEmpty(self):
		return not ChannelsBase.channels
	
	def resetChannels(self):
		ChannelsBase.channels = {}
		ChannelsBase.channels_changed = False
		
		self.loadXML()
	
	def addChannel(self, ref, name, remote):
		log.debug("SP addChannel name remote", name, remote)
		
		if ref in ChannelsBase.channels:
			(name, alternatives) = ChannelsBase.channels[ref]
			if remote not in alternatives:
				alternatives.append(remote)
				ChannelsBase.channels[ref] = (name, alternatives)
		else:
			ChannelsBase.channels[ref] = (name, [remote])
		ChannelsBase.channels_changed = True
	
	def replaceChannel(self, ref, name, remote):
		log.debug("SP addChannel name remote", name, remote)
		
		ChannelsBase.channels[ref] = (name, [remote])
		ChannelsBase.channels_changed = True

	def removeChannel(self, ref):
		if ref in ChannelsBase.channels:
			del ChannelsBase.channels[ref]
			ChannelsBase.channels_changed = True

	#
	# I/O Functions
	#
	def loadXML(self):
		try:
			# Read xml config file
			etree = self.readXML()
			if etree:
				channels = {}
				
				# Parse Config
				def parse(root):
					channels = {}
					version = root.get("version", "1")
					if version.startswith("1"):
						log.warning(_("Skipping old channels file"))
					elif version.startswith("2") or version.startswith("3") or version.startswith("4"):
						log.debug("Channel XML Version 4")
						ChannelsBase.channels_changed = True
						if root:
							for element in root.findall("Channel"):
								name = element.get("name", "")
								reference = element.get("reference", "")
								if name and reference:
									alternatives = []
									for alternative in element.findall("Alternative"):
										alternatives.append(alternative.text)
									channels[reference] = (name, list(set(alternatives)))
									log.debug("Channel", reference, channels[reference])
					else:
						# XMLTV compatible channels file
						log.debug("Channel XML Version 5")
						if root:
							for element in root.findall("channel"):
								alternatives = []
								id = element.get("id", "")
								alternatives.append(id)
								name = element.get("name", "")
								reference = element.text
								#Test customization but XML conform
								for web in element.findall("web"):
									alternatives.append(web.text)
								channels[reference] = (name, list(set(alternatives)))
								log.debug("Channel", reference, channels[reference])
					return channels
				
				channels = parse(etree.getroot())
				log.debug("Channel XML load", len(channels))
			else:
				channels = {}
			ChannelsBase.channels = channels
		except Exception as e:
			log.exception("Exception in loadXML: " + str(e))

	def saveXML(self):
		try:
			if ChannelsBase.channels_changed:
				
				ChannelsBase.channels_changed = False
				
				channels = ChannelsBase.channels
				
				# Generate List in RAM
				etree = None
				#log.debug("saveXML channels", channels)
				log.debug("SP saveXML channels", len(channels))
				
				# XMLTV compatible channels file
				#TEST Do we need to write the xml header node
				
				# Build Header
				from plugin import NAME, VERSION
				root = Element("channels")
				root.set('version', VERSION)
				root.set('created_by', NAME)
				root.append(Comment(_("Don't edit this manually unless you really know what you are doing")))
				
				# Build Body
				def build(root, channels):
					if channels:
						for reference, namealternatives in channels.iteritems():
							name, alternatives = namealternatives[:]
							if alternatives:
								# Add channel
								web = alternatives[0]
								element = SubElement(root, "channel", name=stringToXML(name), id=stringToXML(web))
								element.text = stringToXML(reference)
								del alternatives[0]
								if alternatives:
									for web in alternatives:
										SubElement(element, "web").text = stringToXML(web)
					return root
				
				etree = ElementTree(build(root, channels))
				
				indent(etree.getroot())
				
				self.writeXML(etree)
				
				if config.plugins.seriesplugin.epgimport.value:
					log.debug("Write: xml channels for epgimport")
					try:
						path = "/etc/epgimport/wunschliste.channels.xml"
						etree.write(path, encoding='utf-8', xml_declaration=True) 
					except Exception as e:
						log.exception("Exception in write XML: " + str(e))
				
				if config.plugins.seriesplugin.xmltvimport.value:
					log.debug("Write: xml channels for xmltvimport")
					try:
						path = "/etc/xmltvimport/wunschliste.channels.xml"
						etree.write(path, encoding='utf-8', xml_declaration=True) 
					except Exception as e:
						log.exception("Exception in write XML: " + str(e))
			
		except Exception as e:
			log.exception("Exception in writeXML: " + str(e))
