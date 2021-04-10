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
from mail.mail import Message, sendmail


# Constants
MAIL_HEADER_TEMPLATE = _("{box:s} {name:s}: {plugin:s}: {subject:s}")
MAIL_BODY_TEMPLATE = 	_("{body:s}\n\n") \
								+ _("Provided by Dreambox Plugin {name:s} {version:s} - {plugin:s}\n") \
								+ _("C 2012 by betonme @ IHAD\n") \
								+ _("Support {support:s}\n") \
								+ _("Donate {donate:s}")


class SMTP(ServiceBase):
	
	ForceSingleInstance = False
	
	def __init__(self):
		# Is called on instance creation
		ServiceBase.__init__(self)
		self.connectors = []
		
		# Default configuration
		self.setOption( 'smtpserver', NoSave(ConfigText(default="smtp.server.com", fixed_size = False)),    _("SMTP Server") )
		self.setOption( 'smtpport',   NoSave(ConfigNumber(default = 587)),                                  _("SMTP Port") )
		self.setOption( 'smtpssl',    NoSave(ConfigYesNo(default = True)),                                  _("SMTP SSL") )
		self.setOption( 'smtptls',    NoSave(ConfigYesNo(default = True)),                                  _("SMTP TLS") )
		self.setOption( 'timeout',    NoSave(ConfigNumber(default = 30)),                                   _("Timeout") )
		
		self.setOption( 'username',   NoSave(ConfigText(default="user", fixed_size = False)),               _("User name") )
		self.setOption( 'password',   NoSave(ConfigPassword(default="password")),                           _("Password") )
		
		self.setOption( 'mailfrom',   NoSave(ConfigText(default = "abc@provider.com", fixed_size = False)), _("Mail from") )
		self.setOption( 'mailto',     NoSave(ConfigText(fixed_size = False)),                               _("Mail to or leave empty (From will be used)") )

	def push(self, callback, errback, pluginname, subject, body="", attachments=[]):
		from Plugins.Extensions.PushService.plugin import NAME, VERSION, SUPPORT, DONATE
		
		# Set SMTP parameters
		mailconf = {}
		mailconf["host"]     = self.getValue('smtpserver')
		mailconf["port"]     = self.getValue('smtpport')
		mailconf["username"] = self.getValue('username')
		mailconf["password"] = self.getValue('password')
		mailconf["ssl"]      = self.getValue('smtpssl')
		mailconf["tls"]      = self.getValue('smtptls')
		mailconf["timeout"]  = self.getValue('timeout')
		
		# Create message object
		from_addr = self.getValue('mailfrom')
		to_addrs = [self.getValue('mailto') or from_addr]
		
		# Prepare message
		if body == "":
			body = subject
		subject = MAIL_HEADER_TEMPLATE.format( **{'box': config.pushservice.boxname.value, 'name': NAME, 'plugin': pluginname, 'subject': subject} )
		body    = MAIL_BODY_TEMPLATE.format( **{'body': str(body), 'name': NAME, 'version': VERSION, 'plugin': pluginname, 'support': SUPPORT, 'donate': DONATE} )
		message = Message(from_addr, to_addrs, subject, body) #TODO change mime="text/plain", charset="utf-8")
		if attachments:
			for attachment in attachments:
				message.attach(attachment) #TODO change mime=None, charset=None, content=None):
		
		# Send message
		print _("PushService PushMail: Sending message: %s") % subject
		deferred, connector = sendmail(mailconf, message)
		
		# Add callbacks
		deferred.addCallback(callback)
		deferred.addErrback(errback)
		
		self.connectors.append(connector)

	def cancel(self):
		# Cancel push
		if self.connectors:
			for connector in self.connectors:
				connector.disconnect()
