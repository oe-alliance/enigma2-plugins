# -*- coding: utf-8 -*-
'''
general functions for FritzCall plugin

$Id: __init__.py 1639 2023-01-11 11:21:40Z michael $
$Author: michael $
$Revision: 1639 $
$Date: 2023-01-11 12:21:40 +0100 (Wed, 11 Jan 2023) $
'''

from __future__ import division
import gettext
import os
from logging import NOTSET
from six.moves import range

from Components.config import config  # @UnresolvedImport
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE  # @UnresolvedImport
from enigma import eBackgroundFileEraser

lang = language.getLanguage()
os.environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("FritzCall", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/FritzCall/locale/"))

import logging
logger = logging.getLogger("FritzCall.__init__")
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
exception = logger.exception

from twisted.internet.threads import deferToThread
import requests
USERAGENT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"


def getPage(url, agent=USERAGENT, method="GET", postdata=None, headers={}):
	# debug(repr(method))
	# headers["user-agent"] = agent
	# debug("params: " + repr(postdata))
	if method == "POST" or method == b"POST":
		return deferToThread(requests.post, url, data=postdata, headers=headers, timeout=30.05, verify=False)
	else:
		return deferToThread(requests.get, url, data=postdata, headers=headers, timeout=30.05, verify=False)


def _(txt):  # pylint: disable=C0103
	td = gettext.dgettext("FritzCall", txt)
	if td == txt:
		td = gettext.gettext(txt)
	return td

# scramble text


def __(text, front=True):  #pylint: disable=unused-argument
	#===========================================================================
	# if len(text) > 5:
	#	if front:
	#		return '.....' + text[5:]
	#	else:
	#		return text[:-5] + '.....'
	# else:
	#	return '.....'
	#===========================================================================
	# debug("__ 1")
	out = ""
	# debug("__ 2")
	for i in range(len(text) // 2):
		# debug("__ 3")
		out = out + text[i * 2] + '.'
		# debug("__ 4: %s", out)
	# debug("__ 5")
	return out


import re


def normalizePhoneNumber(intNo):

	found = re.match(r'^\+' + config.plugins.FritzCall.country.value.replace('00', '') + '(.*)', intNo)
	if found:
		intNo = '0' + found.group(1)
	found = re.match(r'^\+(.*)', intNo)
	if found:
		intNo = '00' + found.group(1)
	intNo = intNo.replace('(', '').replace(')', '').replace(' ', '').replace('/', '').replace('-', '')
	found = re.match(r'^49(.*)', intNo)  # this is most probably an error
	if found:
		intNo = '0' + found.group(1)
	found = re.match('.*?([0-9]+)', intNo)
	if found:
		return found.group(1)
	else:
		return '0'
