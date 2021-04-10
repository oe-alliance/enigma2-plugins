#######################################################################
#
#
#    ReferenceToString for Dreambox/Enigma-2
#    Coded by Vali (c)2011
#    Support: www.dreambox-tools.info
#
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#  To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
#
#######################################################################

from Components.Converter.Converter import Converter
from Components.Element import cached
from Screens.InfoBar import InfoBar


class valiRefString(Converter, object):
	CURRENT = 0
	EVENT = 1

	def __init__(self, type):
		Converter.__init__(self, type)
		self.CHANSEL = None
		self.type = {
				"CurrentRef": self.CURRENT,
				"ServicelistRef": self.EVENT
			}[type]

	@cached
	def getText(self):
		if (self.type == self.EVENT):
			return str(self.source.service.toString())
		elif (self.type == self.CURRENT):
			if self.CHANSEL == None:
				self.CHANSEL = InfoBar.instance.servicelist
			vSrv = self.CHANSEL.servicelist.getCurrent()
			return str(vSrv.toString())
		else:
			return "na"

	text = property(getText)
