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

import os
import inspect

from Components.config import *

# Plugin internal
from . import _
from mail import Message, sendmail


# Constants
MAIL_HEADER_PREFIX = _("%s PushService: ")
MAIL_BODY_PREFIX = ""
MAIL_BODY_SUFFIX =	"\n\n" \
										+ _("Provided by Dreambox Plugin %s %s") + "\n" \
										+ _("C 2012 by betonme @ IHAD") + "\n" \
										+ _("Support %s") + "\n" \
										+ _("Donate %s")


class PushMail(object):
	def __init__(self):
		pass

	def push(self, subject, body="", attachments=[], success=None, error=None, timeout=30):
		from plugin import NAME, VERSION, SUPPORT, DONATE
		
		from_addr = config.pushservice.mailfrom.value
		to_addrs = [config.pushservice.mailto.value or config.pushservice.mailfrom.value]
		
		# Set SMTP parameters
		mailconf = {}
		mailconf["host"] = config.pushservice.smtpserver.value
		mailconf["port"] = config.pushservice.smtpport.value
		mailconf["username"] = config.pushservice.username.value
		mailconf["password"] = config.pushservice.password.value
		mailconf["ssl"] = config.pushservice.smtpssl.value
		mailconf["tls"] = config.pushservice.smtptls.value
		mailconf["timeout"] = timeout
		
		# Create message object
		subject = ( MAIL_HEADER_PREFIX % config.pushservice.boxname.value + str(subject) )
		body = ( MAIL_BODY_PREFIX + str(body) + MAIL_BODY_SUFFIX % ( NAME, VERSION, SUPPORT, DONATE) )
		message = Message(from_addr, to_addrs, subject, body) #TODO change mime="text/plain", charset="utf-8")
		if attachments:
			for attachment in attachments:
				message.attach(attachment) #TODO change mime=None, charset=None, content=None):
		
		# Send message
		print _("[PushService] PushMail: Sending message: %s") % subject
		deferred, connector = sendmail(mailconf, message)
		
		# Define callbacks
		def callback(r):
			print _("[PushService] PushMail: Sent successfully: %s") % subject
			if callable(success):
				# Check number of arguments
				argspec = inspect.getargspec(success)
				if len(argspec.args) > 1:
					success(r)
				else:
					success()
		
		def errback(e):
			print _("[PushService] PushMail: Sent failed: %s") % subject + "\n" + str(e)
			if callable(error):
				# Check number of arguments
				argspec = inspect.getargspec(error)
				if len(argspec.args) > 1:
					error(e)
				else:
					error()
		
		# Add callbacks
		deferred.addCallback(callback)
		deferred.addErrback(errback)
		
		return connector
