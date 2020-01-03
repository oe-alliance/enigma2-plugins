#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Alexandre Fiori
# based on the original Tornado by Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# Changes by betonme
# 24.02.2012
#             Added retries and timeout parameter
#             Return deferred and connector
# 03.03.2012
#             Added SSL parameter

"""Implementation of e-mail Message and SMTP with and without SSL"""

import types
import os.path
from cStringIO import StringIO
from OpenSSL.SSL import SSLv3_METHOD

from email import Encoders
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.Utils import COMMASPACE, formatdate

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.ssl import ClientContextFactory
from twisted.mail.smtp import ESMTPSenderFactory

class Message(object):
    def __init__(self, from_addr, to_addrs, subject, message, mime="text/plain", charset="utf-8"):
        self.subject = subject
        self.from_addr = from_addr
        self.to_addrs = isinstance(to_addrs, types.StringType) and [to_addrs] or to_addrs
  
        self.msg = None
        self.__cache = None
        self.message = MIMEText(message)
        self.message.set_charset(charset)
        self.message.set_type(mime)
  
    def attach(self, filename, mime=None, charset=None, content=None):
        base = os.path.basename(filename)
        if content is None:
            fd = open(filename)
            content = fd.read()
            fd.close()
  
        if not isinstance(content, types.StringType):
            raise TypeError("don't know how to handle content: %s" % type(content))
  
        part = MIMEBase("application", "octet-stream")
        part.set_payload(content)
        Encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment; filename=\"%s\"" % base)
  
        if mime is not None:
            part.set_type(mime)
  
        if charset is not None:
            part.set_charset(charset)
  
        if self.msg is None:
            self.msg = MIMEMultipart()
            self.msg.attach(self.message)
  
        self.msg.attach(part)
  
    def __str__(self):
        return self.__cache or "nuswit mail message: not rendered yet"
  
    def render(self):
        if self.msg is None:
            self.msg = self.message
  
        self.msg["Subject"] = self.subject
        self.msg["From"] = self.from_addr
        self.msg["To"] = COMMASPACE.join(self.to_addrs)
        self.msg["Date"] = formatdate(localtime=True)
  
        if self.__cache is None:
            self.__cache = self.msg.as_string()
  
        return StringIO(self.__cache)


def sendmail(mailconf, message):
    """Takes a regular dictionary as mailconf, as follows:
    mailconf["host"] = "your.smtp.com" (required)
    mailconf["port"] = 25 (optional, default 25 or 587 for TLS)
    mailconf["username"] = "username" (optional)
    mailconf["password"] = "password" (optional)
    mailconf["ssl"] = True | False (optional, default False)
    mailconf["tls"] = True | False (optional, default False)
    mailconf["retries"] = 0 (optional, default 0)
    mailconf["timeout"] = 30 (optional, default 30)
    """
    if not isinstance(mailconf, types.DictType):
        raise TypeError("mailconf must be a regular python dictionary")
    
    if not isinstance(message, Message):
        raise TypeError("message must be an instance of nuswit.mail.Message")
    
    host = mailconf.get("host")
    if not isinstance(host, types.StringType):
        raise ValueError("mailconf requires a 'host' configuration")
    
    ssl = mailconf.get("ssl", True)
    tls = mailconf.get("tls", True)
    if ssl is True:
        port = mailconf.get("port", 587)
        contextFactory = ClientContextFactory()
        contextFactory.method = SSLv3_METHOD
    else:
        port = mailconf.get("port", 25)
        contextFactory = None
    
    retries = mailconf.get("retries", 0)
    timeout = mailconf.get("timeout", 30)
    
    if not isinstance(port, types.IntType):
        raise ValueError("mailconf requires a proper 'port' configuration")
    
    deferred = Deferred()
    username, password = mailconf.get("username"), mailconf.get("password")
    factory = ESMTPSenderFactory(
        username, password,
        message.from_addr, message.to_addrs, message.render(),
        deferred, contextFactory=contextFactory,
        requireAuthentication=(username and password),
        requireTransportSecurity=tls,
        retries=retries, timeout=timeout)
    
    if not ssl:
        connector = reactor.connectTCP(host, port, factory, timeout=timeout)
    else:
        connector = reactor.connectSSL(host, port, factory, contextFactory, timeout=timeout)
    
    return deferred, connector
