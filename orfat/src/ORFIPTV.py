##
## ORF.at IPTV streaming module
## by AliAbdul
##
from Components.ActionMap import ActionMap
from Components.Pixmap import MovingPixmap
from enigma import ePoint, eSize
from Plugins.Extensions.VlcPlayer.VlcServerConfig import vlcServerConfig
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import fileExists
from Tools.LoadPixmap import LoadPixmap
from twisted.web.client import downloadPage, getPage

##########################################################

class ORFMain(Screen):
	skin = """
	<screen position="center,center" size="550,450" title="ORF.at IPTV" backgroundColor="#6699cc" >
		<ePixmap pixmap="skin_default/arrowup.png" position="256,10" size="37,70" alphatest="blend" />
		<widget name="pic" position="0,0" size="0,0" />
		<ePixmap pixmap="skin_default/arrowdown.png" position="256,370" size="37,70" alphatest="blend" />
	</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)
		
		self.session = session
		self.movies = []
		self.pics = []
		self.selectedEntry = 0
		self.pic = "/tmp/orf.jpg"
		self.working = False
		
		self["pic"] = MovingPixmap()
		self["actions"] = ActionMap(["WizardActions"],
			{
				"ok": self.okClicked,
				"back": self.close,
				"up": self.up,
				"down": self.down
			}, -1)
		
		self.onLayoutFinish.append(self.downloadList)

	def okClicked(self):
		if self.working == False:
			if len(self.movies) > 0:
				movie = self.movies[self.selectedEntry]
				serverList = vlcServerConfig.getServerlist()
				if len(serverList) == 0:
					self.session.open(MessageBox, "Kein Server im vlc-Plugin konfiguriert!", MessageBox.TYPE_ERROR)
				elif len(serverList) == 1:
					serverList[0].play(self.session, movie, "ORF.at IPTV")
				else:
					list = []
					for x in serverList:
						list.append((x.getName(), x))
					self.session.openWithCallback(self.serverChosen, ChoiceBox, title="Waehle den vlc-Server...", list=list)

	def serverChosen(self, server):
		if server is not None:
			server[1].play(self.session, self.movies[self.selectedEntry], "ORF.at IPTV")

	def downloadList(self):
		self.working = True
		getPage("http://iptv.orf.at").addCallback(self.downloadListCallback).addErrback(self.downloadListError)

	def downloadListError(self, error=""):
		print str(error)
		self.working = False
		self.session.open(MessageBox, "Fehler beim Verbindungsversuch!", MessageBox.TYPE_ERROR)

	def downloadListCallback(self, page=""):
		while page.__contains__("javascript:iptvPopup('"):
			idx = page.index("javascript:iptvPopup('")
			page = page[idx+22:]
			idx = page.index("'")
			movie = page[:idx]
			idx = movie.index("?")
			movie = "%s%s" % ("mms://stream4.orf.at/news/", movie[idx+1:])
			self.movies.append(movie)
			idx = page.index('<IMG SRC=')
			page = page[idx+9:]
			idx = page.index(' ALT')
			pic = "%s%s" % ("http://iptv.orf.at/", page[:idx])
			self.pics.append(pic)
		self.selectionChanged(0)

	def up(self):
		if self.working == False:
			self.selectionChanged(-1)

	def down(self):
		if self.working == False:
			self.selectionChanged(1)

	def selectionChanged(self, direction):
		if len(self.movies) > 0:
			self.working = True
			self.selectedEntry += direction
			if self.selectedEntry < 0:
				self.selectedEntry = len(self.movies) - 1
			elif self.selectedEntry > len(self.movies) - 1:
				self.selectedEntry = 0
			downloadPage(self.pics[self.selectedEntry], self.pic).addCallback(self.downloadPicCallback).addErrback(self.downloadPicError)
		else:
			self.downloadListError()

	def downloadPicCallback(self, page=""):
		picture = LoadPixmap(self.pic)
		size = picture.size()
		width = size.width()
		height = size.height()
		self["pic"].instance.setPixmap(picture)
		self["pic"].instance.resize(eSize(width, height))
		left = int((550 / 2) - (width / 2))
		top = int((450 / 2) - (height / 2))
		self["pic"].moveTo(left, top, 1)
		self["pic"].startMoving()
		self["pic"].show()
		self.working = False

	def downloadPicError(self, error=""):
		print str(error)
		self["pic"].hide()
		self.working = False
		self.session.open(MessageBox, "Fehler beim Herunterladen des Eintrags!", MessageBox.TYPE_ERROR)
