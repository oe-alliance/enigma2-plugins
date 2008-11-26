##
## RS Downloader
## by AliAbdul
##
from Components.Language import language
from os import environ
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE
import gettext

##############################################################################

lang = language.getLanguage()
environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("RSDownloader", resolveFilename(SCOPE_LANGUAGE))

def _(txt):
	t = gettext.dgettext("RSDownloader", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

##############################################################################

class TitleScreen(Screen):
	def __init__(self, session, parent=None):
		Screen.__init__(self, session, parent)
		self.onLayoutFinish.append(self.setScreenTitle)

	def setScreenTitle(self):
		self.setTitle(_("RS Downloader"))

