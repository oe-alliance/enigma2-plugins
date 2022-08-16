from __future__ import print_function
from enigma import eServiceReference, iPlayableService, eServiceCenter
from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Label import Label
from Components.Button import Button
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from Components.ServiceEventTracker import ServiceEventTracker

from Screens.MessageBox import MessageBox

from Components.ConfigList import ConfigListScreen
from Components.config import *

from pyexpat import ExpatError

from os import path as os_path

path = "/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/"

# IMPORT VLC PLAYER PLUGIN STUFF
try:
	from Plugins.Extensions.VlcPlayer.VlcFileList import VlcFileList
	from Plugins.Extensions.VlcPlayer.VlcPlayList import VlcPlayList
	from Plugins.Extensions.VlcPlayer.VlcServerConfig import vlcServerConfig, VlcServerConfigScreen
	from Plugins.Extensions.VlcPlayer.VlcServerList import VlcServerList
	from Plugins.Extensions.VlcPlayer.VlcPlayer import VlcPlayer
except Exception as e:
	print("Media Center: Import VLC Stuff failed")


def addFavoriteVLCFolders():
	i = len(config.plugins.mc_vlc.folders)
	config.plugins.mc_vlc.folders.append(ConfigSubsection())
	config.plugins.mc_vlc.folders[i].name = ConfigText("", False)
	config.plugins.mc_vlc.folders[i].basedir = ConfigText("/", False)
	config.plugins.mc_vlc.foldercount.value = i + 1
	return i


for i in range(0, config.plugins.mc_vlc.foldercount.value):
	addFavoriteVLCFolders()


class MC_VLCServerlist(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)

		self.session = session
		self.serviceHandler = eServiceCenter.getInstance()

		#self.vlcServerConfig = VlcServerConfig()
		self.serverlist = VlcServerList()

		self.isVisible = True

		#self["currentdir"] = Label("List of known VLC-Server")
		self["serverlist"] = self.serverlist

		self["key_red"] = Button("Delete Server")
		self["key_green"] = Button("Add Server")
		self["key_yellow"] = Button("Edit Server")
		self["key_blue"] = Button("Play DVD")

		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions", "MoviePlayerActions"],
			{
			 "back": self.Exit,
			 "red": self.keyDelete,
			 "green": self.keyAddServer,
			 "yellow": self.keyEditServer,
			 "blue": self.keyDVD,
			 "up": self.up,
			 "down": self.down,
			 "left": self.left,
			 "right": self.right,
			 "ok": self.ok
			 }, -1)

		self.onLayoutFinish.append(self.updateServerlist)

	def updateServerlist(self):
		#self.serverlist.update(self.vlcServerConfig.getServerlist())
		self.serverlist.update(vlcServerConfig.getServerlist(), vlcServerConfig.getDefaultServer())

	def keyAddServer(self):
		#newServer = self.vlcServerConfig.new()
		newServer = vlcServerConfig.new()
		self.session.openWithCallback(self.addCallback, VlcServerConfigScreen, newServer)

	def addCallback(self, result, server):
		if result:
			#self.vlcServerConfig.save(server)
			vlcServerConfig.save(server)
			self.updateServerlist()
		else:
			#self.vlcServerConfig.delete(server)
			vlcServerConfig.delete(server)

	def keyDelete(self):
		self.session.openWithCallback(self.deleteCallback, MessageBox, _("Really delete this Server?"))

	def deleteCallback(self, result, server):
		if result:
			#self.vlcServerConfig.delete(self.serverlist.getSelection())
			vlcServerConfig.delete(self.serverlist.getSelection())
			self.updateServerlist()

	def keyDVD(self):
		server = self.serverlist.getSelection()
		if server is not None:
			dlg = self.session.open(VlcPlayer, server, self.serverlist)
			dlg.playfile("dvdsimple://" + server.getDvdPath(), "DVD")

	def keyEditServer(self):
		server = self.serverlist.getSelection()
		if server is not None:
			self.session.openWithCallback(self.editCallback, VlcServerConfigScreen, server)

	def editCallback(self, result, server):
		if result:
			#self.vlcServerConfig.save(server)
			vlcServerConfig.save(server)
			self.updateServerlist()
		else:
			#self.vlcServerConfig.cancel(server)
			vlcServerConfig.cancel(server)

	def up(self):
		self.serverlist.up()

	def down(self):
		self.serverlist.down()

	def left(self):
		self.serverlist.pageUp()

	def right(self):
		self.serverlist.pageDown()

	def ok(self):
		if self.serverlist.getSelection() is not None:
			self.session.open(MC_VLCMedialist, self.serverlist.getSelection()).update()

	def Exit(self):
		if self.isVisible == False:
			self.visibility()
			return

		# Stop currently playing service
		self.session.nav.stopService()

		# Save and exit
		config.plugins.mc_vlc.save()
		self.close()
