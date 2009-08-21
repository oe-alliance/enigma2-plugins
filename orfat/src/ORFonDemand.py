# -*- coding: utf-8 -*-
# ORF.at onDemand streaming module by AliAbdul
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Plugins.Extensions.VlcPlayer.VlcServerConfig import vlcServerConfig
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Tools.Directories import fileExists
from twisted.web.client import getPage

##########################################################

main_url = "http://ondemand.orf.at"

##########################################################

class ORFMain(Screen):
	skin = """
	<screen position="center,center" size="520,320" title="ORF.at onDemand" >
		<widget name="list" position="10,10" size="500,300" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		
		self.session = session	
		self.urls = []
		
		self["list"] = MenuList([])
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.close}, -1)
		
		self.onLayoutFinish.append(self.downloadList)

	def okClicked(self):
		if len(self.urls) > 0:
			idx = self["list"].getSelectedIndex()
			self.session.open(ORFSub, main_url+self.urls[idx])

	def downloadList(self):
		getPage(main_url+"/news/player.php?id=zib").addCallback(self.downloadListCallback).addErrback(self.downloadListError)

	def downloadListCallback(self, html=""):
		list = []
		if html.__contains__('class="list"'):
			idx = html.index('class="list"')
			html = html[idx:]
			while html.__contains__('href="'):
				idx = html.index('href="')
				html = html[idx+6:]
				idx = html.index('">')
				url = html[:idx]
				self.urls.append(url)
				html = html[idx+2:]
				idx = html.index('</a>')
				name = html[:idx]
				list.append(name)
				html = html[idx:]
		self["list"].setList(list)

	def downloadListError(self, error=""):
		print str(error)
		self.session.open(MessageBox, "Fehler beim Verbindungsversuch!", MessageBox.TYPE_ERROR)

##########################################################

class ORFSub(Screen):
	skin = """
	<screen position="center,center" size="520,320" title="ORF.at onDemand" >
		<widget name="list" position="10,10" size="500,300" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session, url):
		Screen.__init__(self, session)
		
		self.session = session
		self.url = url	
		self.urls = []
		
		self["list"] = MenuList([])
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.close}, -1)
		
		self.onLayoutFinish.append(self.downloadList)

	def okClicked(self):
		if len(self.urls) > 0:
			idx = self["list"].getSelectedIndex()
			movie = self.urls[idx]
			serverList = vlcServerConfig.getServerlist()
			if len(serverList) == 0:
				self.session.open(MessageBox, "Kein Server im vlc-Plugin konfiguriert!", MessageBox.TYPE_ERROR)
			elif len(serverList) == 1:
				serverList[0].play(self.session, movie, self["list"].getCurrent())
			else:
				list = []
				for x in serverList:
					list.append((x.getName(), x))
				self.session.openWithCallback(self.serverChosen, ChoiceBox, title="Waehle den vlc-Server...", list=list)

	def serverChosen(self, server):
		if server is not None:
			server[1].play(self.session, self.urls[self["list"].getSelectedIndex()], self["list"].getCurrent())

	def downloadList(self):
		getPage(self.url).addCallback(self.downloadListCallback).addErrback(self.downloadListError)

	def downloadListCallback(self, html=""):
		list = []
		while html.__contains__("javascript:jumpToClip('"):
			idx = html.index("javascript:jumpToClip('")
			html = html[idx+23:]
			idx = html.index('&offset')
			url = html[:idx]
			self.urls.append(url)
			idx = html.index('">')
			html = html[idx+2:]
			idx = html.index("<a/>")
			list.append(html[:idx])
		self["list"].setList(list)

	def downloadListError(self, error=""):
		print str(error)
		self.session.open(MessageBox, "Fehler beim Verbindungsversuch!", MessageBox.TYPE_ERROR)
