# -*- coding: utf-8 -*-
from __future__ import print_function
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os
import gettext

from six.moves import reduce
from functools import reduce


__version__ = "1.6.6"

PluginLanguageDomain = "WebInterface"
PluginLanguagePath = "Extensions/WebInterface/locale"

def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		print("[" + PluginLanguageDomain + "] fallback to default translation for " + txt)
		t = gettext.gettext(txt)
	return t

def bin2long(s):
	return reduce( lambda x, y:(x<<8)+y, list(map(ord, s)))

def long2bin(l):
	res = ""
	for byte in list(range(128)):
		res += chr((l >> (1024 - (byte + 1) * 8)) & 0xff)
	return res

def rsa_pub1024(src, mod):
	return long2bin(pow(bin2long(src), 65537, bin2long(mod)))

def decrypt_block(src, mod):
	if len(src) != 128 and len(src) != 202:
		return None
	dest = rsa_pub1024(src[:128], mod)
	hash = sha.new(dest[1:107])
	if len(src) == 202:
		hash.update(src[131:192])
	result = hash.digest()
	if result == dest[107:127]:
		return dest
	return None

localeInit()
language.addCallback(localeInit)
