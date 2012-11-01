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

# Config
from Components.config import ConfigYesNo, NoSave

# Plugin internal
#from Plugins.Extensions.PushService.__init__ import _
from Plugins.Extensions.PushService.ControllerBase import ControllerBase

# Plugin specific
import NavigationInstance
from time import localtime, strftime
from enigma import eTimer


# Constants
SUBJECT = _("Record Notification")


class RecordNotification(ControllerBase):
	
	ForceSingleInstance = True
	
	def __init__(self):
		# Is called on instance creation
		ControllerBase.__init__(self)
		
		self.forceBindRecordTimer = eTimer()
		self.forceBindRecordTimer.callback.append(self.begin)
 
		# Default configuration
		self.setOption( 'send_on_start', NoSave(ConfigYesNo( default = False )), _("Send notification on record start") )
		self.setOption( 'send_on_end',   NoSave(ConfigYesNo( default = True )),  _("Send notification on record end") )
		#TODO option to send free space

	def begin(self):
		# Is called after starting PushService
		
		if self.getValue('send_on_start') or self.getValue('send_on_end'):
			if NavigationInstance.instance:
				if self.onRecordEvent not in NavigationInstance.instance.RecordTimer.on_state_change:
					print "append"
					# Append callback function
					NavigationInstance.instance.RecordTimer.on_state_change.append(self.onRecordEvent)
			else:
				# Try again later
				self.forceBindRecordTimer.startLongTimer(1)
		else:
			# Remove callback function
			self.end()

	def end(self):
		# Is called after stopping PushSerive
		if NavigationInstance.instance:
			# Remove callback function
			if self.onRecordEvent in NavigationInstance.instance.RecordTimer.on_state_change:
				NavigationInstance.instance.RecordTimer.on_state_change.remove(self.onRecordEvent)

	def run(self, callback, errback):
		# At the end a plugin has to call one of the functions: callback or errback
		# Callback should return with at least one of the parameter: Header, Body, Attachment
		# If empty or none is returned, nothing will be sent
		callback()

	def onRecordEvent(self, timer):
		text = ""
		
		if timer.justplay:
			pass
		
		elif timer.state == timer.StatePrepared:
			pass
		
		elif timer.state == timer.StateRunning:
			if self.getValue('send_on_start'):
				text += _("Record started:\n") \
							+ str(timer.name) + "  " \
							+ strftime(_("%Y.%m.%d %H:%M"), localtime(timer.begin)) + " - " \
							+ strftime(_("%H:%M"), localtime(timer.end)) + "  " \
							+ str(timer.service_ref and timer.service_ref.getServiceName() or "")
				del timer
			
		# Finished repeating timer will report the state StateEnded+1 or StateWaiting
		else:
			if self.getValue('send_on_end'):
				text += _("Record finished:\n  ") \
							+ str(timer.name) + "\t" \
							+ strftime(_("%Y.%m.%d %H:%M"), localtime(timer.begin)) + " - " \
							+ strftime(_("%H:%M"), localtime(timer.end)) + "\t" \
							+ str(timer.service_ref and timer.service_ref.getServiceName() or "")
				del timer
		
		if text:
			#TODO Problem test tun won't get the message
			# Push mail
			from Plugins.Extensions.PushService.plugin import gPushService
			if gPushService:
				gPushService.push(self, SUBJECT, text)

