from __future__ import absolute_import
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
from Components.config import config, NoSave, ConfigText, ConfigNumber, ConfigYesNo, ConfigPassword

# Plugin internal
from Plugins.Extensions.PushService.__init__ import _
from Plugins.Extensions.PushService.ServiceBase import ServiceBase

# Plugin specific
import sys
from .gntp import notifier

# Constants
APP_NAME = _("{box:s} {name:s}")
NOTIFICATION_TYPE = _("{name:s}")
GROWL_SUBJECT_TEMPLATE = _("{box:s}: {subject:s}")
GROWL_BODY_TEMPLATE = 	_("{body:s}\n\n") \
											+ _("Donate {donate:s}")


class GNTP(ServiceBase):
	
	ForceSingleInstance = False
	
	def __init__(self):
		# Is called on instance creation
		ServiceBase.__init__(self)
		#self.sockets = []
		
		# Default configuration
		self.setOption('growlhost',  NoSave(ConfigText(default="host", fixed_size=False)),  _("Growl Host name"))
		self.setOption('growlport',  NoSave(ConfigNumber(default=23053)),                   _("Growl Port"))
		self.setOption('timeout',    NoSave(ConfigNumber(default=3)),                       _("Timeout"))
		self.setOption('password',   NoSave(ConfigPassword()),                                _("Password"))
		self.setOption('sticky',     NoSave(ConfigYesNo(default=True)),                     _("Send as sticky"))
		self.setOption('priority',   NoSave(ConfigNumber(default=1)),                       _("Send with priority"))

	def push(self, callback, errback, pluginname, subject, body="", attachments=[]):
		from Plugins.Extensions.PushService.plugin import NAME, VERSION, SUPPORT, DONATE
		
		box = config.pushservice.boxname.value
		app = APP_NAME.format(**{'box': box, 'name': NAME})
		nottype = NOTIFICATION_TYPE.format(**{'box': box, 'name': NAME})
		
		# Prepare message
		if body == "":
			body = subject
		subject = GROWL_SUBJECT_TEMPLATE.format(**{'box': box, 'subject': subject})
		body = GROWL_BODY_TEMPLATE.format(**{'body': str(body), 'name': NAME, 'version': VERSION, 'plugin': pluginname, 'support': SUPPORT, 'donate': DONATE})
		
		# Registrate
		growl = gntp.notifier.GrowlNotifier(
			applicationName=app,
			notifications=[nottype],
			defaultNotifications=[nottype],
			hostname=self.getValue('growlhost'),
			port=self.getValue('growlport'),
			password=self.getValue('password')
		)
		growl.socketTimeout = self.getValue('timeout')
		growl.register()
		
		# Send a message
		#socket = 
		sent = growl.notify(
			noteType=nottype,
			title=subject,
			description=body,
			#Maybelater icon        = "http://example.com/icon.png",
			sticky=self.getValue('sticky'),
			priority=self.getValue('priority')
		)
		#self.sockets.append(socket)
		
		if sent is True:
			callback()
		else:
			errback(sent)

#TODO Maybe later
# we have to rewrite the gntp client
# it has to use asynchronous connection - maybe twisted
# and it should return the active socket / connector
#	def cancel(self):
#		# Cancel push
#		if self.sockets:
#			for socket in self.sockets:
#				socket.close()