#------------------------------------------------------------------------------------------


class MC_VLCMedialist(Screen):
	def __init__(self, session, server):
		Screen.__init__(self, session)
		self.session = session
		self.server = server
		self.filelistlabel = "Filelist:" + self.server.getBasedir()
		self.playlistlabel = "Playlist"

		self.defaultFilter = "(?i)\.(avi|mpeg|mpg|divx|flac|ogg|xvid|mp3|mp4|mov|ts|vob|wmv|mkv|iso|bin|m3u|pls|dat|xspf)$"

		#self.filelist = VlcFileList(server, self.defaultFilter)
		self.filelist = VlcFileList(self.getFilesAndDirsCB, server.getBasedir(), self.defaultFilter)

		self["filelist"] = self.filelist
		self["playlist"] = VlcPlayList(self.getPlaylistEntriesCB)
		self["listlabel"] = Label("")
		self["key_red"] = Button("Favorites")
		self["key_green"] = Button("Preview")
		self["key_yellow"] = Button("Refresh")
		self["key_blue"] = Button("Filter Off")

		self["currentdir"] = Label("Folder:")
		self["currentmedia"] = Label("")

		self["currentserver"] = Label("Server:")
		self["filterstatus"] = Label("Filter: On")

		self.curfavfolder = -1

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				#iPlayableService.evStart: self.doEofInternal,
				iPlayableService.evEnd: self.StopPlayback,
				iPlayableService.evEOF: self.StopPlayback,
				iPlayableService.evStopped: self.StopPlayback
			})

		self["actions"] = ActionMap(["WizardActions", "InfobarActions", "MovieSelectionActions", "MenuActions", "ShortcutActions", "MoviePlayerActions", "EPGSelectActions"],
			{
			 "back": self.Exit,
			 "red": self.JumpToFavs,
			 "green": self.showPreview,
			 "yellow": self.update,
			 "blue": self.keyFilter,
			 "up": self.up,
			 "down": self.down,
			 "left": self.left,
			 "right": self.right,
			 "ok": self.ok,
			 "menu": self.KeyMenu,
			 "nextBouquet": self.NextFavFolder,
			 "prevBouquet": self.PrevFavFolder,
			 "showMovies": self.visibility,
			 "leavePlayer": self.StopPlayback
			 }, -1)

		self.currentList = None
		self.playlistIds = []

		self.isVisible = True

		self.switchToFileList()

		self.onClose.append(self.__onClose)
		self.onShown.append(self.__onShown)

	def __onClose(self):
		try:
			for id in self.playlistIds:
				self.server.delete(id)
		except Exception as e:
			pass

	def __onShown(self):
		self.setTitle("VLC Server: " + (self.server.getName() or self.server.getHost()))
		self["currentserver"].setText("Server: " + (self.server.getName() or self.server.getHost()))

	def update(self):
		try:
			self.updateFilelist()
			self.updatePlaylist()
			if self.currentList == self["playlist"]:
				self.switchToPlayList()
			else:
				self.switchToFileList()
		except Exception as e:
			self.session.open(
				MessageBox, _("Error updating file- and playlist from server %s:\n%s" % (
						self.server.getName(), e)
					), MessageBox.TYPE_ERROR)

	def updatePlaylist(self):
		self["playlist"].update()

	def updateFilelist(self):
		self["filelist"].update()

	def keyFilter(self):
		if self["filelist"].regex is None:
			self["filelist"].changeRegex(self.defaultFilter)
			self["filterstatus"].setText("Filter: On")
			self["key_blue"].setText("Filter Off")
		else:
			self["filelist"].changeRegex(None)
			self["filterstatus"].setText("Filter: Off")
			self["key_blue"].setText("Filter On")
		try:
			self.updateFilelist()
		except Exception as e:
			self.session.open(
				MessageBox, _("Error updating filelist from server %s:\n%s" % (
						self.server.getName(), e)
					), MessageBox.TYPE_ERROR)

	def KeyMenu(self):
		if self.filelist.getCurrent() is not None:
			# Folder Options
			if self.filelist.getCurrent()[0][1]:
				self.currentDirectory = self.filelist.getCurrent()[0][0]
				foldername = self.currentDirectory.split('/')
				foldername = foldername[-1]
				self.session.open(FolderOptions, self.currentDirectory, foldername)

	def keyDvd(self):
		self.play("dvdsimple://" + self.server.getDvdPath(), "DVD")

	def up(self):
		self.currentList.up()

	def down(self):
		self.currentList.down()

	def left(self):
		self.currentList.pageUp()

	def right(self):
		self.currentList.pageDown()

	def play(self, media, name):
		#dlg = self.session.open(VlcPlayer, self.server, self.currentList)
		#dlg.playfile(media, name)
		self.server.play(self.session, media, name, self.currentList)

	def ok(self):
		media, name = self.currentList.activate()
		if media is not None:
			medianame = media.split('/')
			medianame = medianame[-1]
			self["currentmedia"].setText(("%s") % (medianame))
			if media.lower().endswith(".m3u") or media.lower().endswith(".pls") or media.lower().endswith(".xspf"):
				try:
					id = self.server.loadPlaylist(media)
					if id is not None:
						self.playlistIds.append(id)
						self.updatePlaylist()
				except Exception as e:
					self.session.open(
						MessageBox, _("Error loading playlist %s into server %s:\n%s" % (
								media, self.server.getName(), e)
							), MessageBox.TYPE_ERROR)
			elif media.lower().endswith(".iso"):
				self.play("dvdsimple://" + media, "DVD")
			else:
				self.play(media, name)
		elif name is not None:
			self.setLabel(name)
			self["currentdir"].setText("Folder: " + name)

	def showPreview(self):
		DEFAULT_VIDEO_PID = 0x44
		DEFAULT_AUDIO_PID = 0x45
		ENIGMA_SERVICE_ID = 0x1002

		url = None

		if self.filelist.getCurrent()[0][1]:
			return
		else:
			self.filename = self.filelist.getCurrent()[0][0]
		try:
			url = self.server.playFile(self.filename, DEFAULT_VIDEO_PID, DEFAULT_AUDIO_PID)
			print("[VLC] url: " + url)
		except Exception as e:
			self.session.open(MessageBox, _("Error with VLC server:\n%s" % e), MessageBox.TYPE_ERROR)

		if url is not None:
			#self.session.open(MessageBox, _("OPEN URL:\n%s" % url), MessageBox.TYPE_INFO)
			sref = eServiceReference(ENIGMA_SERVICE_ID, 0, url)
			print("sref valid=", sref.valid())
			sref.setData(0, DEFAULT_VIDEO_PID)
			sref.setData(1, DEFAULT_AUDIO_PID)
			self.session.nav.stopService()
			self.session.nav.playService(sref)

			media, name = self.currentList.activate()
			if media is not None:
				medianame = media.split('/')
				medianame = medianame[-1]
				self["currentmedia"].setText(("%s") % (medianame))

	def getFilesAndDirsCB(self, currentDirectory, regex):
		try:
			return self.server.getFilesAndDirs(currentDirectory, regex)
		except ExpatError as e:
			self.session.open(
				MessageBox, _("Error loading playlist into server %s:\n%s" % (
						self.server.getName(), e)
					), MessageBox.TYPE_ERROR)
			raise ExpatError
		except Exception as e:
			self.session.open(
				MessageBox, _("Error loading filelist into server %s:\n%s" % (
						self.server.getName(), e)
					), MessageBox.TYPE_ERROR)
		return None

	def getPlaylistEntriesCB(self):
		try:
			return self.server.getPlaylistEntries()
		except ExpatError as e:
			self.session.open(
				MessageBox, _("Error loading playlist into server %s:\n%s" % (
						self.server.getName(), e)
					), MessageBox.TYPE_ERROR)
		except Exception as e:
			self.session.open(
				MessageBox, _("Error loading playlist into server %s:\n%s" % (
						self.server.getName(), e)
					), MessageBox.TYPE_ERROR)
		return None

	def setLabel(self, text):
		if self.currentList == self["filelist"]:
			self.filelistlabel = "Filelist:" + text
		else:
			self.playlistlabel = text
		self["listlabel"].setText(text)

	def switchLists(self):
		if self.currentList == self["filelist"]:
			self.switchToPlayList()
		else:
			self.switchToFileList()

	def switchToFileList(self):
		self["playlist"].hide()
		self["filelist"].show()
		self.currentList = self["filelist"]
		self["listlabel"].setText(self.filelistlabel)
		#self["key_yellow"].setText("show playlist")

	def switchToPlayList(self):
		self["filelist"].hide()
		self["playlist"].show()
		self.currentList = self["playlist"]
		self["listlabel"].setText(self.playlistlabel)
		#self["key_yellow"].setText("show filelist")

	def NextFavFolder(self):
		if self.curfavfolder + 1 < config.plugins.mc_vlc.foldercount.value:
			self.curfavfolder += 1
			self.favname = config.plugins.mc_vlc.folders[self.curfavfolder].name.value
			self.currDir = config.plugins.mc_vlc.folders[self.curfavfolder].basedir.value
			self["currentdir"].setText("Folder: " + self.currDir)
			self["currentmedia"].setText(("%s") % (self.favname))
			self.changeDir(self.currDir)
		else:
			return

	def PrevFavFolder(self):
		if self.curfavfolder <= 0:
			return
		else:
			self.curfavfolder -= 1
			self.favname = config.plugins.mc_vlc.folders[self.curfavfolder].name.value
			self.currDir = config.plugins.mc_vlc.folders[self.curfavfolder].basedir.value
			self["currentdir"].setText("Folder: " + self.currDir)
			self["currentmedia"].setText(("%s") % (self.favname))
			self.changeDir(self.currDir)

	def JumpToFolder(self, jumpto=None):
		if jumpto is None:
			return
		else:
			self.changeDir(jumpto)
			self.currDir = jumpto

	def JumpToFavs(self):
		self.session.openWithCallback(self.JumpToFolder, MC_VLCFavoriteFolders)

	def changeDir(self, dir):
		print("[VLC] changeDir ", dir)
		try:
			self.currentList.changeDirectory(dir)
			self.updateFilelist()
		except Exception as e:
			self.session.open(MessageBox, _("Error switching directory:\n%s" % (e)), MessageBox.TYPE_ERROR)

	def visibility(self, force=1):
		if self.isVisible == True:
			self.isVisible = False
			self.hide()
		else:
			self.isVisible = True
			self.show()
			#self["list"].refresh()

	def StopPlayback(self):
		self.session.nav.stopService()
		self["currentmedia"].setText("")

		if self.isVisible == False:
			self.show()
			self.isVisible = True

	def Exit(self):
		if self.isVisible == False:
			self.visibility()
			return

		#if self.filelist.getCurrentDirectory() is None:
		#	config.plugins.mc_vlc.lastDir.value = ""
		#else:
		#	config.plugins.mc_vlc.lastDir.value = self.filelist.getCurrentDirectory()

		# Stop currently playing service
		self.session.nav.stopService()
		# Save and exit
		config.plugins.mc_vlc.save()
		self.close()
