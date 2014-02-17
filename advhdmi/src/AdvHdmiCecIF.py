# -*- coding: utf-8 -*-

from Plugins.SystemPlugins.AdvHdmi.plugin import advhdmiHooks, _print
from Components.config import config

class AdvHdmiCecIF():
	# Param: 
	#   hookKey: an unique identifier
	#   hookDescription: Short Description of the purpose or something; It will be shown in Setup
	def __init__(self, hookKey, hookDescription):
		
		self.hookDescription = hookDescription
		advhdmiHooks[hookKey] = self
	
	def before_event(self, advhdmi_event):
		if config.plugins.AdvHdmiCec.debug.value: _print("Debug: Default-before_event: " + str(advhdmi_event))
		return True
	
	def after_event(self, advhdmi_event):
		if config.plugins.AdvHdmiCec.debug.value: _print("Debug: Default-after_event: " + str(advhdmi_event))

