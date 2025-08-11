# -*- coding: utf-8 -*-
'''
general functions for FritzCall plugin

$Id: __init__.py 1656 2025-08-10 13:02:41Z michael $
$Author: michael $
$Revision: 1656 $
$Date: 2025-08-10 15:02:41 +0200 (So., 10 Aug. 2025) $
'''

# missing-docstring / C0111
# invalid-name / C0103
# consider-iterating-dictionary / C0201
# consider-using-f-string / C0209
# line-too-long / C0301
# too-many-lines / C0302
# multiple-imports / C0410
# ungrouped-imports / C0412
# bad-builtin / W0141
# deprecated-lambda / W0110
# Relative import / W0403
# anomalous-backslash-in-string / W1401
# global-statement / W0603
# unused-argument / W0613
# logging-not-lazy / W1201
# logging-format-interpolation / W1202
# unspecified-encoding / W1514
# no-name-in-module / E0611
# pylint: disable=C0111,c0209,C0301

from __future__ import division
import gettext
import os
import re
import logging
from logging import NOTSET
import requests  # @UnresolvedImport # pylint: disable=unused-import,import-error

from Components.config import config  # @UnresolvedImport
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE  # @UnresolvedImport
from enigma import eBackgroundFileEraser

from twisted.internet.threads import deferToThread

from six.moves import range

lang = language.getLanguage()
os.environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("FritzCall", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/FritzCall/locale/"))

logger = logging.getLogger("FritzCall.__init__")
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
exception = logger.exception

USERAGENT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"


def getPage(url, agent=USERAGENT, method="GET", postdata=None, headers={}):  # pylint disable=invalid-name,dangerous-default-value
	# debug(repr(method))
	headers["user-agent"] = agent
	# debug("params: " + repr(postdata))
	if method == "POST" or method == b"POST":
		return deferToThread(requests.post, url, data=postdata, headers=headers, timeout=30.05, verify=False)
	else:
		return deferToThread(requests.get, url, data=postdata, headers=headers, timeout=30.05, verify=False)


def _(txt):
	translated = gettext.dgettext("FritzCall", txt)
	if translated == txt:
		translated = gettext.gettext(txt)
	return translated

# scramble text


def __(text, front=True):  # pylint disable=unused-argument
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


def normalizePhoneNumber(intNo):  # pylint disable=invalid-name

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
