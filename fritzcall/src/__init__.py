# -*- coding: utf-8 -*-
'''
general functions for FritzCall plugin

$Id: __init__.py 1589 2021-04-25 09:48:00Z michael $
$Author: michael $
$Revision: 1589 $
$Date: 2021-04-25 11:48:00 +0200 (Sun, 25 Apr 2021) $
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
