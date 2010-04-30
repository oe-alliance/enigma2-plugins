# -*- coding: utf-8 -*-
#
#
#    Maximum Box Temperature Renderer for Dreambox/Enigma-2
#    Coded by Vali (c)2010
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

from Components.VariableText import VariableText
from enigma import eLabel
from Components.Sensors import sensors
from Renderer import Renderer

class vRendMaxTemp(Renderer, VariableText):
	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
	GUI_WIDGET = eLabel

	def changed(self, what):
		if not self.suspended:
			maxtemp = 0
			try:
				templist = sensors.getSensorsList(sensors.TYPE_TEMPERATURE)
				tempcount = len(templist)
				for count in range(tempcount):
					id = templist[count]
					tt = sensors.getSensorValue(id)
					if tt > maxtemp:
						maxtemp = tt
			except:
				pass
			self.text = str(maxtemp) + "°C"

	def onShow(self):
		self.suspended = False
		self.changed(None)

	def onHide(self):
		self.suspended = True
