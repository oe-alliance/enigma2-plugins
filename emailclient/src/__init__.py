from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from Components.Language import language
from Components.config import config
import os, gettext, time

lang = language.getLanguage()
os.environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("EmailClient", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/EmailClient/locale/"))

def _(txt):
	t = gettext.dgettext("EmailClient", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

def initLog():
	try:
		os.remove("/tmp/EmailClient.log")
	except:
		pass

def debug(message):
	if config.plugins.emailimap.debug.value:
		try:
			deb = open("/tmp/EmailClient.log", "aw")
			deb.write(time.ctime() + ': ' + message + "\n")
			deb.close()
		except:
			debug(repr(message) + " (retried debug)")

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
