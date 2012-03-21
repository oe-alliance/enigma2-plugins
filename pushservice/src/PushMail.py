'''
Created on 14.11.2011

@author: Frank Glaser
'''

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
		to_addrs = [config.pushservice.mailfrom.value or config.pushservice.mailto.value]
		
		# Set SMTP parameters
		mailconf = {}
		mailconf["host"] = config.pushservice.smtpserver.value
		mailconf["port"] = config.pushservice.smtpport.value
		mailconf["username"] = config.pushservice.username.value
		mailconf["password"] = config.pushservice.password.value
		mailconf["tls"] = config.pushservice.smtptyp.value
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