#------------------------------------------------------------------------------------------


class MC_VLCFavoriteFolders(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)

		self.list = []
		for i in range(0, config.plugins.mc_vlc.foldercount.value):
			cfg = config.plugins.mc_vlc.folders[i]
			self.list.append((cfg.name.value, int(i), cfg.basedir.value, "50"))

		self["favoritelist"] = List(self.list)
		self["title"] = StaticText("")

		self["key_red"] = Button("Delete")
		self["key_green"] = Button("Add Folder")
		self["key_yellow"] = Button("Edit Folder")
		self["key_blue"] = Button("Reset All")

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.JumpToFolder,
			"cancel": self.Exit,
			"red": self.keyDelete,
			"green": self.FavoriteFolderAdd,
			"yellow": self.FavoriteFolderEdit,
			"blue": self.ResetAll
		}, -1)

	def JumpToFolder(self):
		configfile.save()
		selection = self["favoritelist"].getCurrent()
		if selection is not None:
			self.close(selection[2])

	def FavoriteFolderEdit(self):
		selection = self["favoritelist"].getCurrent()
		if selection is None:
			return
		else:
			self.session.openWithCallback(self.conditionalEdit, FavoriteFolderEdit, selection[1])

	def FavoriteFolderAdd(self):
		self.session.openWithCallback(self.conditionalNew, FavoriteFolderAdd)

	def keyDelete(self):
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this favorite?"))

	def deleteConfirm(self, result):
		if result:
			selection = self["favoritelist"].getCurrent()
			id = int(selection[1])
			del config.plugins.mc_vlc.folders[id]
			config.plugins.mc_vlc.foldercount.value -= 1
			configfile.save()
			self.list.pop(id)
			# redraw list
			self["favoritelist"].setList(self.list)

	def ResetAll(self):
		# FIX MEEEEE !!!!!!!!!!!!!
		config.plugins.mc_vlc.foldercount.value = 0
		config.plugins.mc_vlc.foldercount.save()

		#for i in range(0, len(config.plugins.mc_vlc.folders)):
		for i in range(0, 100):
			try:
				del (config.plugins.mc_vlc.folders[i])
			except Exception as e:
				print("MC_ResetAll-DelaFavFailed")
		config.plugins.mc_vlc.folders.save()
		try:
			del (config.plugins.mc_vlc.folders)
		except Exception as e:
			print("MC_DELFAVFOLDERS-FAILED")
			#self.session.open(MessageBox,("Error: %s\n") % (Exception),  MessageBox.TYPE_INFO)
		try:
			del (config.plugins.mc_vlc.folders[0])
		except Exception as e:
			#self.session.open(MessageBox,("Error: %s\n") % (Exception),  MessageBox.TYPE_INFO)
			print("MC_DELFAV0-FAILED")

		config.plugins.mc_vlc.folders.save()
		configfile.save()
		self.close()

	def conditionalNew(self, added):
		if added == 0:
			return

		id = len(config.plugins.mc_vlc.folders) - 1
		self.list.insert(id, getConfigListEntry(str(config.plugins.mc_vlc.folders[id].name.value), id))

	def conditionalEdit(self, id):
		self.list.pop(id)
		self.list.insert(id, getConfigListEntry(str(config.plugins.mc_vlc.folders[id].name.value), id))

	def refresh(self):
		pass

	def Exit(self):
		configfile.save()
		self.close()
