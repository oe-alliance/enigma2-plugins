# -*- coding: utf-8 -*-
#
# ServiceReference to PiconName  - Converter
#
# Coded by dre (c) 2014
# Support: www.dreambox-tools.info
# E-Mail: dre@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Multimedia GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Multimedia GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Multimedia GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from Components.Converter.Converter import Converter
from Components.Element import cached
from enigma import eServiceCenter, eServiceReference

class RefToPiconName(Converter, object):
	def __init__(self, type):
		Converter.__init__(self, type)

	@cached
	def getText(self):
		ref = self.source.service
		if ref is not None:
			#bouquet or marker
			if ref.flags & (eServiceReference.isDirectory|eServiceReference.isMarker):
				info = eServiceCenter.getInstance().info(ref)
				if info:
					return info.getName(ref).replace(" ", "_")
			#channel
			else:
				return ref.toString()
		
		return ""
		
	text = property(getText)
