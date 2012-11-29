# -*- coding: utf-8 -*-
'''
general functions for FritzCall plugin
'''
from Components.config import config #@UnresolvedImport
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS #@UnresolvedImport
import gettext, os
from enigma import eBackgroundFileEraser

PluginLanguageDomain = "FritzCall"
PluginLanguagePath = "Extensions/FritzCall/locale/"

def localeInit():
	if os.path.exists(resolveFilename(SCOPE_PLUGINS, os.path.join(PluginLanguagePath, language.getLanguage()))):
		lang = language.getLanguage()
	else:
		lang = language.getLanguage()[:2]
	os.environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		print ("[" + PluginLanguageDomain + "] fallback to default translation for", txt)
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

def initDebug():
	try:
		# os.remove("/tmp/FritzDebug.log")
		eBackgroundFileEraser.getInstance().erase("/tmp/FritzDebug.log")
	except OSError:
		pass

from time import localtime
def debug(message):
	if config.plugins.FritzCall.debug.value:
		try:
			# ltim = localtime()
			# headerstr = u"%04d%02d%02d %02d:%02d " %(ltim[0],ltim[1],ltim[2],ltim[3],ltim[4])
			deb = open("/tmp/FritzDebug.log", "aw")
			# deb.write(headerstr + message.decode('utf-8') + u"\n")
			deb.write(message + "\n")
			deb.close()
		except Exception, e:
			debug("%s (retried debug: %s)" % (repr(message), str(e)))
		

import re
def normalizePhoneNumber(intNo):
	
	found = re.match('^\+' + config.plugins.FritzCall.country.value.replace('00','') + '(.*)', intNo)
	if found:
		intNo = '0' + found.group(1)
	found = re.match('^\+(.*)', intNo)
	if found:
		intNo = '00' + found.group(1)
	intNo = intNo.replace('(', '').replace(')', '').replace(' ', '').replace('/', '').replace('-', '')
	found = re.match('^49(.*)', intNo) # this is most probably an error
	if found:
		intNo = '0' + found.group(1)
	found = re.match('.*?([0-9]+)', intNo)
	if found:
		return found.group(1)
	else:
		return '0'