#------------------------------------------------------------------------------------------


class FavoriteFolderAdd(Screen, ConfigListScreen):
	skin = """
		<screen position="160,220" size="400,120" title="Media Center - Add VLC Favorite" >
			<widget name="config" position="10,10" size="380,100" />
		</screen>"""

	def __init__(self, session, directory="/", name=""):
		Screen.__init__(self, session)

		self["actions"] = NumberActionMap(["SetupActions", "OkCancelActions"],
		{
			"ok": self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self.id = config.plugins.mc_vlc.foldercount.value

		config.plugins.mc_vlc.folders.append(ConfigSubsection())
		config.plugins.mc_vlc.folders[self.id].name = ConfigText("", False)
		config.plugins.mc_vlc.folders[self.id].basedir = ConfigText("", False)

		config.plugins.mc_vlc.folders[self.id].name.value = name
		config.plugins.mc_vlc.folders[self.id].basedir.value = directory

		self.list = []
		self.list.append(getConfigListEntry(_("Name:"), config.plugins.mc_vlc.folders[self.id].name))
		self.list.append(getConfigListEntry(_("Directory:"), config.plugins.mc_vlc.folders[self.id].basedir))

		ConfigListScreen.__init__(self, self.list, session)

	def keyOK(self):
		config.plugins.mc_vlc.foldercount.value += 1
		config.plugins.mc_vlc.foldercount.save()
		config.plugins.mc_vlc.folders.save()
		self.close(1)

	def keyCancel(self):
		try:
			del (config.plugins.mc_vlc.folders[self.id])
		except Exception as e:
			print("MC_Settings_DelaFavFailed")
		self.close(0)
#------------------------------------------------------------------------------------------


class FavoriteFolderEdit(Screen, ConfigListScreen):
	skin = """
		<screen position="160,220" size="400,120" title="Media Center - Edit VLC Favorite" >
			<widget name="config" position="10,10" size="380,100" />
		</screen>"""

	def __init__(self, session, foldernum):
		Screen.__init__(self, session)

		self["actions"] = NumberActionMap(["SetupActions", "OkCancelActions"],
		{
			"ok": self.keyOK,
			"cancel": self.keyOK
		}, -1)

		self.list = []
		i = foldernum
		self.fn = foldernum

		self.list.append(getConfigListEntry(_("Name"), config.plugins.mc_vlc.folders[i].name))
		self.list.append(getConfigListEntry(_("Directory"), config.plugins.mc_vlc.folders[i].basedir))

		ConfigListScreen.__init__(self, self.list, session)

	def keyOK(self):
		config.plugins.mc_vlc.folders.save()
		self.close(self.fn)
#------------------------------------------------------------------------------------------


class FolderOptions(Screen):
	skin = """
		<screen position="160,200" size="400,200" title="Media Center - VLC Folder Options" >
			<widget source="pathlabel" transparent="1" render="Label" zPosition="2" position="0,180" size="380,20" font="Regular;16" />
			<widget source="menu" render="Listbox" zPosition="5" transparent="1" position="10,10" size="380,160" scrollbarMode="showOnDemand" >
				<convert type="StringList" />
			</widget>
		</screen>"""

	def __init__(self, session, directory, name):
		self.skin = FolderOptions.skin
		Screen.__init__(self, session)

		self.name = name
		self.directory = directory

		list = []
		#list.append(("Titel", "nothing", "entryID", "weight"))
		list.append(("Add Folder to Favorites", "addtofav", "menu_addtofav", "50"))

		self["menu"] = List(list)
		self["pathlabel"] = StaticText("Folder: " + directory)

		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"cancel": self.Exit,
			"ok": self.okbuttonClick
		}, -1)

	def okbuttonClick(self):
		print("okbuttonClick")
		selection = self["menu"].getCurrent()
		if selection is not None:
			if selection[1] == "addtofav":
				self.session.openWithCallback(self.FolderAdded, FavoriteFolderAdd, self.directory, self.name)
			else:
				self.close()
		else:
			self.close()

	def FolderAdded(self, added):
		self.close()

	def Exit(self):
		self.close()
