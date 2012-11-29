# -*- coding: utf-8 -*-
'''
Common functions for EmailClient
'''
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from Components.Language import language
from Components.config import config
import os, gettext, time

PluginLanguageDomain = "EmailClient"
PluginLanguagePath = "Extensions/EmailClient/locale/"

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
		print "[" + PluginLanguageDomain + "] fallback to default translation for", txt
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

def initLog():
	try:
		os.remove("/tmp/EmailClient.log")
	except OSError:
		pass

def debug(message):
	if config.plugins.emailimap.debug.value:
		try:
			deb = open("/tmp/EmailClient.log", "aw")
			deb.write(time.ctime() + ': ' + message + "\n")
			deb.close()
		except Exception, e:
			debug("%s (retried debug: %s)" %(repr(message), str(e)))

from enigma import getDesktop
DESKTOP_WIDTH = getDesktop(0).size().width()
DESKTOP_HEIGHT = getDesktop(0).size().height()
def scaleH(y2, y1):
	if y2 == -1:
		y2 = y1*1280/720
	elif y1 == -1:
		y1 = y2*720/1280
	return scale(y2, y1, 1280, 720, DESKTOP_WIDTH)
def scaleV(y2, y1):
	if y2 == -1:
		y2 = y1*720/576
	elif y1 == -1:
		y1 = y2*576/720
	return scale(y2, y1, 720, 576, DESKTOP_HEIGHT)
def scale(y2, y1, x2, x1, x):
	return (y2 - y1) * (x - x1) / (x2 - x1) + y1
