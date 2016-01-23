# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. Latsch 2007
#                   modified by Volker Christian 2008
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os,gettext

def localeInit():
	gettext.bindtextdomain("VlcPlayer", resolveFilename(SCOPE_PLUGINS, "Extensions/VlcPlayer/locale"))

def _(txt):
	t = gettext.dgettext("VlcPlayer", txt)
	if t == txt:
		print "[VLC] fallback to default translation for", txt
		t = gettext.gettext(txt)
	return t

localeInit()
