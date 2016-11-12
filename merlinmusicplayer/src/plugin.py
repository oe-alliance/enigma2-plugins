#
#  Merlin Music Player E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2010
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.

# for localized messages
from . import _
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Label import Label
from enigma import RT_VALIGN_CENTER, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, gFont, eListbox,ePoint, eListboxPythonMultiContent
from Components.FileList import FileList
from enigma import eServiceReference, eTimer
from os import path as os_path, mkdir as os_mkdir, listdir as os_listdir, walk as os_walk, access as os_access, W_OK as os_W_OK
from Components.ProgressBar import ProgressBar
from twisted.internet import reactor, defer
from twisted.web import client
from twisted.web.client import HTTPClientFactory, downloadPage
from enigma import getDesktop
from Screens.MessageBox import MessageBox
from Screens.InfoBar import InfoBar
from Components.GUIComponent import GUIComponent
from enigma import ePicLoad
from xml.etree.cElementTree import fromstring as cet_fromstring
from urllib import quote
from urlparse import urlparse
from Components.ScrollLabel import ScrollLabel
from Components.AVSwitch import AVSwitch
from Tools.Directories import fileExists, resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ServicePosition import ServicePositionGauge
from Screens.InfoBarGenerics import  InfoBarSeek, InfoBarNotifications
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from enigma import iPlayableService, iServiceInformation
from Components.Sources.StaticText import StaticText
from Screens.ChoiceBox import ChoiceBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.BoundFunction import boundFunction
from sqlite3 import dbapi2 as sqlite
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, USLT
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
from mutagen.oggvorbis import OggVorbis
from datetime import timedelta as datetime_timedelta
from time import time
from random import shuffle, randrange
import re
import skin
from Components.config import config, ConfigSubsection, ConfigDirectory, ConfigYesNo, ConfigInteger, getConfigListEntry, configfile
from Components.ConfigList import ConfigListScreen

from Components.SystemInfo import SystemInfo
from enigma import eServiceCenter, getBestPlayableServiceReference
from Components.VideoWindow import VideoWindow
from ServiceReference import ServiceReference
from Screens.EpgSelection import EPGSelection
from Screens.EventView import  EventViewEPGSelect
from enigma import ePoint, eEPGCache
from Screens.InfoBarGenerics import NumberZap
try:
	from Plugins.SystemPlugins.PiPServiceRelation.plugin import getRelationDict, CONFIG_FILE
	plugin_PiPServiceRelation_installed = True
except:
	plugin_PiPServiceRelation_installed = False

START_MERLIN_PLAYER_SCREEN_TIMER_VALUE = 7000

config.plugins.merlinmusicplayer = ConfigSubsection()
config.plugins.merlinmusicplayer.startlastsonglist = ConfigYesNo(default = True)
config.plugins.merlinmusicplayer.lastsonglistindex = ConfigInteger(-1)
config.plugins.merlinmusicplayer.databasepath = ConfigDirectory(default = "/media/hdd/")
config.plugins.merlinmusicplayer.usegoogleimage = ConfigYesNo(default = True)
config.plugins.merlinmusicplayer.googleimagepath = ConfigDirectory(default = "/media/hdd/")
config.plugins.merlinmusicplayer.usescreensaver = ConfigYesNo(default = True)
config.plugins.merlinmusicplayer.screensaverwait = ConfigInteger(1,limits = (1, 60))
config.plugins.merlinmusicplayer.idreamextendedpluginlist = ConfigYesNo(default = True)
config.plugins.merlinmusicplayer.merlinmusicplayerextendedpluginlist = ConfigYesNo(default = True)
config.plugins.merlinmusicplayer.defaultfilebrowserpath = ConfigDirectory(default = "/media/hdd/")
config.plugins.merlinmusicplayer.rememberlastfilebrowserpath = ConfigYesNo(default = True)
config.plugins.merlinmusicplayer.idreammainmenu = ConfigYesNo(default = False)
config.plugins.merlinmusicplayer.merlinmusicplayermainmenu = ConfigYesNo(default = False)

from enigma import ePythonMessagePump
from threading import Thread, Lock

class ThreadQueue:
	def __init__(self):
		self.__list = [ ]
		self.__lock = Lock()

	def push(self, val):
		lock = self.__lock
		lock.acquire()
		self.__list.append(val)
		lock.release()

	def pop(self):
		lock = self.__lock
		lock.acquire()
		ret = self.__list.pop()
		lock.release()
		return ret

THREAD_WORKING = 1
THREAD_FINISHED = 2

class PathToDatabase(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.__running = False
		self.__cancel = False
		self.__path = None
		self.__messages = ThreadQueue()
		self.__messagePump = ePythonMessagePump()

	def __getMessagePump(self):
		return self.__messagePump

	def __getMessageQueue(self):
		return self.__messages

	def __getRunning(self):
		return self.__running

	def Cancel(self):
		self.__cancel = True

	MessagePump = property(__getMessagePump)
	Message = property(__getMessageQueue)
	isRunning = property(__getRunning)

	def Start(self, path):
		if not self.__running:
			self.__path = path
			self.start()

	def run(self):
		mp = self.__messagePump
		self.__running = True
		self.__cancel = False
		if self.__path:
			connection = OpenDatabase()
			if connection is not None:
				connection.text_factory = str
				cursor = connection.cursor()
				counter = 0
				checkTime = 0
				for root, subFolders, files in os_walk(self.__path):
					if self.__cancel:
						break
					for filename in files:
						if self.__cancel:
							break
						cursor.execute('SELECT song_id FROM Songs WHERE filename = "%s";' % os_path.join(root,filename))
						row = cursor.fetchone()
						if row is None:
							audio, isAudio, title, genre,artist,album,tracknr,track,date,length,bitrate = getID3Tags(root,filename)
							if  audio:	
								# 1. Artist
								artistID = -1
								cursor.execute('SELECT artist_id FROM Artists WHERE artist = "%s";' % (artist.replace('"','""')))

								row = cursor.fetchone()
								if row is None:
										cursor.execute('INSERT INTO Artists (artist) VALUES("%s");' % (artist.replace('"','""')))
										artistID = cursor.lastrowid
								else:
										artistID = row[0]
								# 2. Album
								albumID = -1
								cursor.execute('SELECT album_id FROM Album WHERE album_text = "%s";' % (album.replace('"','""')))
								row = cursor.fetchone()
								if row is None:
										cursor.execute('INSERT INTO Album (album_text) VALUES("%s");' % (album.replace('"','""')))
										albumID = cursor.lastrowid
								else:
										albumID = row[0]

								# 3. Genre
								genreID = -1
								cursor.execute('SELECT genre_id FROM Genre WHERE genre_text = "%s";' % (genre.replace('"','""')))
								row = cursor.fetchone()
								if row is None:
										cursor.execute('INSERT INTO Genre (genre_text) VALUES("%s");' % (genre.replace('"','""')))
										genreID = cursor.lastrowid
								else:
										genreID = row[0]

								# 4. Songs
								try:
									cursor.execute("INSERT INTO Songs (filename,title,artist_id,album_id,genre_id,tracknumber, bitrate, length, track, date) VALUES(?,?,?,?,?,?,?,?,?,?);" , (os_path.join(root,filename),title,artistID,albumID,genreID, tracknr, bitrate, length, track, date))
									self.__messages.push((THREAD_WORKING, _("%s\n added to database") % os_path.join(root,filename)))
									mp.send(0)
									counter +=1
								except sqlite.IntegrityError:
									self.__messages.push((THREAD_WORKING, _("%s\n already exists in database!") % os_path.join(root,filename)))
									mp.send(0)
								audio = None
						elif time() - checkTime >= 0.1: # update interval for gui
							self.__messages.push((THREAD_WORKING, _("%s\n already exists in database!") % os_path.join(root,filename)))
							mp.send(0)
							checkTime = time()

				if not self.__cancel:
					connection.commit()
				cursor.close()
				connection.close()
				if self.__cancel:
					self.__messages.push((THREAD_FINISHED, _("Process aborted.\n 0 files added to database!\nPress OK to close.") ))
				else:
					self.__messages.push((THREAD_FINISHED, _("%d files added to database!\nPress OK to close.") % counter))
			else:
				self.__messages.push((THREAD_FINISHED, _("Error!\nCan not open database!\nCheck if save folder is correct and writeable!\nPress OK to close.") ))
			mp.send(0)
			self.__running = False
			Thread.__init__(self)

pathToDatabase = PathToDatabase()

class iDreamAddToDatabase(Screen):
	skin = """<screen name="iDreamAddToDatabase" position="center,center" size="560,320" title="Add music files to iDream database">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget name="output" position="10,10" size="540,300" valign="center" halign="center" font="Regular;22" />
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;20" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;20" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""
	def __init__(self, session, initDir):
		Screen.__init__(self, session)
		self.setTitle(_("Add music files to iDream database"))
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"back": self.cancel,
			"green": self.green,
			"red": self.cancel,
			"ok": self.green,

		}, -1)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Close"))
		self["output"] = Label()
		self.onClose.append(self.__onClose)
		pathToDatabase.MessagePump.recv_msg.get().append(self.gotThreadMsg)
		if not pathToDatabase.isRunning and initDir:
			pathToDatabase.Start(initDir)

	def gotThreadMsg(self, msg):
		msg = pathToDatabase.Message.pop()
		self["output"].setText(msg[1])
		if msg[0] == THREAD_FINISHED:
			self["key_red"].setText("")

	def green(self):
		self.close()

	def cancel(self):
		if pathToDatabase.isRunning:
			pathToDatabase.Cancel()

	def __onClose(self):
		pathToDatabase.MessagePump.recv_msg.get().remove(self.gotThreadMsg)	

class myHTTPClientFactory(HTTPClientFactory):
	def __init__(self, url, method='GET', postdata=None, headers=None,
	agent="SHOUTcast", timeout=0, cookies=None,
	followRedirect=1, lastModified=None, etag=None):
		HTTPClientFactory.__init__(self, url, method=method, postdata=postdata,
		headers=headers, agent=agent, timeout=timeout, cookies=cookies,followRedirect=followRedirect)

def sendUrlCommand(url, contextFactory=None, timeout=60, *args, **kwargs):
	parsed = urlparse(url)
	scheme = parsed.scheme
	host = parsed.hostname
	port = parsed.port or (443 if scheme == 'https' else 80)
	factory = myHTTPClientFactory(url, *args, **kwargs)
	reactor.connectTCP(host, port, factory, timeout=timeout)
	return factory.deferred

class MethodArguments:
	def __init__(self, method = None, arguments = None):
		self.method = method
		self.arguments = arguments

class CacheList:
	def __init__(self, cache = True, index = 0, listview = [], headertext = "", methodarguments = None):
		self.cache = cache
		self.index = index
		self.listview = listview
		self.headertext = headertext
		self.methodarguments = methodarguments

class Item:
	def __init__(self, text = "", mode = 0, id = -1, navigator = False, artistID = 0, albumID = 0, title = "", artist = "", filename = "", bitrate = None, length = "", genre = "", track = "", date = "", album = "", playlistID = 0,  genreID = 0, songID = 0, join = True, PTS = None):
		self.text = text
		self.mode = mode
		self.navigator = navigator
		self.artistID = artistID
		self.albumID = albumID
		self.title = title
		self.artist = artist
		self.filename = filename
		if bitrate is not None:
			if join:
				self.bitrate = "%d Kbps" % bitrate
			else:
				self.bitrate = bitrate
		else:
			self.bitrate = ""
		self.length = length
		self.genre = genre
		if track is not None:
			self.track = _("Track %s") % track
		else:
			self.track = ""
		if date is not None:
			if join:
				self.date = " (%s)" % date
			else:
				self.date = date
		else:
			self.date = ""
		self.album = album
		self.playlistID = playlistID
		self.genreID = genreID
		self.songID = songID
		self.PTS = PTS

def OpenDatabase():
		connectstring = os_path.join(config.plugins.merlinmusicplayer.databasepath.value ,"iDream.db")
		db_exists = False
		if os_path.exists(connectstring):
			db_exists = True
		try:
			connection = sqlite.connect(connectstring)
			if not os_access(connectstring, os_W_OK):
				print "[MerlinMusicPlayer] Error: database file needs to be writable, can not open %s for writing..." % connectstring
				connection.close()
				return None
		except:
			print "[MerlinMusicPlayer] unable to open database file: %s" % connectstring
			return None
		if not db_exists:
				connection.execute('CREATE TABLE IF NOT EXISTS Songs (song_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL UNIQUE, title TEXT, artist_id INTEGER, album_id INTEGER, genre_id INTEGER, tracknumber INTEGER, bitrate INTEGER, length TEXT, track TEXT, date TEXT, lyrics TEXT);')
				connection.execute('CREATE TABLE IF NOT EXISTS Artists (artist_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, artist TEXT NOT NULL UNIQUE);')
				connection.execute('CREATE TABLE IF NOT EXISTS Album (album_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, album_text TEXT NOT NULL UNIQUE);')
				connection.execute('CREATE TABLE IF NOT EXISTS Genre (genre_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, genre_text TEXT NOT NULL UNIQUE);')
				connection.execute('CREATE TABLE IF NOT EXISTS Playlists (playlist_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, playlist_text TEXT NOT NULL);')
				connection.execute('CREATE TABLE IF NOT EXISTS Playlist_Songs (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, playlist_id INTEGER NOT NULL, song_id INTEGER NOT NULL);')
				connection.execute('CREATE TABLE IF NOT EXISTS CurrentSongList (ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, song_id INTEGER, filename TEXT NOT NULL, title TEXT, artist TEXT, album TEXT, genre TEXT, bitrate TEXT, length TEXT, track TEXT, date TEXT, PTS INTEGER);')
		return connection

def getEncodedString(value):
	returnValue = ""
	try:
		returnValue = value.encode("utf-8", 'ignore')
	except UnicodeDecodeError:
		try:
			returnValue = value.encode("iso8859-1", 'ignore')
		except UnicodeDecodeError:
			try:
				returnValue = value.decode("cp1252").encode("utf-8")
			except UnicodeDecodeError:
				returnValue = "n/a"
	return returnValue

def getID3Tags(root,filename):
	audio = None
	isFlac = False
	isAudio = True
	title = ""
	genre = ""
	artist = ""
	album = ""
	tracknr = -1
	track = None
	date = None
	length = ""
	bitrate = None
	if filename.lower().endswith(".mp3"):
		try: audio = MP3(os_path.join(root,filename), ID3 = EasyID3)
		except: audio = None
	elif filename.lower().endswith(".flac"):
		try: 
			audio = FLAC(os_path.join(root,filename))
			isFlac = True
		except: audio = None
	elif filename.lower().endswith(".m4a"):
		try: audio = EasyMP4(os_path.join(root,filename))
		except: audio = None
	elif filename.lower().endswith(".ogg"):
		try: audio = OggVorbis(os_path.join(root,filename))
		except: audio = None
	else:
		isAudio = False
	if audio:
		title = getEncodedString(audio.get('title', [filename])[0])
		try:
			# list index out of range workaround
			genre = getEncodedString(audio.get('genre', ['n/a'])[0])
		except:
			genre = "n/a"
		artist = getEncodedString(audio.get('artist', ['n/a'])[0])
		album = getEncodedString(audio.get('album', ['n/a'])[0])
		try:
			tracknr = int(audio.get('tracknumber', ['-1'])[0].split("/")[0])
		except:
			tracknr = -1
		track = getEncodedString(audio.get('tracknumber', ['n/a'])[0])
		date = getEncodedString(audio.get('date', ['n/a'])[0])
		try:
			length = str(datetime_timedelta(seconds=int(audio.info.length))).encode("utf-8", 'ignore')
		except:
			length = -1
		if not isFlac:
			bitrate = audio.info.bitrate / 1000
		else:
			bitrate = None
	else:
		if isAudio:
			title = os_path.splitext(os_path.basename(filename))[0]
			genre = "n/a"
			artist = "n/a"
			album = "n/a"
			tracknr = -1
			track = None
			date = None
			length = ""
			bitrate = None

	return audio, isAudio, title, genre ,artist, album, tracknr, track, date, length, bitrate

class MerlinMusicPlayerScreenSaver(Screen):

	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:
		skin = """
			<screen name="MerlinMusicPlayerScreenSaver" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#00000000" title="MerlinMusicPlayerScreenSaver">
			<widget name="coverArt" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/no_coverArt.png" position="200,77" size="238,238" transparent="1" alphatest="blend" />
			<widget name="display" position="200,315" size="1280,24" zPosition="1" transparent="1" font="Regular;20" foregroundColor="#fcc000" />
			</screen>"""
	elif sz_w == 1024:
		skin = """
			<screen name="MerlinMusicPlayerScreenSaver" position="0,0" size="1024,576" flags="wfNoBorder" backgroundColor="#00000000" title="MerlinMusicPlayerScreenSaver">
			<widget name="coverArt" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/no_coverArt.png" position="200,77" size="238,238" transparent="1" alphatest="blend" />
			<widget name="display" position="200,315" size="1024,24" zPosition="1" transparent="1" font="Regular;20" foregroundColor="#fcc000" />
			</screen>"""

	else:
		skin = """
			<screen name="MerlinMusicPlayerScreenSaver" position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="#00000000" title="MerlinMusicPlayerScreenSaver">
			<widget name="coverArt" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/no_coverArt.png" position="200,77" size="238,238" transparent="1" alphatest="blend" />
			<widget name="display" position="200,315" size="720,24" zPosition="1" transparent="1" font="Regular;20" foregroundColor="#fcc000" />
			</screen>"""
		
	
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EventViewActions"],
		{
			"back": self.close,
			"right": self.close,
			"left": self.close,
			"up": self.close,
			"down": self.close,
			"ok": self.close,
			"pageUp": self.close,
			"pageDown": self.close,
			"yellow": self.close,
			"blue": self.close,
			"red": self.close,
			"green": self.close,
			"right": self.close,
			"left": self.close,
			"prevBouquet": self.close,
			"nextBouquet": self.close,
			"info": self.close,
		}, -1)
		self["coverArt"] = MerlinMediaPixmap()
		self.coverMoveTimer = eTimer()
		self.coverMoveTimer.timeout.get().append(self.moveCoverArt)
		self.coverMoveTimer.start(1)
		self["display"] = Label()

	def updateDisplayText(self, text):
		self["display"].setText(text)

	def updateLCD(self, text, line):
		self.summaries.setText(text,line)

	def updateCover(self, filename = None, modus = 0):
		print "[MerlinMusicPlayerScreenSaver] updating coverart with filename = %s and modus = %d" % (filename, modus)
		if modus == 0:
			if filename:
				self["coverArt"].showCoverFromFile(filename)
			else:
				self["coverArt"].showDefaultCover()
		elif modus == 1:
			self["coverArt"].showDefaultCover()
		elif modus == 2:
			self["coverArt"].embeddedCoverArt()
		elif modus == 3:
			self["coverArt"].updateCoverArt(filename)
		elif modus == 4:
			self["coverArt"].showCoverFromFile(filename)

	def moveCoverArt(self):
		x = randrange(getDesktop(0).size().width()-238)
		y = randrange(getDesktop(0).size().height()-238-28)
		self["coverArt"].move(ePoint(x,y))
		self["display"].move(ePoint(x,y+240))
		self.coverMoveTimer.start(15000)

	def createSummary(self):
		return MerlinMusicPlayerLCDScreen

class MerlinMusicPlayerTV(MerlinMusicPlayerScreenSaver):

	w = getDesktop(0).size().width()
	h = getDesktop(0).size().height()
	if w == 1280:
		cy = 606
	else:
		cy = 462
	dx = 135
	cx = 66
	dy = cy + 20
	dw = w - dx - cx

	skin = """
		<screen backgroundColor="transparent" flags="wfNoBorder" position="0,0" size="%d,%d" title="MerlinMusicPlayerTV">
			<widget backgroundColor="transparent" name="video" position="0,0" size="%d,%d" zPosition="1"/>
			<widget name="coverArt" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/no_coverArt.png" position="%d,%d" size="64,64" transparent="1" alphatest="blend" zPosition="2" />
			<widget name="display" position="%d,%d" size="%d,24" zPosition="2" backgroundColor="#33000000" font="Regular;20" foregroundColor="#fcc000" />
		</screen>""" % (w,h,w,h,cx,cy,dx,dy,dw)

	def __init__(self, session, currentService, servicelist):
		self.session = session
		Screen.__init__(self, session)
		self.setTitle(_("Merlin Music Player TV"))
		self.onClose.append(self.__onClose)
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ChannelSelectBaseActions", "ChannelSelectEPGActions"], 
		{
			"cancel": self.close,
			"ok": self.showHide,
			"right": self.nextService,
			"left": self.prevService,
			"nextBouquet": self.nextBouquet,
			"prevBouquet": self.prevBouquet,
			"showEPGList": self.openEventView,
		}, -1)
		self["actions2"] = NumberActionMap(["NumberActions"],
		{
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
		}, -1)
		self.epgcache = eEPGCache.getInstance()
		self.currentService = currentService
		self.servicelist = servicelist
		self.currentPiP = ""
		self["coverArt"] = MerlinMediaPixmap()
		self["display"] = Label()
		self["video"] = VideoWindow(fb_width = getDesktop(0).size().width(), fb_height = getDesktop(0).size().height())
		if plugin_PiPServiceRelation_installed:
			self.pipServiceRelation = getRelationDict()
		else:
			self.pipServiceRelation = {}
		try:
			if self.currentService:
				current = ServiceReference(self.currentService)
				cur_service = current.ref
		except:
			cur_service = None
		if cur_service is None:
			try:
				if self.servicelist:
					current = ServiceReference(self.servicelist.getCurrentSelection())
					service = current.ref
					self.playService(service)
			except:
				pass
		else:
			self.playService(cur_service)

		self.showHideTimer = eTimer()
		self.showHideTimer.timeout.get().append(self.showHideTimerTimeout)
		self.idx = config.usage.infobar_timeout.index
		if self.idx:
			self.showHideTimer.start(self.idx * 1000)
		self.displayShown = True

	def showHide(self):
		if self.displayShown:
			if self.showHideTimer.isActive():
				self.showHideTimer.stop()
			self["coverArt"].hide()
			self["display"].hide()
		else:
			self["coverArt"].show()
			self["display"].show()
			if self.idx:
				self.showHideTimer.start(self.idx * 1000)
		self.displayShown = not self.displayShown

	def showHideTimerTimeout(self):
		self.showHide()

	def updateDisplayText(self, text):
		if self.showHideTimer.isActive():
			self.showHideTimer.stop()
		self["display"].setText(text)
		self.displayShown = False
		self.showHide()

	def keyNumberGlobal(self, number):
		if self.servicelist is not None:
			self.session.openWithCallback(self.numberEntered, NumberZap, number, self.searchNumber)

	def numberEntered(self, retval):
		if retval > 0:
			self.zapToNumber(retval)

	def numberEntered(self, service = None, bouquet = None):
		if service:
			self.selectAndStartService(service, bouquet)

	def searchNumberHelper(self, serviceHandler, num, bouquet):
		servicelist = serviceHandler.list(bouquet)
		if servicelist:
			serviceIterator = servicelist.getNext()
			while serviceIterator.valid():
				if num == serviceIterator.getChannelNum():
					return serviceIterator
				serviceIterator = servicelist.getNext()
		return None

	def searchNumber(self, number, firstBouquetOnly = False):
		bouquet = self.servicelist.getRoot()
		service = None
		serviceHandler = eServiceCenter.getInstance()
		if not firstBouquetOnly:
			service = self.searchNumberHelper(serviceHandler, number, bouquet)
		if config.usage.multibouquet.value and not service:
			bouquet = self.servicelist.bouquet_root
			bouquetlist = serviceHandler.list(bouquet)
			if bouquetlist:
				bouquet = bouquetlist.getNext()
				while bouquet.valid():
					if bouquet.flags & eServiceReference.isDirectory:
						service = self.searchNumberHelper(serviceHandler, number, bouquet)
						if service:
							playable = not (service.flags & (eServiceReference.isMarker|eServiceReference.isDirectory)) or (service.flags & eServiceReference.isNumberedMarker)
							if not playable:
								service = None
							break
						if config.usage.alternative_number_mode.value or firstBouquetOnly:
							break
					bouquet = bouquetlist.getNext()
		return service, bouquet

	def selectAndStartService(self, service, bouquet):
		if service:
			if self.servicelist.getRoot() != bouquet:
				self.servicelist.clearPath()
				if self.servicelist.bouquet_root != bouquet:
					self.servicelist.enterPath(self.servicelist.bouquet_root)
				self.servicelist.enterPath(bouquet)
			self.servicelist.setCurrentSelection(service)
			current = ServiceReference(self.servicelist.getCurrentSelection())
			self.playService(current.ref)

	def zapToNumber(self, number):
		service, bouquet = self.searchNumber(number)
		self.selectAndStartService(service, bouquet)

	def nextService(self):
		if self.servicelist is not None:
			if self.servicelist.inBouquet():
				prev = self.servicelist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value and self.servicelist.atEnd():
							self.servicelist.nextBouquet()
						else:
							self.servicelist.moveDown()
						cur = self.servicelist.getCurrentSelection()
						if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
							break
			else:
				self.servicelist.moveDown()
			if self.isPlayable():
				current = ServiceReference(self.servicelist.getCurrentSelection())
				self.playService(current.ref)
			else:
				self.nextService()

	def prevService(self):
		if self.servicelist is not None:
			if self.servicelist.inBouquet():
				prev = self.servicelist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value:
							if self.servicelist.atBegin():
								self.servicelist.prevBouquet()
						self.servicelist.moveUp()
						cur = self.servicelist.getCurrentSelection()
						if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
							break
			else:
				self.servicelist.moveUp()
			if self.isPlayable():
				current = ServiceReference(self.servicelist.getCurrentSelection())
				self.playService(current.ref)
			else:
				self.prevService()

	def isPlayable(self):
		current = ServiceReference(self.servicelist.getCurrentSelection())
		return not (current.ref.flags & (eServiceReference.isMarker|eServiceReference.isDirectory))

	def nextBouquet(self):
		if self.servicelist is not None:
			if config.usage.multibouquet.value:
				self.servicelist.nextBouquet()
				current = ServiceReference(self.servicelist.getCurrentSelection())
				self.playService(current.ref)

	def prevBouquet(self):
		if self.servicelist is not None:
			if config.usage.multibouquet.value:
				self.servicelist.prevBouquet()
				current = ServiceReference(self.servicelist.getCurrentSelection())
				self.playService(current.ref)

	def openSingleServiceEPG(self):
		if self.servicelist is not None:
			current = ServiceReference(self.servicelist.getCurrentSelection())
			self.session.open(EPGSelection, current.ref)

	def openEventView(self):
		if self.servicelist is not None: 
			epglist = [ ]
			self.epglist = epglist
			service = ServiceReference(self.servicelist.getCurrentSelection())
			ref = service.ref
			evt = self.epgcache.lookupEventTime(ref, -1)
			if evt:
				epglist.append(evt)
			evt = self.epgcache.lookupEventTime(ref, -1, 1)
			if evt:
				epglist.append(evt)
			if epglist:
				self.session.open(EventViewEPGSelect, epglist[0], service, self.eventViewCallback, self.openSingleServiceEPG, self.openMultiServiceEPG, self.openSimilarList)

	def eventViewCallback(self, setEvent, setService, val):
		epglist = self.epglist
		if len(epglist) > 1:
			tmp = epglist[0]
			epglist[0] = epglist[1]
			epglist[1] = tmp
			setEvent(epglist[0])

	def getBouquetServices(self, bouquet):
		services = [ ]
		Servicelist = eServiceCenter.getInstance().list(bouquet)
		if not Servicelist is None:
			while True:
				service = Servicelist.getNext()
				if not service.valid():
					break
				if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker):
					continue
				services.append(ServiceReference(service))
		return services

	def openMultiServiceEPG(self):
		if self.servicelist is not None:
			bouquet = self.servicelist.getRoot()
			services = self.getBouquetServices(bouquet)
			if services:
				self.session.open(EPGSelection, services)

	def openSimilarList(self, eventid, refstr):
		self.session.open(EPGSelection, refstr, None, eventid)

	def playService(self, service):
		current_service = service
		n_service = self.pipServiceRelation.get(service.toString(),None)
		if n_service is not None:
			service = eServiceReference(n_service)
		if service and (service.flags & eServiceReference.isGroup):
			ref = getBestPlayableServiceReference(service, eServiceReference())
		else:
			ref = service
		if ref and ref.toString() != self.currentPiP:
			self.pipservice = eServiceCenter.getInstance().play(ref)
			if self.pipservice and not self.pipservice.setTarget(1):
				self.pipservice.start()
				if self.servicelist is not None:
					self.servicelist.setCurrentSelection(current_service) 
				self.currentPiP = current_service.toString()
			else:
				self.pipservice = None
				self.currentPiP = ""
		else:
			self.pipservice = None
			self.currentPiP = ""

	def __onClose(self):
		self.pipservice = None
		self.currentPiP = ""
		if self.showHideTimer.isActive():
			self.showHideTimer.stop()

class MerlinMusicPlayerScreen(Screen, InfoBarBase, InfoBarSeek, InfoBarNotifications):
	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:
		skin = """
			<screen name="MerlinMusicPlayerScreen" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#00000000" title="iDream">
			<eLabel backgroundColor="#999999" position="178,112" size="924,2" zPosition="1"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="178,104" size="250,20" text="MERLIN  MUSIC  PLAYER" valign="center" zPosition="2"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="852,104" size="250,20" text="WWW.DREAMBOX-TOOLS.INFO" valign="center" zPosition="2"/>
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/mmp3pHD.png" position="128,72" size="1024,576"/>
			<widget name="coverArt" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/no_coverArt.png" position="328,149" size="238,238" transparent="1" alphatest="blend" />
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr.png" position="688,232" size="150,20" transparent="1" zPosition="1"/>
			<widget name="title" position="362,415" size="600,28" zPosition="1" transparent="1" font="Regular;24" foregroundColor="#fcc000" />
			<widget name="album" position="362,462" size="600,22" zPosition="1" transparent="1" font="Regular;18" foregroundColor="#999999" />
			<widget name="artist" position="362,492" size="600,22" zPosition="1" transparent="1" font="Regular;18" foregroundColor="#999999" />
			<widget name="genre" position="362,522" size="600,22" zPosition="1" transparent="1" font="Regular;18" foregroundColor="#999999" />
			<widget name="nextTitle" position="362,562" size="600,22" zPosition="1" transparent="1" font="Regular;16" foregroundColor="#f0f0f0" />
			<widget name="PositionGauge" position="664,264" size="198,14" pointer="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/progressbar.png:198,0" seek_pointer="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/progressbar.png:198,0" transparent="1"/>
			<widget source="session.CurrentService" render="Label" position="873,267" size="116,18" zPosition="1" font="Regular;18" halign="left" foregroundColor="#999999" transparent="1" >
					<convert type="ServicePosition">Length,ShowHours</convert>
			</widget>
			<widget source="session.CurrentService" render="Label" position="684,292" size="198,20" zPosition="1" font="Regular;20" halign="left" foregroundColor="#fcc000" transparent="1" >
					<convert type="ServicePosition">Position,ShowHours</convert>
			</widget>
			<widget name="shuffle" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/placeholder1.png,/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr_shuf.png" position="598,275" size="53,34" transparent="1" alphatest="on"/>
			<widget name="repeat" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/placeholder1.png,/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr_rep.png" position="598,239" size="53,34" transparent="1" alphatest="on"/>
			<widget name="dvrStatus" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr_pl.png,/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr_pau.png" position="683,227" size="160,39" transparent="1" alphatest="on"/>
			</screen>"""
	elif sz_w == 1024:
		skin = """
			<screen name="MerlinMusicPlayerScreen" position="0,0" size="1024,576" flags="wfNoBorder" backgroundColor="#00000000" title="iDream">
			<eLabel backgroundColor="#999999" position="50,40" size="924,2" zPosition="1"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="50,32" size="250,20" text="MERLIN  MUSIC  PLAYER" valign="center" zPosition="2"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="724,32" size="250,20" text="WWW.DREAMBOX-TOOLS.INFO" valign="center" zPosition="2"/>
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/mmp3pHD.png" position="0,0" size="1024,576"/>
			<widget name="coverArt" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/no_coverArt.png" position="200,77" size="238,238" transparent="1" alphatest="blend" />
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr.png" position="560,160" size="150,20" transparent="1" zPosition="1"/>
			<widget name="title" position="234,343" size="600,28" zPosition="1" transparent="1" font="Regular;24" foregroundColor="#fcc000" />
			<widget name="album" position="234,390" size="600,22" zPosition="1" transparent="1" font="Regular;18" foregroundColor="#999999" />
			<widget name="artist" position="234,420" size="600,22" zPosition="1" transparent="1" font="Regular;18" foregroundColor="#999999" />
			<widget name="genre" position="234,450" size="600,22" zPosition="1" transparent="1" font="Regular;18" foregroundColor="#999999" />
			<widget name="nextTitle" position="234,490" size="600,22" zPosition="1" transparent="1" font="Regular;16" foregroundColor="#f0f0f0" />
			<widget name="PositionGauge" position="536,197" size="198,14" pointer="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/progressbar.png:198,0" seek_pointer="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/progressbar.png:198,0" transparent="1"/>
			<widget source="session.CurrentService" render="Label" position="745,195" size="116,18" zPosition="1" font="Regular;18" halign="left" foregroundColor="#999999" transparent="1" >
					<convert type="ServicePosition">Length,ShowHours</convert>
			</widget>
			<widget source="session.CurrentService" render="Label" position="556,220" size="198,20" zPosition="1" font="Regular;20" halign="left" foregroundColor="#fcc000" transparent="1" >
					<convert type="ServicePosition">Position,ShowHours</convert>
			</widget>
			<widget name="shuffle" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/placeholder1.png,/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr_shuf.png" position="470,203" size="53,34" transparent="1" alphatest="on"/>
			<widget name="repeat" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/placeholder1.png,/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr_rep.png" position="470,167" size="53,34" transparent="1" alphatest="on"/>
			<widget name="dvrStatus" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr_pl.png,/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr_pau.png" position="555,155" size="160,39" transparent="1" alphatest="on"/>
			</screen>"""
	else:
		skin = """
			<screen name="MerlinMusicPlayerScreen" position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="#00000000" title="iDream">
			<eLabel backgroundColor="#999999" position="50,50" size="620,2" zPosition="1"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="50,40" size="250,20" text="MERLIN  MUSIC  PLAYER" valign="center" zPosition="2"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="420,40" size="250,20" text="WWW.DREAMBOX-TOOLS.INFO" valign="center" zPosition="2"/>
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/mmp3p.png" position="120,350" size="33,162"/>
			<widget name="coverArt" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/no_coverArt.png" position="106,130" size="180,180" transparent="1" alphatest="blend" />
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr.png" position="410,160" size="150,20" transparent="1" zPosition="1"/>
			<widget name="title" position="160,345" size="550,28" zPosition="1" transparent="1" font="Regular;24" foregroundColor="#fcc000" />
			<widget name="album" position="160,392" size="550,22" zPosition="1" transparent="1" font="Regular;18" foregroundColor="#999999" />
			<widget name="artist" position="160,422" size="550,22" zPosition="1" transparent="1" font="Regular;18" foregroundColor="#999999" />
			<widget name="genre" position="160,455" size="550,22" zPosition="1" transparent="1" font="Regular;18" foregroundColor="#999999" />
			<widget name="nextTitle" position="160,492" size="550,22" zPosition="1" transparent="1" font="Regular;16" foregroundColor="#f0f0f0" />
			<widget name="PositionGauge" position="386,197" size="198,14" pointer="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/progressbar.png:198,0" seek_pointer="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/progressbar.png:198,0" transparent="1"/>
			<widget source="session.CurrentService" render="Label" position="595,193" size="116,18" zPosition="1" font="Regular;18" halign="left" foregroundColor="#999999" transparent="1" >
					<convert type="ServicePosition">Length,ShowHours</convert>
			</widget>
			<widget source="session.CurrentService" render="Label" position="406,220" size="198,20" zPosition="1" font="Regular;20" halign="left" foregroundColor="#fcc000" transparent="1" >
					<convert type="ServicePosition">Position,ShowHours</convert>
			</widget>
			<widget name="shuffle" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/placeholder1.png,/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr_shuf.png" position="320,203" size="53,34" transparent="1" alphatest="on"/>
			<widget name="repeat" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/placeholder1.png,/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr_rep.png" position="320,167" size="53,34" transparent="1" alphatest="on"/>
			<widget name="dvrStatus" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr_pl.png,/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/dvr_pau.png" position="405,155" size="160,39" transparent="1" alphatest="on"/>
			</screen>"""

	def __init__(self, session, songlist, index, idreammode, currentservice, servicelist):
		self.session = session
		Screen.__init__(self, session)
		InfoBarNotifications.__init__(self)
		InfoBarBase.__init__(self)
		self["actions"] = ActionMap(["WizardActions", "MediaPlayerActions", "EPGSelectActions", "MediaPlayerSeekActions", "ColorActions"],
		{
			"back": self.closePlayer,
			"pause": self.pauseEntry,
			"stop": self.stopEntry,
			"right": self.playNext,
			"left": self.playPrevious,
			"up": self.showPlaylist,
			"down" : self.showPlaylist,
			"prevBouquet": self.shuffleList,
			"nextBouquet": self.repeatSong,
			"info" : self.showLyrics,
			"yellow": self.pauseEntry,
			"green": self.play,
			"menu": self.config,
			"ok": self.showTV,
		}, -1)

		self.onClose.append(self.__onClose)
		self.session.nav.stopService()
		self["PositionGauge"] = ServicePositionGauge(self.session.nav)
		self["coverArt"] = MerlinMediaPixmap()
		self["repeat"] = MultiPixmap()
		self["shuffle"] = MultiPixmap()
		self["dvrStatus"] = MultiPixmap()
		self["title"] = Label()
		self["album"] = Label()
		self["artist"] = Label()
		self["genre"] = Label()
		self["nextTitle"] = Label()
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evUpdatedInfo: self.__evUpdatedInfo,
				iPlayableService.evUser+10: self.__evAudioDecodeError,
				iPlayableService.evUser+12: self.__evPluginError,
				iPlayableService.evUser+13: self.embeddedCoverArt,
				iPlayableService.evStart: self.__serviceStarted,
			})

		InfoBarSeek.__init__(self, actionmap = "MediaPlayerSeekActions")
		self.songList = songlist
		self.origSongList = songlist[:]
		self.currentIndex = index
		self.shuffle = False
		self.repeat = False
		self.currentFilename = ""
		self.currentGoogleCoverFile = ""
		self.googleDownloadDir = os_path.join(config.plugins.merlinmusicplayer.googleimagepath.value, "downloaded_covers/" )
		if not os_path.exists(self.googleDownloadDir):
			try:
				os_mkdir(self.googleDownloadDir)
			except:
				self.googleDownloadDir = "/tmp/"
				
		self.init = 0
		self.onShown.append(self.__onShown)
		# for lcd
		self.currentTitle = ""
		self.nextTitle = ""
		self.screenSaverTimer = eTimer()
		self.screenSaverTimer.timeout.get().append(self.screenSaverTimerTimeout)
		self.screenSaverScreen = None

		self.iDreamMode = idreammode
		self.currentService = currentservice
		self.serviceList = servicelist

	def embeddedCoverArt(self):
		self["coverArt"].embeddedCoverArt()
		if self.screenSaverScreen:
			self.screenSaverScreen.updateCover(modus = 2)

	def screenSaverTimerTimeout(self):
		if config.plugins.merlinmusicplayer.usescreensaver.value:
			if self.screenSaverTimer.isActive():
				self.screenSaverTimer.stop()
			if not self.screenSaverScreen:
				self.screenSaverScreen = self.session.instantiateDialog(MerlinMusicPlayerScreenSaver)
				self.session.execDialog(self.screenSaverScreen)
				self.screenSaverScreen.updateLCD(self.currentTitle,1)
				self.screenSaverScreen.updateLCD(self.nextTitle,4)
				album = self["album"].getText()
				if album:
					text = "%s - %s" % (self["title"].getText(), album)
				else:
					text = self["title"].getText()
				self.screenSaverScreen.updateDisplayText(text)
				self.screenSaverScreen.updateCover(self["coverArt"].coverArtFileName, modus = 0)

	def resetScreenSaverTimer(self):
		if config.plugins.merlinmusicplayer.usescreensaver.value and config.plugins.merlinmusicplayer.screensaverwait.value != 0:
			if self.screenSaverTimer.isActive():
				self.screenSaverTimer.stop()
			self.screenSaverTimer.start(config.plugins.merlinmusicplayer.screensaverwait.value * 60000)

	def __onShown(self):
		if self.init == 0:
			self.init = 1
			self["coverArt"].onShow()
			self.playSong(self.songList[self.currentIndex][0].filename)
		else:
			self.summaries.setText(self.currentTitle,1)
			self.summaries.setText(self.nextTitle,4)
			if self.screenSaverScreen:
				self.screenSaverScreen.doClose()
				self.screenSaverScreen = None
		self.resetScreenSaverTimer()

	def __onClose(self):
		del self["coverArt"].picload
		self.seek = None

	def config(self):
		if self.screenSaverTimer.isActive():
			self.screenSaverTimer.stop()
		self.session.openWithCallback(self.setupFinished, MerlinMusicPlayerSetup, False)

	def showTV(self):
		if SystemInfo.get("NumVideoDecoders", 1) > 1:
			if self.screenSaverTimer.isActive():
				self.screenSaverTimer.stop()
			if self.screenSaverScreen:
				self.screenSaverScreen.doClose()
				self.screenSaverScreen = None
			self.screenSaverScreen = self.session.instantiateDialog(MerlinMusicPlayerTV, self.currentService, self.serviceList)
			self.session.execDialog(self.screenSaverScreen)
			self.screenSaverScreen.updateLCD(self.currentTitle,1)
			self.screenSaverScreen.updateLCD(self.nextTitle,4)
			album = self["album"].getText()
			if album:
				text = "%s - %s" % (self["title"].getText(), album)
			else:
				text = self["title"].getText()
			self.screenSaverScreen.updateDisplayText(text)
			self.screenSaverScreen.updateCover(self["coverArt"].coverArtFileName, modus = 0)

	def setupFinished(self, result):
		if result:
			self.googleDownloadDir = os_path.join(config.plugins.merlinmusicplayer.googleimagepath.value, "downloaded_covers/" )
			if not os_path.exists(self.googleDownloadDir):
				try:
					os_mkdir(self.googleDownloadDir)
				except:
					self.googleDownloadDir = "/tmp/"
		self.resetScreenSaverTimer()

	def closePlayer(self):
		if config.plugins.merlinmusicplayer.startlastsonglist.value:
			config.plugins.merlinmusicplayer.lastsonglistindex.value = self.currentIndex
			config.plugins.merlinmusicplayer.lastsonglistindex.save()
			connection = OpenDatabase()
			if connection is not None:
				connection.text_factory = str
				cursor = connection.cursor()
				cursor.execute("Delete from CurrentSongList;")
				for song in self.origSongList:
					cursor.execute("INSERT INTO CurrentSongList (song_id, filename,title,artist,album,genre, bitrate, length, track, date, PTS) VALUES(?,?,?,?,?,?,?,?,?,?,?);" , (song[0].songID, song[0].filename,song[0].title,song[0].artist,song[0].album,song[0].genre, song[0].bitrate, song[0].length, song[0].track, song[0].date, song[0].PTS))
				connection.commit()
				cursor.close()
				connection.close()
		if self.screenSaverTimer.isActive():
			self.screenSaverTimer.stop()
		self.close()

	def playSong(self, filename):
		self.session.nav.stopService()
		self.seek = None
		self.currentFilename = filename
		sref = eServiceReference(4097, 0, self.currentFilename)
		self.session.nav.playService(sref, adjust=False)
		if self.songList[self.currentIndex][0].PTS is not None:
			service = self.session.nav.getCurrentService()
			if service:
				self.seek = service.seek()
			self.updateMusicInformationCUE()
			self.ptsTimer = eTimer()
			self.ptsTimer.callback.append(self.ptsTimerCallback)
			self.ptsTimer.start(1000)
		self["nextTitle"].setText(self.getNextTitle())

	def ptsTimerCallback(self):
		if self.seek:
			pts = self.seek.getPlayPosition()
			index = 0
			currentIndex = 0
			for songs in self.songList:
				if pts[1] > songs[0].PTS:
					currentIndex = index
				else:
					break
				index +=1
			if currentIndex != self.currentIndex:
				self.currentIndex = currentIndex
				self.updateMusicInformationCUE()
		self.ptsTimer.start(1000)

	def updateMusicInformationCUE(self):
		self.updateSingleMusicInformation("artist", self.songList[self.currentIndex][0].artist, True)
		self.updateSingleMusicInformation("title", self.songList[self.currentIndex][0].title, True)
		self.updateSingleMusicInformation("album", self.songList[self.currentIndex][0].album, True)
		self.summaries.setText(self.songList[self.currentIndex][0].title,1)
		if self.screenSaverScreen:
			self.screenSaverScreen.updateLCD(self.songList[self.currentIndex][0].title,1)
			if self.songList[self.currentIndex][0].album:
				self.screenSaverScreen.updateDisplayText("%s - %s" % (self.songList[self.currentIndex][0].title,self.songList[self.currentIndex][0].album))
			else:
				self.screenSaverScreen.updateDisplayText(self.songList[self.currentIndex][0].title)
		self.updateCover(self.songList[self.currentIndex][0].artist, self.songList[self.currentIndex][0].album, self.songList[self.currentIndex][0].title)
		self.currentTitle = self.songList[self.currentIndex][0].title
		self["nextTitle"].setText(self.getNextTitle())

	def __serviceStarted(self):
		self["dvrStatus"].setPixmapNum(0)

	def __evUpdatedInfo(self):
		currPlay = self.session.nav.getCurrentService()
		if currPlay is not None:
			sTitle = currPlay.info().getInfoString(iServiceInformation.sTagTitle)
			sAlbum = currPlay.info().getInfoString(iServiceInformation.sTagAlbum)
			sArtist = currPlay.info().getInfoString(iServiceInformation.sTagArtist)
			sGenre = currPlay.info().getInfoString(iServiceInformation.sTagGenre)
			sYear = currPlay.info().getInfoString(iServiceInformation.sTagDate)
			if sYear:
				sYear = "(%s)" % sYear
			if not sTitle:
				sTitle = os_path.splitext(os_path.basename(self.currentFilename))[0]

			if self.songList[self.currentIndex][0].PTS is None:
				self.updateMusicInformation( sArtist, sTitle, sAlbum, sGenre, sYear, clear = True )
			else:
				self.updateSingleMusicInformation("genre", sGenre, True)
		else:
			self.updateMusicInformation()

	def updateMusicInformation(self, artist = "", title = "", album = "", genre = "", year = "", clear = False):
		if year and album:
			album = "%s %s" % (album, year)
		self.updateSingleMusicInformation("artist", artist, clear)
		self.updateSingleMusicInformation("title", title, clear)
		self.updateSingleMusicInformation("album", album, clear)
		self.updateSingleMusicInformation("genre", genre, clear)
		self.currentTitle = title
		if not self.iDreamMode and self.songList[self.currentIndex][0].PTS is None:
			# for lyrics
			self.songList[self.currentIndex][0].title = title
			self.songList[self.currentIndex][0].artist = artist
		self.summaries.setText(title,1)
		if self.screenSaverScreen:
			self.screenSaverScreen.updateLCD(title,1)
			if album:
				self.screenSaverScreen.updateDisplayText("%s - %s" % (title,album))
			else:
				self.screenSaverScreen.updateDisplayText(title)
		self.updateCover(artist, album, title)

	def updateCover(self, artist, album, title):
		hasCover = False
		audio = None
		audiotype = 0
		if self.currentFilename.lower().endswith(".mp3"):
			try: 
				audio = ID3(self.currentFilename)
				audiotype = 1
			except: audio = None
		elif self.currentFilename.lower().endswith(".flac"):
			try: 
				audio = FLAC(self.currentFilename)
				audiotype = 2
			except: audio = None
		elif self.currentFilename.lower().endswith(".m4a"):
			try: 
				audio = MP4(self.currentFilename)
				audiotype = 3
			except: audio = None
		elif self.currentFilename.lower().endswith(".ogg"):
			try:
				audio = OggVorbis(self.currentFilename)
				audiotype = 4
			except: audio = None
		if audio:
			if audiotype == 1:
				apicframes = audio.getall("APIC")
				if len(apicframes) >= 1:
					hasCover = True
			elif audiotype == 2:
				if len(audio.pictures) >= 1:
					hasCover = True
			elif audiotype == 3:
				if 'covr' in audio.tags:
					hasCover = True
			elif audiotype == 4:
				if 'METADATA_BLOCK_PICTURE' in audio.tags:
					hasCover = True
			audio = None
		if not hasCover:
			if not self["coverArt"].updateCoverArt(self.currentFilename):
				if config.plugins.merlinmusicplayer.usegoogleimage.value:
					self.getGoogleCover(artist, album, title)
				else:
					self["coverArt"].showDefaultCover()
					if self.screenSaverScreen:
						self.screenSaverScreen.updateCover(modus = 1)
			else:
				if self.screenSaverScreen:
					self.screenSaverScreen.updateCover(filename = self.currentFilename, modus = 3)
				self.currentGoogleCoverFile = ""
		else:
			self.currentGoogleCoverFile = ""

	def updateSingleMusicInformation(self, name, info, clear):
		if info != "" or clear:
			if self[name].getText() != info:
				self[name].setText(info)

	def getGoogleCover(self, artist, album, title, imagesize = "&imgsz=medium"):
		if (artist == "" or artist == "n/a"):
			self["coverArt"].showDefaultCover()
		elif (album == "" or album.startswith("n/a")):
			if (title == "" or title == "n/a"):
				self["coverArt"].showDefaultCover()
			else:
				url = "http://ajax.googleapis.com/ajax/services/search/images?v=1.0" + imagesize + "&q=%s+%s" % (quote(title),quote(artist))
				sendUrlCommand(url, None,10).addCallback(boundFunction(self.googleImageCallback, artist, album, title, imagesize)).addErrback(boundFunction(self.coverDownloadFailed, [], album, title))
		else:
			url = "http://ajax.googleapis.com/ajax/services/search/images?v=1.0" + imagesize + "&q=%s+%s" % (quote(album),quote(artist))
			sendUrlCommand(url, None,10).addCallback(boundFunction(self.googleImageCallback, artist, album, title, imagesize)).addErrback(boundFunction(self.coverDownloadFailed, [], album, title))

	def googleImageCallback(self, artist, album, title, imgsize, result):
		urls = re.findall("unescapedUrl\":\"(.*?)\",\"url\":\"", result)
		if (len(urls) == 0):
			print "[MerlinMusicPlayer] No medium images found. Search for all images"
			getGoogleCover(artist, album, title, "")
			return
		self.coverDownload(urls, album, title)

	def coverDownload(self, urls, album, title):
		url = urls[0]
		parts = urls[0].split("/")
		if (title != "" and title != "n/a"):
			filename = re.sub(r'[^A-Za-z0-9_-]', r'', title) + "_" + parts[-1]
		else:
			filename = re.sub(r'[^A-Za-z0-9_-]', r'', album) + "_" + parts[-1]
		if filename != self.currentGoogleCoverFile:
			self.currentGoogleCoverFile = filename
			filename = self.googleDownloadDir + filename
			if os_path.exists(filename):
				print "[MerlinMusicPlayer] using cover from %s " % filename
				self["coverArt"].showCoverFromFile(filename)
				if self.screenSaverScreen:
					self.screenSaverScreen.updateCover(filename = filename, modus = 4)
			else:
				urls.pop(0)
				print "[MerlinMusicPlayer] downloading cover from %s " % url
				downloadPage(url , filename).addCallback(boundFunction(self.coverDownloadFinished, filename)).addErrback(boundFunction(self.coverDownloadFailed, urls, album, title))

	def coverDownloadFailed(self, urls, album, title, result):
		print "[MerlinMusicPlayer] cover download failed: %s " % result
		if (len(urls) > 0):
			self.coverDownload(urls, album, title)
			return
		self["coverArt"].showDefaultCover()
		if self.screenSaverScreen:
			self.screenSaverScreen.updateCover(modus = 1)

	def coverDownloadFinished(self,filename, result):
		print "[MerlinMusicPlayer] cover download finished"
		self["coverArt"].showCoverFromFile(filename)
		if self.screenSaverScreen:
			self.screenSaverScreen.updateCover(filename = filename, modus = 4)

	def __evAudioDecodeError(self):
		currPlay = self.session.nav.getCurrentService()
		sAudioType = currPlay.info().getInfoString(iServiceInformation.sUser+10)
		print "[MerlinMusicPlayer] audio-codec %s can't be decoded by hardware" % (sAudioType)
		self.session.open(MessageBox, _("This Receiver can't decode %s streams!") % sAudioType, type = MessageBox.TYPE_INFO,timeout = 20 )

	def __evPluginError(self):
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser+12)
		print "[MerlinMusicPlayer]" , message
		self.session.open(MessageBox, message, type = MessageBox.TYPE_INFO,timeout = 20 )

	def doEofInternal(self, playing):
		if playing:
			self.playNext()

	def checkSkipShowHideLock(self):
		self.updatedSeekState()

	def updatedSeekState(self):
		if self.seekstate == self.SEEK_STATE_PAUSE:
			self["dvrStatus"].setPixmapNum(1)
		elif self.seekstate == self.SEEK_STATE_PLAY:
			self["dvrStatus"].setPixmapNum(0)

	def pauseEntry(self):
		self.pauseService()
		self.resetScreenSaverTimer()

	def play(self):
		#play the current song from beginning again
		if self.songList[self.currentIndex][0].PTS is None:
			self.playSong(self.songList[self.currentIndex][0].filename)
		else:
			if self.seek:
				self.seek.seekTo(self.songList[self.currentIndex][0].PTS)
				self.updatedSeekState()
		self.resetScreenSaverTimer()

	def unPauseService(self):
		self.setSeekState(self.SEEK_STATE_PLAY)

	def stopEntry(self):
		self.seek = None
		self.session.nav.stopService()
		self.origSongList = []
		self.songList = []
		if config.plugins.merlinmusicplayer.startlastsonglist.value:
			config.plugins.merlinmusicplayer.lastsonglistindex.value = -1
			config.plugins.merlinmusicplayer.lastsonglistindex.save()
			connection = OpenDatabase()
			if connection is not None:
				connection.text_factory = str
				cursor = connection.cursor()
				cursor.execute("Delete from CurrentSongList;")
				connection.commit()
				cursor.close()
				connection.close()
		self.resetScreenSaverTimer()
		self.close()

	def playNext(self):
		if not self.repeat:
			if self.currentIndex +1 > len(self.songList) -1:
				self.currentIndex = 0
			else:
				self.currentIndex += 1
		if self.songList[self.currentIndex][0].PTS is None:
			self.playSong(self.songList[self.currentIndex][0].filename)
		else:
			self.playCUETrack()
		if not self.screenSaverScreen:
			self.resetScreenSaverTimer()

	def playPrevious(self):
		if not self.repeat:
			if self.currentIndex - 1 < 0:
				self.currentIndex = len(self.songList) - 1
			else:
				self.currentIndex -= 1

		if self.songList[self.currentIndex][0].PTS is None:
			self.playSong(self.songList[self.currentIndex][0].filename)
		else:
			self.playCUETrack()
		self.resetScreenSaverTimer()

	def getNextTitle(self):
		if self.repeat:
			index = self.currentIndex
		else:
			if self.currentIndex + 1 > len(self.songList) -1:
				index = 0
			else:
				index = self.currentIndex + 1
		if self.iDreamMode or self.songList[index][0].PTS is not None:
			text = "%s - %s" % (self.songList[index][0].title, self.songList[index][0].artist)
		else:
			if self.songList[index][0].filename.lower().startswith("http://"):
				text = self.songList[index][0].filename
			else:
				path,filename = os_path.split(self.songList[index][0].filename)
				audio, isAudio, title, genre,artist,album,tracknr,track,date,length,bitrate = getID3Tags(path,filename)
				if audio:
					if artist:
						text = "%s - %s" % (title, artist)
					else:
						text = title
				else:
					text = title
				audio = None
		self.nextTitle = text
		self.summaries.setText(text,4)
		if self.screenSaverScreen:
			self.screenSaverScreen.updateLCD(text,4)
		return str(text)

	def shuffleList(self):
		if self.songList[self.currentIndex][0].PTS is None: # not implemented for cue files yet
			self.shuffle = not self.shuffle
			if self.shuffle:
				self["shuffle"].setPixmapNum(1)
				shuffle(self.songList)
			else:
				self.songList = self.origSongList[:]
				self["shuffle"].setPixmapNum(0)
			index = 0
			for x in self.songList:
				if x[0].filename == self.currentFilename:
					self.currentIndex = index
					break
				index += 1
			self["nextTitle"].setText(self.getNextTitle())
		else:
			self.session.open(MessageBox, _("Shuffle is not available yet with cue-files!"), type = MessageBox.TYPE_INFO,timeout = 20 )
		self.resetScreenSaverTimer()

	def repeatSong(self):
		if self.songList[self.currentIndex][0].PTS is None: # not implemented for cue files yet
			self.repeat = not self.repeat
			if self.repeat:
				self["repeat"].setPixmapNum(1)
			else:
				self["repeat"].setPixmapNum(0)
			self["nextTitle"].setText(self.getNextTitle())
		else:
			self.session.open(MessageBox, _("Repeat is not available yet with cue-files!"), type = MessageBox.TYPE_INFO,timeout = 20 )
		self.resetScreenSaverTimer()

	def showPlaylist(self):
		if self.screenSaverTimer.isActive():
			self.screenSaverTimer.stop()
		self.session.openWithCallback(self.showPlaylistCallback, MerlinMusicPlayerSongList, self.songList, self.currentIndex, self.iDreamMode)

	def showPlaylistCallback(self, index):
		if index != -1:
			self.currentIndex = index

			if self.songList[self.currentIndex][0].PTS is None:
				self.playSong(self.songList[self.currentIndex][0].filename)
			else:
				self.playCUETrack()

		self.resetScreenSaverTimer()

	def playCUETrack(self):
		if self.ptsTimer.isActive():
			self.ptsTimer.stop()
		if self.seek:
			self.seek.seekTo(self.songList[self.currentIndex][0].PTS)
			self.updatedSeekState()
			self.updateMusicInformationCUE()
			self.ptsTimer.start(1000)

	def showLyrics(self):
		if self.screenSaverTimer.isActive():
			self.screenSaverTimer.stop()
		self.session.openWithCallback(self.resetScreenSaverTimer, MerlinMusicPlayerLyrics, self.songList[self.currentIndex][0])

	def createSummary(self):
		return MerlinMusicPlayerLCDScreen

class MerlinMusicPlayerLyrics(Screen):

	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:
		skin = """
			<screen name="MerlinMusicPlayerLyrics" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#00000000" title="Merlin Music Player Lyrics">
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/mmpborderHD.png" position="128,72" size="1024,576"/>
			<eLabel backgroundColor="#999999" position="178,112" size="924,2" zPosition="1"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="178,104" size="250,20" text="MERLIN  MUSIC  PLAYER" valign="center" zPosition="2"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="852,104" size="250,20" text="WWW.DREAMBOX-TOOLS.INFO" valign="center" zPosition="2"/>
			<widget name="headertext" position="178,145" zPosition="1" size="900,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
			<widget name="resulttext" position="178,172" zPosition="1" size="900,20" font="Regular;16" transparent="1"   backgroundColor="#00000000"/>
			<widget name="lyric_text" position="178,222" zPosition="2" size="940,350" font="Regular;18" transparent="0"  backgroundColor="#00000000"/>
			</screen>"""
	elif sz_w == 1024:
		skin = """
			<screen name="MerlinMusicPlayerLyrics" position="0,0" size="1024,576" flags="wfNoBorder" backgroundColor="#00000000" title="Merlin Music Player Lyrics">
			<eLabel backgroundColor="#999999" position="50,40" size="924,2" zPosition="1"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="50,32" size="250,20" text="MERLIN  MUSIC  PLAYER" valign="center" zPosition="2"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="724,32" size="250,20" text="WWW.DREAMBOX-TOOLS.INFO" valign="center" zPosition="2"/>
			<widget name="headertext" position="50,73" zPosition="1" size="900,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
			<widget name="resulttext" position="50,100" zPosition="1" size="900,20" font="Regular;16" transparent="1"   backgroundColor="#00000000"/>
			<widget name="lyric_text" position="50,150" zPosition="2" size="940,350" font="Regular;18" transparent="0"  backgroundColor="#00000000"/>
			</screen>"""
	else:
		skin = """
			<screen name="MerlinMusicPlayerLyrics" position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="#00000000" title="Merlin Music Player Lyrics">
			<eLabel backgroundColor="#999999" position="50,50" size="620,2" zPosition="1"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="50,40" size="250,20" text="MERLIN  MUSIC  PLAYER" valign="center" zPosition="2"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="420,40" size="250,20" text="WWW.DREAMBOX-TOOLS.INFO" valign="center" zPosition="2"/>
			<widget name="headertext" position="50,73" zPosition="1" size="620,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
			<widget name="resulttext" position="50,100" zPosition="1" size="620,20" font="Regular;16" transparent="1"   backgroundColor="#00000000"/>
			<widget name="lyric_text" position="50,150" zPosition="2" size="620,350" font="Regular;18" transparent="0"  backgroundColor="#00000000"/>
			</screen>"""
		
	
	def __init__(self, session, currentsong):
		self.session = session
		Screen.__init__(self, session)
		self.setTitle(_("Lyrics"))
		self["headertext"] = Label(_("Merlin Music Player Lyrics"))
		# leoslyrics does not work anymore
#		self["resulttext"] = Label(_("Getting lyrics from api.leoslyrics.com..."))
		self["resulttext"] = Label()
		self["actions"] = ActionMap(["WizardActions", "DirectionActions"],
		{
			"back": self.close,
			"upUp": self.pageUp,
			"leftUp": self.pageUp,
			"downUp": self.pageDown,
			"rightUp": self.pageDown,
		}, -1)
		self["lyric_text"] = ScrollLabel()
		self.currentSong = currentsong
		self.onLayoutFinish.append(self.startRun)

	def startRun(self):
		# get lyric-text from id3 tag
		try:
			audio = ID3(self.currentSong.filename)
		except:
			audio = None
		text = getEncodedString(self.getLyricsFromID3Tag(audio)).replace("\r\n","\n")
		text = text.replace("\r","\n")
		self["lyric_text"].setText(text)
 
	def getLyricsFromID3Tag(self,tag):
		if tag:
			for frame in tag.values():
				if frame.FrameID == "USLT":
					return frame.text
		url = "http://api.chartlyrics.com/apiv1.asmx/SearchLyricDirect?artist=%s&song=%s" % (quote(self.currentSong.artist), quote(self.currentSong.title))
		sendUrlCommand(url, None,10).addCallback(self.gotLyrics).addErrback(self.urlError)
		return "No lyrics found in id3-tag, trying api.chartlyrics.com..."

	def urlError(self, error = None):
		if error is not None:
			self["resulttext"].setText(str(error.getErrorMessage()))
			self["lyric_text"].setText("")

	def gotLyrics(self, xmlstring):
		root = cet_fromstring(xmlstring)
		lyrictext = ""
		lyrictext = root.findtext("{http://api.chartlyrics.com/}Lyric").encode("utf-8", 'ignore')
		self["lyric_text"].setText(lyrictext)
		title = root.findtext("{http://api.chartlyrics.com/}LyricSong").encode("utf-8", 'ignore')
		artist = root.findtext("{http://api.chartlyrics.com/}LyricArtist").encode("utf-8", 'ignore')
		result = _("Response -> lyrics for: %s (%s)") % (title,artist)
		self["resulttext"].setText(result)
		if not lyrictext:
			self["resulttext"].setText(_("No lyrics found"))
			self["lyric_text"].setText("")

	def pageUp(self):
		self["lyric_text"].pageUp()

	def pageDown(self):
		self["lyric_text"].pageDown()

class MerlinMusicPlayerSongList(Screen):
	
	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:
		skin = """
			<screen name="MerlinMusicPlayerSongList" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#00000000" title="Songlist">
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/mmpborderHD.png" position="128,72" size="1024,576"/>
			<eLabel backgroundColor="#999999" position="178,112" size="924,2" zPosition="1"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="178,104" size="250,20" text="MERLIN  MUSIC  PLAYER" valign="center" zPosition="2"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="852,104" size="250,20" text="WWW.DREAMBOX-TOOLS.INFO" valign="center" zPosition="2"/>
			<widget name="headertext" position="178,145" zPosition="1" size="900,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
			<widget name="list" position="178,182" zPosition="2" size="940,350" scrollbarMode="showOnDemand" transparent="0"  backgroundColor="#00000000"/>
			</screen>"""
	elif sz_w == 1024:
		skin = """
			<screen name="MerlinMusicPlayerSongList" position="0,0" size="1024,576" flags="wfNoBorder" backgroundColor="#00000000" title="Songlist">
			<eLabel backgroundColor="#999999" position="50,40" size="924,2" zPosition="1"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="50,32" size="250,20" text="MERLIN  MUSIC  PLAYER" valign="center" zPosition="2"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="724,32" size="250,20" text="WWW.DREAMBOX-TOOLS.INFO" valign="center" zPosition="2"/>
			<widget name="headertext" position="50,73" zPosition="1" size="900,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
			<widget name="list" position="50,110" zPosition="2" size="940,350" scrollbarMode="showOnDemand" transparent="0"  backgroundColor="#00000000"/>
			</screen>"""
	else:
		skin = """
			<screen name="MerlinMusicPlayerSongList" position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="#00000000" title="Songlist">
			<eLabel backgroundColor="#999999" position="50,50" size="620,2" zPosition="1"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="50,40" size="250,20" text="MERLIN  MUSIC  PLAYER" valign="center" zPosition="2"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="420,40" size="250,20" text="WWW.DREAMBOX-TOOLS.INFO" valign="center" zPosition="2"/>
			<widget name="headertext" position="50,73" zPosition="1" size="620,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
			<widget name="list" position="50,110" zPosition="2" size="620,350" scrollbarMode="showOnDemand" transparent="0"  backgroundColor="#00000000"/>
			</screen>"""
		
	
	def __init__(self, session, songlist, index, idreammode):
		self.session = session
		Screen.__init__(self, session)
		
		
		self["headertext"] = Label(_("Merlin Music Player Songlist"))
		self["list"] = iDreamList()
		self["list"].connectSelChanged(self.lcdUpdate)
		self["actions"] = ActionMap(["WizardActions"],
		{
			"ok": self.ok,
			"back": self.closing,
		}, -1)
		self.songList = songlist
		self.index = index
		self.iDreamMode = idreammode
		self.onLayoutFinish.append(self.startRun)
		self.onShown.append(self.lcdUpdate)

	def startRun(self):
		if self.iDreamMode:
			self["list"].setMode(10) # songlist
		self["list"].setList(self.songList)
		self["list"].moveToIndex(self.index)

	def ok(self):
		self.close(self["list"].getCurrentIndex())

	def closing(self):
		self.close(-1)

	def lcdUpdate(self):
		try:
			index = self["list"].getCurrentIndex()
			songlist = self["list"].getList()
			mode =  self.iDreamMode or songlist[index][0].PTS
			if mode:
				self.summaries.setText(songlist[index][0].title,1)
			else:
				self.summaries.setText(songlist[index][0].text,1)
			count = self["list"].getItemCount()
			# voheriges
			index -= 1
			if index < 0:
				index = count
			if mode:
				self.summaries.setText(songlist[index][0].title,3)
			else:
				self.summaries.setText(songlist[index][0].text,3)
			# naechstes
			index = self["list"].getCurrentIndex() + 1
			if index > count:
				index = 0
			if mode:
				self.summaries.setText(songlist[index][0].title,4)
			else:
				self.summaries.setText(songlist[index][0].text,4)
		except: pass

	def createSummary(self):
		return MerlinMusicPlayerLCDScreenText

class iDreamMerlin(Screen):
	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:
		skin = """
			<screen name="iDreamMerlin" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#00000000" title="iDream">
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/mmpborderHD.png" position="128,72" size="1024,576"/>
				<ePixmap position="178,102" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="328,102" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap position="478,102" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="628,102" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<widget render="Label" source="key_red" position="178,102" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;18" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_green" position="328,102" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;18" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_yellow" position="478,102" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;18" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_blue" position="628,102" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;18" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="headertext" position="178,149" zPosition="1" size="900,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
				<widget name="list" position="178,182" zPosition="2" size="940,350" scrollbarMode="showOnDemand" transparent="0"  backgroundColor="#00000000"/>
			</screen>"""
	elif sz_w == 1024:
		skin = """
			<screen name="iDreamMerlin" position="0,0" size="1024,576" flags="wfNoBorder" backgroundColor="#00000000" title="iDream">
				<ePixmap position="50,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="200,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap position="350,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="500,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<widget render="Label" source="key_red" position="50,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;18" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_green" position="200,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;18" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_yellow" position="350,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;18" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_blue" position="500,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;18" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="headertext" position="50,77" zPosition="1" size="900,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
				<widget name="list" position="50,110" zPosition="2" size="940,350" scrollbarMode="showOnDemand" transparent="0"  backgroundColor="#00000000"/>
			</screen>"""
	else:
		skin = """
			<screen name="iDreamMerlin" position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="#00000000" title="iDream">
				<ePixmap position="50,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="200,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap position="350,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="500,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<widget render="Label" source="key_red" position="50,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;18" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_green" position="200,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;18" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_yellow" position="350,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;18" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_blue" position="500,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;18" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="headertext" position="50,77" zPosition="1" size="620,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
				<widget name="list" position="50,110" zPosition="2" size="620,350" scrollbarMode="showOnDemand" transparent="0"  backgroundColor="#00000000"/>
			</screen>"""
	def __init__(self, session, servicelist):
		self.session = session
		Screen.__init__(self, session)
		self["list"] = iDreamList()
		self["list"].connectSelChanged(self.lcdUpdate)
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions"],
		{
			"ok": self.ok,
			"back": self.closing,
			"red": self.red_pressed,
			"green": self.green_pressed,
			"yellow": self.yellow_pressed,
			"blue": self.blue_pressed,
			"menu": self.menu_pressed,
			"info" : self.info_pressed,
		}, -1)

		self["actions2"] = NumberActionMap(["InputActions"],
		{
			"0": self.keyNumber_pressed,
		}, -1)

		self.onLayoutFinish.append(self.startRun)
		self.onShown.append(self.lcdUpdate)
		self.onClose.append(self.__onClose)
		
		self.serviceList = servicelist
		self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
		
		self.mode = 0
		self.mainMenuList = []
		self.cacheList = []
		self.LastMethod = None
		self.player = None
		
		self["key_red"] = StaticText("")
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText("")
		self["headertext"] = Label(_("iDream Main Menu"))

		self.startMerlinPlayerScreenTimer = eTimer()
		self.startMerlinPlayerScreenTimer.timeout.get().append(self.info_pressed)

	def getPlayList(self):
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			playList = []
			cursor.execute("select playlist_id,playlist_text from playlists order by playlist_text;")
			for row in cursor:
				playList.append((row[1], row[0]))
			cursor.close()  
			connection.close()
			return playList
		else:
			return None

	def sqlCommand(self, sqlSatement):
		connection = OpenDatabase()
		if connection is not None:
			cursor = connection.cursor()
			cursor.execute(sqlSatement)
			cursor.close()
			connection.commit()
			connection.close()

	def clearCache(self):
		for items in self.cacheList:
			items.cache = False
			items.listview = []
			items.headertext = ""

	def getCurrentSelection(self):
		sel = None
		try: sel = self["list"].l.getCurrentSelection()[0]
		except: pass
		return sel

	def addListToPlaylistConfirmed(self, methodName, answer):
		if answer:
			playList = self.getPlayList()
			if len(playList):
				self.session.openWithCallback(methodName, ChoiceBox,list = playList)
			else:
				self.session.openWithCallback(self.createPlaylistConfirmed, MessageBox, _("There are no playlists defined.\nDo you want to create a new playlist?"))

	def menu_pressed(self):
		self.startMerlinPlayerScreenTimer.stop()
		options = [(_("Configuration"), self.config),(_("Search in iDream database"), self.searchInIDreamDatabase),]
		options.extend(((_("Scan path for music files and add them to database"), self.scanDir),))
		if self.mode != 1:
			options.extend(((_("Create new playlist"), self.createPlaylist),))
		if self["list"].getDisplaySongMode():
			if self.mode == 2:
				options.extend(((_("Delete song from current playlist"), self.deleteSongFromPlaylist),))
			else:
				options.extend(((_("Add selected song to a playlist"), self.addSongToPlaylist),))
				if self.mode == 18:
					options.extend(((_("Add all songs from selected album to a playlist"), self.addAlbumToPlaylist),))
				elif self.mode == 19:
					options.extend(((_("Add all songs from selected artist to a playlist"), self.addArtistToPlaylist),))
				options.extend(((_("Delete song from database"), self.deleteSongFromDatabase),))
			options.extend(((_("Clear current songlist and play selected entry"), self.stopPlayingAndAppendFileToSongList),))
			options.extend(((_("Append file to current playing songlist"), self.appendFileToSongList),))
			if self.player is not None and self.player.songList:
				options.extend(((_("Insert file to current playing songlist and play next"), self.insertFileToSongList),))
		else:
			if self.mode == 1:
				options.extend(((_("Delete selected playlist"), self.deletePlaylist),))
			elif self.mode == 4:
				options.extend(((_("Add all songs from selected artist to a playlist"), self.addArtistToPlaylist),))
			elif self.mode == 5 or self.mode == 7:
				options.extend(((_("Add all songs from selected album to a playlist"), self.addAlbumToPlaylist),))
			elif self.mode == 13:
				options.extend(((_("Add all songs from selected genre to a playlist"), self.addGenreToPlaylist),))
		self.session.openWithCallback(self.menuCallback, ChoiceBox,list = options)

	def menuCallback(self, ret):
		ret and ret[1]()

	def scanDir(self):
		SelectPath
		self.session.openWithCallback(self.pathSelected,SelectPath,"/media/")

	def pathSelected(self, res):
		if res is not None:
			self.session.openWithCallback(self.filesAdded, iDreamAddToDatabase,res)

	def filesAdded(self):
		if pathToDatabase.isRunning:
			self.close()
		else:
			self.red_pressed()

	def addGenreToPlaylist(self):
		self.session.openWithCallback(boundFunction(self.addListToPlaylistConfirmed,self.addGenreToPlaylistConfirmedCallback), MessageBox, _("Do you really want to add all songs from that genre to a playlist?"))

	def addGenreToPlaylistConfirmedCallback(self, ret):
		if ret:
			sel = self.getCurrentSelection()
			if sel:
				self.sqlCommand("INSERT INTO Playlist_Songs (playlist_id,song_id) select %d, song_id from songs where genre_id=%d order by album_id,tracknumber,title,filename;" % (ret[1],sel.genreID))
				self.clearCache()

	def addArtistToPlaylist(self):
		self.session.openWithCallback(boundFunction(self.addListToPlaylistConfirmed, self.addArtistToPlaylistConfirmedCallback), MessageBox, _("Do you really want to add all songs from that artist to a playlist?"))

	def addArtistToPlaylistConfirmedCallback(self, ret):
		if ret:
			sel = self.getCurrentSelection()
			if sel:
				self.sqlCommand("INSERT INTO Playlist_Songs (playlist_id,song_id) select %d, song_id from songs where artist_id=%d order by album_id,tracknumber,title,filename;" % (ret[1],sel.artistID))
				self.clearCache()

	def addAlbumToPlaylist(self):
		self.session.openWithCallback(boundFunction(self.addListToPlaylistConfirmed, self.addAlbumToPlaylistConfirmedCallback), MessageBox, _("Do you really want to add all songs from that album to a playlist?"))

	def addAlbumToPlaylistConfirmedCallback(self, ret):
		if ret:
			sel = self.getCurrentSelection()
			if sel:
				self.sqlCommand("INSERT INTO Playlist_Songs (playlist_id,song_id) select %d, song_id from songs where album_id=%d order by tracknumber,title,filename;" % (ret[1],sel.albumID))
				self.clearCache()

	def deletePlaylist(self):
		self.session.openWithCallback(self.deletePlaylistConfirmed, MessageBox, _("Do you really want to delete the current playlist?"))

	def deletePlaylistConfirmed(self, answer):
		if answer:
			sel = self.getCurrentSelection()
			if sel:
				self.sqlCommand("delete from playlist_songs where playlist_id = %d" % (sel.playlistID))
				self.sqlCommand("delete from playlists where playlist_id = %d" % (sel.playlistID))
				self["list"].removeItem(self["list"].getCurrentIndex())
				self.clearCache()

	def deleteSongFromPlaylist(self):
		self.session.openWithCallback(self.deleteSongFromPlaylistConfirmed, MessageBox, _("Do you really want to delete that song the current playlist?"))

	def deleteSongFromPlaylistConfirmed(self, answer):
		if answer:
			sel = self.getCurrentSelection()
			if sel:
				self.sqlCommand("delete from playlist_songs where song_id = %d" % (sel.songID))
				self["list"].removeItem(self["list"].getCurrentIndex())
				self.clearCache()

	def deleteSongFromDatabase(self):
		self.session.openWithCallback(self.deleteSongFromDatabaseConfirmed, MessageBox, _("Do you really want to delete that song from the database?"))

	def deleteSongFromDatabaseConfirmed(self, answer):
		if answer:
			sel = self.getCurrentSelection()
			if sel:
				self.sqlCommand("delete from playlist_songs where song_id = %d" % (sel.songID))
				self.sqlCommand("delete from songs where song_id = %d" % (sel.songID))
				self["list"].removeItem(self["list"].getCurrentIndex())
				self.clearCache()
			
	def addSongToPlaylist(self):
		playList = self.getPlayList()
		if len(playList):
			self.session.openWithCallback(self.addSongToPlaylistCallback, ChoiceBox,list = playList)
		else:
			self.session.openWithCallback(self.createPlaylistConfirmed, MessageBox, _("There are no playlists defined.\nDo you want to create a new playlist?"))

	def createPlaylistConfirmed(self, val):
		if val:
			self.createPlaylist()

	def addSongToPlaylistCallback(self,ret):
		if ret:
			sel = self.getCurrentSelection()
			if sel:
				self.sqlCommand("INSERT INTO Playlist_Songs (playlist_id,song_id) VALUES(%d,%d);" % (ret[1],sel.songID))
				self.clearCache()

	def createPlaylist(self):
		self.session.openWithCallback(self.createPlaylistFinished, VirtualKeyBoard, title = _("Enter name for playlist"))

	def createPlaylistFinished(self, text = None):
		if text:
			self.sqlCommand('INSERT INTO Playlists (playlist_text) VALUES("%s");' % (text))
			self.clearCache()
			self.menu_pressed()

	def searchInIDreamDatabase(self):
		options = [(_("search for title"), 1),
			(_("search for artist"), 2),
			(_("search for album"), 3),
			(_("search in all of them"), 4),]
		self.session.openWithCallback(self.enterSearchText, ChoiceBox,list = options)

	def enterSearchText(self, ret):
		if ret:
			self.session.openWithCallback(boundFunction(self.enterSearchTextFinished,ret[1]), VirtualKeyBoard, title = _("Enter search text"))

	def enterSearchTextFinished(self, searchType, searchText = None):
		if searchText:
			search = "%" + searchText + "%"
			if searchType == 1:
				sql_where = "where title like '%s'" % search
				text = _('Search results for "%s" in all titles') % searchText
			elif searchType == 2:
				sql_where = "where artists.artist like '%s'" % search
				text = _('Search results for "%s" in all artists') % searchText
			elif searchType == 3:
				sql_where = "where album_text like '%s'" % search
				text = _('Search results for "%s" in all albums') % searchText
			else:
				sql_where = "where (title like '%s' or artists.artist like '%s' or album_text like '%s')"  % (search,search,search)
				text = _('Search results for "%s" in title, artist or album') % searchText
			self.setButtons(red = True, yellow = True, blue = True)
			oldmode = self.mode
			self.mode = 20
			self["list"].setMode(self.mode)
			self.buildSearchSongList(sql_where, text, oldmode, True)


	def keyNumber_pressed(self, number):
		if number == 0 and self.mode != 0:
			self["list"].moveToIndex(0)
			self.ok()

	def ok(self):
		sel = self.getCurrentSelection()
		if sel is None:
			return
		if sel.mode == 99:
			self.green_pressed()
		else:
			self.mode = sel.mode
			self["list"].setMode(self.mode)
			if sel.navigator and len(self.cacheList) > 0:
				cache = self.cacheList.pop()
			else:
				cache = CacheList(cache = False, index = -1)
			if sel.navigator: 
				self["headertext"].setText(cache.headertext)
				if cache.cache:
					self["list"].setList(cache.listview)
					self.LastMethod = MethodArguments(method = cache.methodarguments.method, arguments = cache.methodarguments.arguments)
				else:
					cache.methodarguments.method(**cache.methodarguments.arguments)
				self["list"].moveToIndex(cache.index)
			if self.mode == 0:
				self.setButtons()
				if not sel.navigator:
					self.buildMainMenuList()
			elif self.mode == 1:
				self.setButtons(red = True)
				if not sel.navigator:
					self.buildPlaylistList(addToCache = True)
			elif self.mode == 2:
				self.setButtons(red = True, green = True, yellow = True, blue = True)
				if not sel.navigator:
					self.buildPlaylistSongList(playlistID = sel.playlistID, addToCache = True)
			elif self.mode == 4:
				self.setButtons(red = True)
				if not sel.navigator:
					self.buildArtistList(addToCache = True)
			elif self.mode == 5:
				self.setButtons(red = True)
				if not sel.navigator:
					self.buildArtistAlbumList(sel.artistID, addToCache = True)
			elif self.mode == 6:
				self.setButtons(red = True, green = True, yellow = True)
				if not sel.navigator:
					self.buildAlbumSongList(albumID = sel.albumID, mode = 5, addToCache = True)
			elif self.mode == 7:
				self.setButtons(red = True)
				if not sel.navigator:
					self.buildAlbumList(addToCache = True)
			elif self.mode == 8:
				self.setButtons(red = True, green = True, yellow = True)
				if not sel.navigator:
					self.buildAlbumSongList(albumID = sel.albumID, mode = 7, addToCache = True)
			elif self.mode == 10:
				self.setButtons(red = True, green = True, yellow = True, blue = True)
				if not sel.navigator:
					self.buildSongList(addToCache = True)
			elif self.mode == 13:
				self.setButtons(red = True)
				if not sel.navigator:
					self.buildGenreList(addToCache = True)
			elif self.mode == 14:
				self.setButtons(red = True, green = True, yellow = True, blue = True)
				if not sel.navigator:
					self.buildGenreSongList(genreID = sel.genreID, addToCache = True)
			elif self.mode == 18 or self.mode == 19:
				if self.mode == 18:
					self.setButtons(red = True, green = True, yellow = True)
				if self.mode == 19:
					self.setButtons(red = True, green = True, blue = True)
				if not sel.navigator:
					self.red_pressed() # back to main menu --> normally that can not be happened
			elif self.mode == 20:
				self.setButtons(red = True, green = True, yellow = True, blue = True)
				if not sel.navigator:
					self.red_pressed() # back to main menu --> normally that can not be happened

	def buildPlaylistList(self, addToCache):
		if addToCache:
			self.cacheList.append(CacheList(index = self["list"].getCurrentIndex(), listview = self["list"].getList(), headertext = self["headertext"].getText(), methodarguments = self.LastMethod))
		arguments = {}
		arguments["addToCache"] = False
		self.LastMethod = MethodArguments(method = self.buildPlaylistList, arguments = arguments)
		self["headertext"].setText(_("Playlists"))
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			playlistList = []
			playlistList.append((Item(text = _("[back]"), mode = 0, navigator = True),))
			cursor.execute("select playlists.playlist_id, playlist_text, count(Playlist_Songs.playlist_id) from playlists left outer join Playlist_Songs on playlists.playlist_id = Playlist_Songs.playlist_id group by playlists.playlist_id order by playlists.playlist_text;")
			for row in cursor:
				playlistList.append((Item(text = "%s (%d)" % (row[1], row[2]), mode = 2, playlistID = row[0]),))
			cursor.close() 
			connection.close()
			self["list"].setList(playlistList)
			if len(playlistList) > 1:
				self["list"].moveToIndex(1)

	def buildPlaylistSongList(self, playlistID, addToCache):
		if addToCache:
			self.cacheList.append(CacheList(index = self["list"].getCurrentIndex(), listview = self["list"].getList(), headertext = self["headertext"].getText(), methodarguments = self.LastMethod))
		arguments = {}
		arguments["playlistID"] = playlistID
		arguments["addToCache"] = False
		self.LastMethod = MethodArguments(method = self.buildPlaylistSongList, arguments = arguments)
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			playlistSongList = []
			playlistSongList.append((Item(text = _("[back]"), mode = 1, navigator = True),))
			cursor.execute("select songs.song_id, title, artists.artist, filename, songs.artist_id, bitrate, length, genre_text, track, date, album_text, songs.Album_id from songs inner join artists on songs.artist_id = artists.artist_id inner join Album on songs.Album_id = Album.Album_id inner join genre on songs.genre_id = genre.genre_id inner join playlist_songs on songs.song_id = playlist_songs.song_id where playlist_songs.playlist_id =  %d order by playlist_songs.id;" % (playlistID))
			for row in cursor:
				playlistSongList.append((Item(mode = 99, songID = row[0], title = row[1], artist = row[2], filename = row[3], artistID = row[4], bitrate = row[5], length = row[6], genre = row[7], track = row[8], date = row[9], album = row[10], albumID = row[11], playlistID = playlistID),))
			cursor.execute("SELECT playlist_text from playlists where playlist_id = %d;" % playlistID)
			row = cursor.fetchone()
			self["headertext"].setText(_("Playlist (%s) -> Song List") % row[0])
			cursor.close() 
			connection.close()
			self["list"].setList(playlistSongList)
			if len(playlistSongList) > 1:
				self["list"].moveToIndex(1)

	def buildGenreList(self, addToCache):
		if addToCache:
			self.cacheList.append(CacheList(index = self["list"].getCurrentIndex(), listview = self["list"].getList(), headertext = self["headertext"].getText(), methodarguments = self.LastMethod))
		arguments = {}
		arguments["addToCache"] = False
		self.LastMethod = MethodArguments(method = self.buildGenreList, arguments = arguments)
		self["headertext"].setText(_("Genre List"))
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			genreList = []
			genreList.append((Item(text = _("[back]"), mode = 0, navigator = True),))
			cursor.execute("select Genre.genre_id,Genre.Genre_text, count(*) from songs inner join Genre on songs.genre_id = Genre.Genre_id group by songs.Genre_id order by Genre.Genre_text;")
			for row in cursor:
				genreList.append((Item(text = "%s (%d)" % (row[1], row[2]), mode = 14, genreID = row[0]),))
			cursor.close() 
			connection.close()
			self["list"].setList(genreList)
			if len(genreList) > 1:
				self["list"].moveToIndex(1)

	def buildGenreSongList(self, genreID, addToCache):
		if addToCache:
			self.cacheList.append(CacheList(index = self["list"].getCurrentIndex(), listview = self["list"].getList(), headertext = self["headertext"].getText(), methodarguments = self.LastMethod))
		arguments = {}
		arguments["genreID"] = genreID
		arguments["addToCache"] = False
		self.LastMethod = MethodArguments(method = self.buildGenreSongList, arguments = arguments)
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			genreSongList = []
			genreSongList.append((Item(text = _("[back]"), mode = 13, navigator = True),))
			cursor.execute("select song_id, title, artists.artist, filename, songs.artist_id, bitrate, length, genre_text, track, date, album_text, songs.Album_id from songs inner join artists on songs.artist_id = artists.artist_id inner join Album on songs.Album_id = Album.Album_id inner join genre on songs.genre_id = genre.genre_id where songs.genre_id = %d order by title, filename;" % (genreID))
			for row in cursor:
				genreSongList.append((Item(mode = 99, songID = row[0], title = row[1], artist = row[2], filename = row[3], artistID = row[4], bitrate = row[5], length = row[6], genre = row[7], track = row[8], date = row[9], album = row[10], albumID = row[11], genreID = genreID),))
			cursor.execute("SELECT genre_text from genre where genre_ID = %d;" % genreID)
			row = cursor.fetchone()
			self["headertext"].setText(_("Genre (%s) -> Song List") % row[0])
			cursor.close() 
			connection.close()
			self["list"].setList(genreSongList)
			if len(genreSongList) > 1:
				self["list"].moveToIndex(1)

	def setButtons(self, red = False, green = False, yellow = False, blue = False):
		if red:
			self["key_red"].setText(_("Main Menu"))
		else:
			self["key_red"].setText("")
		if green:
			self["key_green"].setText(_("Play"))
		else:
			self["key_green"].setText("")
		if yellow:
			self["key_yellow"].setText(_("All Artists"))
		else:
			self["key_yellow"].setText("")
		if blue:
			self["key_blue"].setText(_("Show Album"))
		else:
			self["key_blue"].setText("")

	def info_pressed(self):
		self.startMerlinPlayerScreenTimer.stop()
		if self.player is not None:
			if self.player.songList:
				self.session.execDialog(self.player)

	def green_pressed(self):
		try:
			sel = self["list"].l.getCurrentSelection()[0]
		except: 
			sel = None
		if sel is None:
			return
		if sel.songID != 0:
			if self.player is not None:
				self.player.doClose()
				self.player = None
			self.startMerlinPlayerScreenTimer.stop()
			self.player = self.session.instantiateDialog(MerlinMusicPlayerScreen,self["list"].getList()[1:], self["list"].getCurrentIndex() -1, True, self.currentService, self.serviceList)
			self.session.execDialog(self.player)

	def red_pressed(self):
		self.cacheList = []
		self.setButtons()
		self.mode = 0
		self["list"].setMode(self.mode)
		self.buildMainMenuList()

	def yellow_pressed(self):
		try:
			sel = self["list"].l.getCurrentSelection()[0]
		except: 
			return
		if sel.artistID != 0:
			oldmode = self.mode
			self.mode = 19
			self.setButtons(red = True, green = True, blue = True)
			self["list"].setMode(self.mode)
			self.buildArtistSongList(artistID = sel.artistID, mode = oldmode, addToCache = True)

	def blue_pressed(self):
		try:
			sel = self["list"].l.getCurrentSelection()[0]
		except: 
			return
		if sel.albumID != 0:
			self.setButtons(red = True, green = True, yellow = True)
			oldmode = self.mode
			self.mode = 18
			self["list"].setMode(self.mode)
			self.buildAlbumSongList(albumID = sel.albumID, mode = oldmode, addToCache = True)

	def buildSongList(self, addToCache):
		if addToCache:
			self.cacheList.append(CacheList(index = self["list"].getCurrentIndex(), listview = self["list"].getList(), headertext = self["headertext"].getText(), methodarguments = self.LastMethod))
		arguments = {}
		arguments["addToCache"] = False
		self.LastMethod = MethodArguments(method = self.buildSongList, 	arguments = arguments)
		self["headertext"].setText(_("All Songs"))
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			SongList = []
			SongList.append((Item(text = _("[back]"), mode = 0, navigator = True),))
			cursor.execute("select song_id, title, artists.artist, filename, songs.artist_id, bitrate, length, genre_text, track, date, album_text, songs.Album_id from songs inner join artists on songs.artist_id = artists.artist_id inner join Album on songs.Album_id = Album.Album_id inner join genre on songs.genre_id = genre.genre_id order by title, filename;")
			for row in cursor:
				SongList.append((Item(mode = 99, songID = row[0], title = row[1], artist = row[2], filename = row[3], artistID = row[4], bitrate = row[5], length = row[6], genre = row[7], track = row[8], date = row[9], album = row[10], albumID = row[11]),))
			cursor.close() 
			connection.close()
			self["list"].setList(SongList)
			if len(SongList) > 1:
				self["list"].moveToIndex(1)

	def buildSearchSongList(self, sql_where, headerText, mode, addToCache):
		if addToCache:
			self.cacheList.append(CacheList(index = self["list"].getCurrentIndex(), listview = self["list"].getList(), headertext = self["headertext"].getText(), methodarguments = self.LastMethod))
		arguments = {}
		arguments["sql_where"] = sql_where
		arguments["headerText"] = headerText
		arguments["mode"] = mode
		arguments["addToCache"] = False
		self.LastMethod = MethodArguments(method = self.buildSearchSongList, arguments = arguments)
		self["headertext"].setText(headerText)
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			SongList = []
			SongList.append((Item(text = _("[back]"), mode = mode, navigator = True),))
			cursor.execute("select song_id, title, artists.artist, filename, songs.artist_id, bitrate, length, genre_text, track, date, album_text, songs.Album_id from songs inner join artists on songs.artist_id = artists.artist_id inner join Album on songs.Album_id = Album.Album_id inner join genre on songs.genre_id = genre.genre_id %s order by title, filename;" % sql_where)
			for row in cursor:
				SongList.append((Item(mode = 99, songID = row[0], title = row[1], artist = row[2], filename = row[3], artistID = row[4], bitrate = row[5], length = row[6], genre = row[7], track = row[8], date = row[9], album = row[10], albumID = row[11]),))
			cursor.close() 
			connection.close()
			self["list"].setList(SongList)
			if len(SongList) > 1:
				self["list"].moveToIndex(1)

	def buildArtistSongList(self, artistID, mode, addToCache):
		if addToCache:
			self.cacheList.append(CacheList(index = self["list"].getCurrentIndex(), listview = self["list"].getList(), headertext = self["headertext"].getText(), methodarguments = self.LastMethod))
		arguments = {}
		arguments["artistID"] = artistID
		arguments["mode"] = mode
		arguments["addToCache"] = False
		self.LastMethod = MethodArguments(method = self.buildArtistSongList, arguments = arguments)
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			artistSongList = []
			artistSongList.append((Item(text = _("[back]"), mode = mode, navigator = True),))
			cursor.execute("select song_id, title, artists.artist, filename, bitrate, length, genre_text, track, date, album_text, songs.Album_id from songs inner join artists on songs.artist_id = artists.artist_id inner join Album on songs.Album_id = Album.Album_id inner join genre on songs.genre_id = genre.genre_id where songs.artist_id = %d order by Album.album_text, tracknumber, filename;" % (artistID))
			for row in cursor:
				artistSongList.append((Item(mode = 99, songID = row[0], title = row[1], artist = row[2], filename = row[3], bitrate = row[4], length = row[5], genre = row[6], track = row[7], date = row[8], album = row[9], albumID = row[10], artistID = artistID),))
			cursor.execute("SELECT artist from artists where artist_ID = %d;" % artistID)
			row = cursor.fetchone()
			self["headertext"].setText(_("Artist (%s) -> Song List") % row[0])
			cursor.close() 
			connection.close()
			self["list"].setList(artistSongList)
			if len(artistSongList) > 1:
				self["list"].moveToIndex(1)

	def buildAlbumSongList(self, albumID, mode, addToCache):
		if addToCache:
			self.cacheList.append(CacheList(index = self["list"].getCurrentIndex(), listview = self["list"].getList(), headertext = self["headertext"].getText(), methodarguments = self.LastMethod))
		arguments = {}
		arguments["albumID"] = albumID
		arguments["mode"] = mode
		arguments["addToCache"] = False
		self.LastMethod = MethodArguments(method = self.buildAlbumSongList, arguments = arguments)
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			albumSongList = []
			albumSongList.append((Item(text = _("[back]"), mode = mode, navigator = True),))
			cursor.execute("select song_id, title, artists.artist, filename, songs.artist_id, bitrate, length, genre_text, track, date, album_text from songs inner join artists on songs.artist_id = artists.artist_id inner join Album on songs.Album_id = Album.Album_id inner join genre on songs.genre_id = genre.genre_id where songs.album_id = %d order by tracknumber, filename;" % (albumID))
			for row in cursor:
				albumSongList.append((Item(mode = 99, songID = row[0], title = row[1], artist = row[2], filename = row[3], artistID = row[4], bitrate = row[5], length = row[6], genre = row[7], track = row[8], date = row[9], album = row[10], albumID = albumID),))
			cursor.execute("SELECT album_text from album where album_ID = %d;" % albumID)
			row = cursor.fetchone()
			self["headertext"].setText(_("Album (%s) -> Song List") % row[0])
			cursor.close() 
			connection.close()
			self["list"].setList(albumSongList)
			if len(albumSongList) > 1:
				self["list"].moveToIndex(1)

	def buildMainMenuList(self, addToCache = True):
		arguments = {}
		arguments["addToCache"] = True
		self.LastMethod = MethodArguments(method = self.buildMainMenuList, arguments = arguments)
		self["headertext"].setText(_("iDream Main Menu"))
		mainMenuList = []
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			# 1. Playlists
			cursor.execute("SELECT COUNT (*) FROM playlists;")
			row = cursor.fetchone()
			mainMenuList.append((Item(text = _("Playlists (%d)") % row[0], mode = 1),))
			# 2. Artists
			cursor.execute("SELECT COUNT (*) FROM artists;")
			row = cursor.fetchone()
			mainMenuList.append((Item(text = _("Artists (%d)") % row[0], mode = 4),))
			# 3. Albums
			cursor.execute("SELECT COUNT (DISTINCT album_text) FROM album;")
			row = cursor.fetchone()
			mainMenuList.append((Item(text = _("Albums (%d)") % row[0], mode = 7),))
			# 4. Songs
			cursor.execute("SELECT COUNT (*) FROM songs;")
			row = cursor.fetchone()
			mainMenuList.append((Item(text = _("Songs (%d)") % row[0], mode = 10),))
			# 5. Genres
			cursor.execute("SELECT COUNT (*) FROM genre;")
			row = cursor.fetchone()
			mainMenuList.append((Item(text = _("Genres (%d)") % row[0], mode = 13),))
			cursor.close()  
			connection.close()
			self["list"].setList(mainMenuList)
			self["list"].moveToIndex(0)

	def buildArtistList(self, addToCache):
		if addToCache:
			self.cacheList.append(CacheList(index = self["list"].getCurrentIndex(), listview = self["list"].getList(), headertext = self["headertext"].getText(), methodarguments = self.LastMethod))
		arguments = {}
		arguments["addToCache"] = False
		self.LastMethod = MethodArguments(method = self.buildArtistList, arguments = arguments)
		self["headertext"].setText(_("Artists List"))
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			artistList = []
			artistList.append((Item(text = _("[back]"), mode = 0, navigator = True),))
			cursor.execute("SELECT artists.artist_id,artists.artist, count (distinct album.album_text) FROM songs INNER JOIN artists ON songs.artist_id = artists.artist_id inner join album on songs.album_id =  album.album_id GROUP BY songs.artist_id ORDER BY artists.artist;")
			for row in cursor:
				artistList.append((Item(text = "%s (%d)" % (row[1], row[2]), mode = 5, artistID = row[0]),))
			cursor.close() 
			connection.close()
			self["list"].setList(artistList)
		
	def buildArtistAlbumList(self, ArtistID, addToCache):
		if addToCache:
			self.cacheList.append(CacheList(index = self["list"].getCurrentIndex(), listview = self["list"].getList(), headertext = self["headertext"].getText(), methodarguments = self.LastMethod))
		arguments = {}
		arguments["ArtistID"] = ArtistID
		arguments["addToCache"] = False
		self.LastMethod = MethodArguments(method = self.buildArtistAlbumList, arguments = arguments)
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			albumArtistList = []
			albumArtistList.append((Item(text = _("[back]"), mode = 4, navigator = True),))
			cursor.execute("select Album.Album_id,Album.Album_text from songs inner join Album on songs.Album_id = Album.Album_id where songs.artist_id = %d group by songs.Album_id order by Album.Album_text;" % ArtistID)
			for row in cursor:
				cursor2 = connection.cursor()
				cursor2.execute("select count(song_id) from songs where album_id = %d;" % row[0])
				row2 = cursor2.fetchone()
				albumArtistList.append((Item(text = "%s (%d)" % (row[1], row2[0]), mode = 6, albumID = row[0], artistID = ArtistID),))
				cursor2.close()
			cursor.execute("SELECT artist from artists where artist_ID = %d;" % ArtistID)
			row = cursor.fetchone()
			self["headertext"].setText(_("Artist (%s) -> Album List") % row[0])
			cursor.close() 
			connection.close()
			self["list"].setList(albumArtistList)
			if len(albumArtistList) > 1:
				self["list"].moveToIndex(1)

	def buildAlbumList(self, addToCache):
		if addToCache:
			self.cacheList.append(CacheList(index = self["list"].getCurrentIndex(), listview = self["list"].getList(), headertext = self["headertext"].getText(), methodarguments = self.LastMethod))
		arguments = {}
		arguments["addToCache"] = False
		self.LastMethod = MethodArguments(method = self.buildAlbumList, arguments = arguments)
		self["headertext"].setText(_("Albums List"))
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			albumList = []
			albumList.append((Item(text = _("[back]"), mode = 0, navigator = True),))
			cursor.execute("select Album.Album_id,Album.Album_text, count(*) from songs inner join Album on songs.Album_id = Album.Album_id group by songs.Album_id order by Album.Album_text;")
			for row in cursor:
				albumList.append((Item(text = "%s (%d)" % (row[1], row[2]), mode = 8, albumID = row[0]),))
			cursor.close() 
			connection.close()
			self["list"].setList(albumList)
			if len(albumList) > 1:
				self["list"].moveToIndex(1)

	def startRun(self):
		if pathToDatabase.isRunning:
			self.showScanner = eTimer()
			self.showScanner.callback.append(self.showScannerCallback)
			self.showScanner.start(0,1)
		else:
			if config.plugins.merlinmusicplayer.startlastsonglist.value:
				self.startPlayerTimer = eTimer()
				self.startPlayerTimer.callback.append(self.startPlayerTimerCallback)
				self.startPlayerTimer.start(0,1)
			self.mode = 0
			self["list"].setMode(self.mode)
			self.buildMainMenuList()

	def showScannerCallback(self):
		self.session.openWithCallback(self.filesAdded, iDreamAddToDatabase,None)

	def startPlayerTimerCallback(self):
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			iDreamMode = False
			SongList = []
			cursor.execute("select song_id, filename, title, artist, album, genre, bitrate, length,  track, date, PTS from CurrentSongList;")
			for row in cursor:
				SongList.append((Item(songID = row[0], text = os_path.basename(row[1]), filename = row[1], title = row[2], artist = row[3], album = row[4], genre = row[5],  bitrate = row[6], length = row[7], track = row[8], date = row[9], PTS = row[10], join = False),))
				if row[0] != 0:
					iDreamMode = True
			cursor.close() 
			connection.close()
			if self.player is not None:
				self.player.doClose()
				self.player = None
			self.startMerlinPlayerScreenTimer.stop()
			count = len(SongList)
			if count:
				# just to be sure, check the index , it's critical
				index = config.plugins.merlinmusicplayer.lastsonglistindex.value
				if index >= count:
					index = 0
				self.player = self.session.instantiateDialog(MerlinMusicPlayerScreen,SongList, index, iDreamMode, self.currentService, self.serviceList)
				self.session.execDialog(self.player)

	def config(self):
		self.startMerlinPlayerScreenTimer.stop()
		self.session.openWithCallback(self.setupFinished, MerlinMusicPlayerSetup, True)

	def setupFinished(self, result):
		if result:
			self.red_pressed()

	def stopPlayingAndAppendFileToSongList(self):
		self.startMerlinPlayerScreenTimer.stop()
		if self.player is not None:
			self.player.doClose()
			self.player = None
		self.appendFileToSongList()
		self.startMerlinPlayerScreenTimer.start(START_MERLIN_PLAYER_SCREEN_TIMER_VALUE)

	def appendFileToSongList(self):
		SongList = []
		playerAvailable =  self.player is not None and self.player.songList
		sel = self.getCurrentSelection()
		if sel:
			if playerAvailable:
				self.player.songList.append((sel,))
				self.player.origSongList.append((sel,))
			else:
				SongList.append((sel,))
			if not playerAvailable:
				if self.player is not None:
					self.player.doClose()
					self.player = None
				self.player = self.session.instantiateDialog(MerlinMusicPlayerScreen,SongList, 0, True, self.currentService, self.serviceList)
				self.player.playSong(self.player.songList[self.player.currentIndex][0].filename)
				self.player["coverArt"].onShow()
				self.player.init = 1
			else:
				self.player["nextTitle"].setText(self.player.getNextTitle())
				self.session.open(MessageBox, _("%s\nappended to songlist") % sel.title, type = MessageBox.TYPE_INFO,timeout = 3)

	def insertFileToSongList(self):
		sel = self.getCurrentSelection()
		if sel:
			if self.player is not None and self.player.songList:
				index = self.player.currentIndex
				self.player.songList.insert(index+1,(sel,))
				self.player.origSongList.insert(index+1,(sel,))
				self.player["nextTitle"].setText(self.player.getNextTitle())
				self.session.open(MessageBox, _("%s\ninserted and will be played as next song") % sel.title, type = MessageBox.TYPE_INFO,timeout = 3)
			else:
				self.appendFileToSongList()

	def Error(self, error = None):
		if error is not None:
			self["list"].hide()
			self["statustext"].setText(str(error.getErrorMessage()))

	def closing(self):
		self.close()

	def __onClose(self):
		self.startMerlinPlayerScreenTimer.stop()
		if self.player is not None:
			self.player.closePlayer()
			self.player.doClose()
			self.player = None
		if self.serviceList is None:
			self.session.nav.playService(self.currentService, adjust=False)
		else:
			current = ServiceReference(self.serviceList.getCurrentSelection())
			self.session.nav.playService(current.ref, adjust=False)

	def lcdUpdate(self):
		self.startMerlinPlayerScreenTimer.start(START_MERLIN_PLAYER_SCREEN_TIMER_VALUE)
		try:
			count = self["list"].getItemCount()
			index = self["list"].getCurrentIndex()
			iDreamList = self["list"].getList()
			self.summaries.setText(iDreamList[index][0].title or iDreamList[index][0].text,1)
			# voheriges
			index -= 1
			if index < 0:
				index = count
			self.summaries.setText(iDreamList[index][0].title or iDreamList[index][0].text,3)
			# naechstes
			index = self["list"].getCurrentIndex() + 1
			if index > count:
				index = 0
			self.summaries.setText(iDreamList[index][0].title or iDreamList[index][0].text,4)
		except: pass

	def createSummary(self):
		return MerlinMusicPlayerLCDScreenText


class iDreamList(GUIComponent, object):
	def buildEntry(self, item):
		width = self.l.getItemSize().width()
		res = [ None ]
		if self.displaySongMode:
			if item.navigator:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 3, width , 20, 0, RT_HALIGN_CENTER|RT_VALIGN_CENTER, "%s" % item.text))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 3, width - 100 , 20, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, "%s - %s" % (item.title, item.artist)))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 100,3,100, 20, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, "%s" % item.track))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 26,width -200, 18, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, "%s%s" % (item.album, item.date)))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, width -200, 26,200, 18, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, "%s" % item.length))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 47,width -200, 18, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, "%s" % item.genre))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, width -200, 47,200, 18, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, "%s" % item.bitrate))
		else:
			if item.navigator:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 3, width , 20, 0, RT_HALIGN_CENTER|RT_VALIGN_CENTER, "%s" % item.text))
			else:
				if item.PTS is None:
					res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 3, width , 20, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, "%s" % item.text))
				else:
					res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 3, width , 20, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, "%s" % item.title))
		return res

	def __init__(self):
		GUIComponent.__init__(self)
		self.l = eListboxPythonMultiContent()
		self.l.setBuildFunc(self.buildEntry)
		font = skin.fonts.get("iDreamListFont0", ("Regular", 20))
		self.l.setFont(0, gFont(font[0], font[1]))
		font = skin.fonts.get("iDreamListFont1", ("Regular", 16))
		self.l.setFont(1, gFont(font[0], font[1]))
		font = skin.fonts.get("iDreamListItem", (22, 68))
		self.item = font[0]
		self.item1 = font[1]
		self.l.setItemHeight(self.item)
		self.onSelectionChanged = [ ]
		self.mode = 0
		self.displaySongMode = False
		self.list = []
		self.itemCount = 0

	def connectSelChanged(self, fnc):
		if not fnc in self.onSelectionChanged:
			self.onSelectionChanged.append(fnc)

	def disconnectSelChanged(self, fnc):
		if fnc in self.onSelectionChanged:
			self.onSelectionChanged.remove(fnc)

	def selectionChanged(self):
		for x in self.onSelectionChanged:
			x()

	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.setWrapAround(True)
		instance.selectionChanged.get().append(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		instance.selectionChanged.get().remove(self.selectionChanged)

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	currentIndex = property(getCurrentIndex, moveToIndex)
	currentSelection = property(getCurrent)

	def setList(self, list):
		self.list = list
		self.l.setList(list)
		self.itemCount = len(self.list) - 1

	def getItemCount(self):
		return  self.itemCount

	def getList(self):
		return self.list

	def removeItem(self, index):
		del self.list[index]
		self.l.entryRemoved(index)

	def getDisplaySongMode(self):
		return self.displaySongMode
		
	def setMode(self, mode):
		self.mode = mode
		if mode == 2 or mode == 6 or mode == 8 or mode == 10 or mode == 18 or mode == 19 or mode == 14 or mode == 20:
			self.displaySongMode = True
			self.l.setItemHeight(self.item1)
		else:
			self.displaySongMode = False
			self.l.setItemHeight(self.item)

class MerlinMediaPixmap(Pixmap):
	def __init__(self):
		Pixmap.__init__(self)
		self.coverArtFileName = ""
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintCoverArtPixmapCB)
		self.coverFileNames = ["folder.png", "folder.jpg", "cover.jpg", "cover.png", "coverArt.jpg"]

	def applySkin(self, desktop, screen):
		from Tools.LoadPixmap import LoadPixmap
		noCoverFile = None
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "pixmap":
					noCoverFile = value
					break
		if noCoverFile is None:
			noCoverFile = resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/no_coverArt.png")
		self.noCoverPixmap = LoadPixmap(noCoverFile)
		return Pixmap.applySkin(self, desktop, screen)

	def onShow(self):
		Pixmap.onShow(self)
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((self.instance.size().width(), self.instance.size().height(), sc[0], sc[1], False, 1, "#00000000"))

	def paintCoverArtPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr != None:
			self.instance.setPixmap(ptr.__deref__())

	def updateCoverArt(self, path):
		back = False
		while not path.endswith("/"):
			path = path[:-1]
		new_coverArtFileName = None
		for filename in self.coverFileNames:
			if fileExists(path + filename):
				new_coverArtFileName = path + filename
		if self.coverArtFileName != new_coverArtFileName:
			if new_coverArtFileName:
				self.coverArtFileName = new_coverArtFileName
				print "[MerlinMusicPlayer] using cover from %s " % self.coverArtFileName
				self.picload.startDecode(self.coverArtFileName)
				back = True
		else:
			if new_coverArtFileName:
				back = True
		return back

	def showDefaultCover(self):
		self.coverArtFileName = ""
		self.instance.setPixmap(self.noCoverPixmap)

	def showCoverFromFile(self, filename):
		self.coverArtFileName = filename
		self.picload.startDecode(self.coverArtFileName)

	def embeddedCoverArt(self):
		print "[embeddedCoverArt] found"
		self.coverArtFileName = "/tmp/.id3coverart"
		self.picload.startDecode(self.coverArtFileName)


class SelectPath(Screen):
	skin = """<screen name="SelectPath" position="center,center" size="560,320" title="Select path">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget name="target" position="0,60" size="540,22" valign="center" font="Regular;22" />
			<widget name="filelist" position="0,100" zPosition="1" size="560,220" scrollbarMode="showOnDemand"/>
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""
	def __init__(self, session, initDir):
		Screen.__init__(self, session)
		self.setTitle(_("Select path"))
		inhibitDirs = ["/bin", "/boot", "/dev", "/etc", "/lib", "/proc", "/sbin", "/sys", "/usr", "/var"]
		inhibitMounts = []
		self["filelist"] = FileList(initDir, showDirectories = True, showFiles = False, inhibitMounts = inhibitMounts, inhibitDirs = inhibitDirs)
		self["target"] = Label()
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions"],
		{
			"back": self.cancel,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
			"ok": self.ok,
			"green": self.green,
			"red": self.cancel
		}, -1)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

	def cancel(self):
		self.close(None)

	def green(self):
		self.close(self["filelist"].getSelection()[0])

	def up(self):
		self["filelist"].up()
		self.updateTarget()

	def down(self):
		self["filelist"].down()
		self.updateTarget()

	def left(self):
		self["filelist"].pageUp()
		self.updateTarget()

	def right(self):
		self["filelist"].pageDown()
		self.updateTarget()

	def ok(self):
		if self["filelist"].canDescent():
			self["filelist"].descent()
			self.updateTarget()

	def updateTarget(self):
		currFolder = self["filelist"].getSelection()[0]
		if currFolder is not None:
			self["target"].setText(currFolder)
		else:
			self["target"].setText(_("Invalid Location"))

class MerlinMusicPlayerLCDScreen(Screen):
	skin = """
		<screen position="0,0" size="132,64">
			<widget source="session.CurrentService" render="Label" position="4,0" size="132,12" valign="top" font="Regular;10" halign="center">
				<convert type="ServicePosition">Position,ShowHours</convert>
			</widget>
			<widget name="text1" position="4,14" size="132,35" halign="center" valign="top" font="Regular;14"/>
			<widget name="text4" position="4,51" size="132,12" halign="center" valign="top" font="Regular;10"/>
		</screen>"""

	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self["text1"] = Label()
		self["text4"] = Label()

	def setText(self, text, line):
		if line == 1:
			self["text1"].setText(text)
		elif line == 4:
			self["text4"].setText(text)

class MerlinMusicPlayerLCDScreenText(Screen):
	skin = """
		<screen position="0,0" size="132,64">
			<widget name="text3" position="4,0" size="132,14" font="Regular;10"/>
			<widget name="text1" position="4,14" size="132,35" font="Regular;14"/>
			<widget name="text4" position="4,49" size="132,14" font="Regular;10"/>
		</screen>"""

	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self["text1"] = Label()
		self["text3"] = Label()
		self["text4"] = Label()

	def setText(self, text, line):
		textleer = "    "
		text = text + textleer*10
		if line == 1:
			self["text1"].setText(text)
		elif line == 3:
			self["text3"].setText(text)
		elif line == 4:
			self["text4"].setText(text)

class MerlinMusicPlayerSetup(Screen, ConfigListScreen):
	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:
		skin = """
			<screen position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#00000000" title="Merlin Music Player Setup" >
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/mmpborderHD.png" position="128,72" size="1024,576"/>
				<ePixmap position="178,102" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="328,102" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<widget render="Label" source="key_red" position="178,102" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_green" position="328,102" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="config" position="178,152" size="924,350" backgroundColor="#00000000" scrollbarMode="showOnDemand" />
			</screen>"""

	elif sz_w == 1024:
		skin = """
			<screen position="0,0" size="1024,576" flags="wfNoBorder" backgroundColor="#00000000" title="Merlin Music Player Setup" >
				<ePixmap position="50,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="200,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<widget render="Label" source="key_red" position="50,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_green" position="200,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="config" position="50,80" size="924,350" backgroundColor="#00000000" scrollbarMode="showOnDemand" />
			</screen>"""
	else:
		skin = """
			<screen position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="#00000000" title="Merlin Music Player Setup">
				<ePixmap position="50,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="200,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<widget render="Label" source="key_red" position="50,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_green" position="200,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="config" position="50,80" size="620,350" backgroundColor="#00000000" scrollbarMode="showOnDemand" />
			</screen>"""


	def __init__(self, session, databasePath):
		Screen.__init__(self, session)
		self.setTitle(_("Merlin Music Player Setup"))

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self.list = [ ]
		self.list.append(getConfigListEntry(_("Play last used songlist after starting"), config.plugins.merlinmusicplayer.startlastsonglist))
		if databasePath:
			self.database = getConfigListEntry(_("iDream database path"), config.plugins.merlinmusicplayer.databasepath)
			self.list.append(self.database)
		else:
			self.database = None
		self.list.append(getConfigListEntry(_("Use google-images for cover art"), config.plugins.merlinmusicplayer.usegoogleimage))
		self.googleimage = getConfigListEntry(_("Google image path"), config.plugins.merlinmusicplayer.googleimagepath)
		self.list.append(self.googleimage)
		self.list.append(getConfigListEntry(_("Activate screensaver"), config.plugins.merlinmusicplayer.usescreensaver))
		self.list.append(getConfigListEntry(_("Wait for screensaver (in min)"), config.plugins.merlinmusicplayer.screensaverwait))
		self.list.append(getConfigListEntry(_("Remember last path of filebrowser"), config.plugins.merlinmusicplayer.rememberlastfilebrowserpath))
		self.defaultFileBrowserPath = getConfigListEntry(_("Filebrowser startup path"), config.plugins.merlinmusicplayer.defaultfilebrowserpath)
		self.list.append(self.defaultFileBrowserPath)
		self.list.append(getConfigListEntry(_("Show iDream in extensions menu"), config.plugins.merlinmusicplayer.idreamextendedpluginlist))
		self.list.append(getConfigListEntry(_("Show Merlin Music Player in extensions menu"), config.plugins.merlinmusicplayer.merlinmusicplayerextendedpluginlist))
		self.list.append(getConfigListEntry(_("Show iDream in main menu"), config.plugins.merlinmusicplayer.idreammainmenu))
		self.list.append(getConfigListEntry(_("Show Merlin Music Player in main menu"), config.plugins.merlinmusicplayer.merlinmusicplayermainmenu))

		ConfigListScreen.__init__(self, self.list, session)
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyClose,
			"ok": self.keySelect,
		}, -2)

	def keySelect(self):
		cur = self["config"].getCurrent()
		if cur == self.database:
			self.session.openWithCallback(self.pathSelectedDatabase,SelectPath,config.plugins.merlinmusicplayer.databasepath.value)
		elif cur == self.defaultFileBrowserPath:
			self.session.openWithCallback(self.pathSelectedFilebrowser,SelectPath,config.plugins.merlinmusicplayer.defaultfilebrowserpath.value)
		elif cur == self.googleimage:
			self.session.openWithCallback(self.pathSelectedGoogleImage,SelectPath,config.plugins.merlinmusicplayer.googleimagepath.value)

	def pathSelectedGoogleImage(self, res):
		if res is not None:
			config.plugins.merlinmusicplayer.googleimagepath.value = res

	def pathSelectedDatabase(self, res):
		if res is not None:
			config.plugins.merlinmusicplayer.databasepath.value = res

	def pathSelectedFilebrowser(self, res):
		if res is not None:
			config.plugins.merlinmusicplayer.defaultfilebrowserpath.value = res

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		self.close(True)

	def keyClose(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close(False)


class MerlinMusicPlayerFileList(Screen):
	
	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:
		skin = """
			<screen name="MerlinMusicPlayerFileList" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#00000000" title="iDream">
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/images/mmpborderHD.png" position="128,72" size="1024,576"/>
			<eLabel backgroundColor="#999999" position="178,112" size="924,2" zPosition="1"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="178,104" size="250,20" text="MERLIN  MUSIC  PLAYER" valign="center" zPosition="2"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="852,104" size="250,20" text="WWW.DREAMBOX-TOOLS.INFO" valign="center" zPosition="2"/>
			<widget name="headertext" position="178,145" zPosition="1" size="900,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
			<widget name="list" position="178,182" zPosition="2" size="940,350" scrollbarMode="showOnDemand" transparent="0"  backgroundColor="#00000000"/>
			</screen>"""
	elif sz_w == 1024:
		skin = """
			<screen name="MerlinMusicPlayerFileList" position="0,0" size="1024,576" flags="wfNoBorder" backgroundColor="#00000000" title="iDream">
			<eLabel backgroundColor="#999999" position="50,40" size="924,2" zPosition="1"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="50,32" size="250,20" text="MERLIN  MUSIC  PLAYER" valign="center" zPosition="2"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="724,32" size="250,20" text="WWW.DREAMBOX-TOOLS.INFO" valign="center" zPosition="2"/>
			<widget name="headertext" position="50,73" zPosition="1" size="900,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
			<widget name="list" position="50,110" zPosition="2" size="940,350" scrollbarMode="showOnDemand" transparent="0"  backgroundColor="#00000000"/>
			</screen>"""
	else:
		skin = """
			<screen name="MerlinMusicPlayerFileList" position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="#00000000" title="iDream">
			<eLabel backgroundColor="#999999" position="50,50" size="620,2" zPosition="1"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="50,40" size="250,20" text="MERLIN  MUSIC  PLAYER" valign="center" zPosition="2"/>
			<eLabel backgroundColor="#999999" font="Regular;16" foregroundColor="#0f0f0f" halign="center" position="420,40" size="250,20" text="WWW.DREAMBOX-TOOLS.INFO" valign="center" zPosition="2"/>

			<widget name="headertext" position="50,73" zPosition="1" size="620,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
			<widget name="list" position="50,110" zPosition="2" size="620,350" scrollbarMode="showOnDemand" transparent="0"  backgroundColor="#00000000"/>
			</screen>"""
		
	
	def __init__(self, session, servicelist):
		self.session = session
		Screen.__init__(self, session)
		self["list"] = FileList(config.plugins.merlinmusicplayer.defaultfilebrowserpath.value, showDirectories = True, showFiles = True, matchingPattern = "(?i)^.*\.(mp3|m4a|flac|ogg|m3u|pls|cue)", useServiceRef = False)

		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions"],
		{
			"ok": self.ok,
			"back": self.close,
			"menu": self.menu_pressed,
			"info" : self.info_pressed,
			"green": self.green_pressed,
			"up": self.moveup,
			"down": self.movedown,
			"right": self.moveright,
			"left" : self.moveleft,
			"blue" : self.appendFileToSongList,
			"yellow" : self.insertFileToSongList,
			"red" : self.stopPlayingAndAppendFileToSongList,
		}, -1)
		self.serviceList = servicelist
		self["headertext"] = Label()
		self.player = None
		self.onClose.append(self.__onClose)
		self.onLayoutFinish.append(self.startRun)
		self.onShown.append(self.updateTarget)
		self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()

		self.startMerlinPlayerScreenTimer = eTimer()
		self.startMerlinPlayerScreenTimer.timeout.get().append(self.info_pressed)

	def startRun(self):
		if config.plugins.merlinmusicplayer.startlastsonglist.value:
			self.startPlayerTimer = eTimer()
			self.startPlayerTimer.callback.append(self.startPlayerTimerCallback)
			self.startPlayerTimer.start(0,1)

	def startPlayerTimerCallback(self):
		connection = OpenDatabase()
		if connection is not None:
			connection.text_factory = str
			cursor = connection.cursor()
			iDreamMode = False
			SongList = []
			cursor.execute("select song_id, filename, title, artist, album, genre, bitrate, length,  track, date, PTS from CurrentSongList;")
			for row in cursor:
				SongList.append((Item(songID = row[0], text = os_path.basename(row[1]), filename = row[1], title = row[2], artist = row[3], album = row[4], genre = row[5],  bitrate = row[6], length = row[7], track = row[8], date = row[9], PTS = row[10], join = False),))
				if row[0] != 0:
					iDreamMode = True
			cursor.close() 
			connection.close()
			if self.player is not None:
				self.player.doClose()
				self.player = None
			self.startMerlinPlayerScreenTimer.stop()
			count = len(SongList)
			if count:
				# just to be sure, check the index , it's critical
				index = config.plugins.merlinmusicplayer.lastsonglistindex.value
				if index >= count:
					index = 0
				self.player = self.session.instantiateDialog(MerlinMusicPlayerScreen,SongList, index, iDreamMode, self.currentService, self.serviceList)
				self.session.execDialog(self.player)

	def readCUE(self, filename):
		SongList = []
		displayname = None
		try:
			cuefile = open(filename, "r")
		except IOError:
			return None
		import re
		performer_re = re.compile(r"""PERFORMER "(?P<performer>.*?)"(?:=\r\n|\r|\n|$)""")
		title_re = re.compile(r"""TITLE "(?P<title>.*?)"(?:=\r\n|\r|\n|$)""")
		filename_re = re.compile(r"""FILE "(?P<filename>.+?)".*(?:=\r\n|\r|\n|$)""", re.DOTALL)
		track_re = re.compile(r"""TRACK (?P<track_number>[^ ]+?)(?:[ ]+.*?)(?:=\r\n|\r|\n|$)""")
		index_re = re.compile(r"""INDEX (?P<index_nr>[^ ]+?)[ ]+(?P<track_index>[^ ]+?)(?:=\r\n|\r|\n|$)""")
		msts_re = re.compile("""^(?P<mins>[0-9]{1,}):(?P<secs>[0-9]{2}):(?P<ms>[0-9]{2})$""")
		songfilename = ""
		album = ""
		performer = ""
		title = ""
		pts = 0
		state = 0 # header
		for line in cuefile.readlines():
			entry = line.strip()
			m = filename_re.search(entry)
			if m:
				if  m.group('filename')[0] == "/":
					songfilename = m.group('filename')
				else:
					songfilename = os_path.join(os_path.dirname(filename), m.group('filename'))
			m = title_re.search(entry)
			if m:
				if state == 0:
					album = m.group('title')
				else:
					title = m.group('title')
			m = performer_re.search(entry)
			if m:
				performer = m.group('performer')
			m = track_re.search(entry)
			if m:
				state = 1 # tracks
			m = index_re.search(entry)
			if m:
				if int(m.group('index_nr')) == 1:
					m1 = msts_re.search(m.group('track_index'))
					if m1:
						pts = (int(m1.group('mins')) * 60 + int(m1.group('secs'))) * 90000
						SongList.append((Item(text = title, filename = songfilename, title = title, artist = performer, album = album,join = False, PTS = pts),))
		cuefile.close()
		return SongList

	def readM3U(self, filename):
		SongList = []
		displayname = None
		try:
			m3ufile = open(filename, "r")
		except IOError:
			return None
		for line in m3ufile.readlines():
			entry = line.strip()
			if entry != "":
				if entry.startswith("#EXTINF:"):
					extinf = entry.split(',',1)
					if len(extinf) > 1:
						displayname = extinf[1]
				elif entry[0] != "#":
					if entry[0] == "/":
						songfilename = entry
					else:
						songfilename = os_path.join(os_path.dirname(filename),entry)
					if displayname:
						text = displayname
						displayname = None
					else:
						text = entry
					SongList.append((Item(text = text, filename = songfilename),))
		m3ufile.close()
		return SongList

	def readPLS(self, filename):
		SongList = []
		displayname = None
		try:
			plsfile = open(filename, "r")
		except IOError:
			return None
		entry = plsfile.readline().strip()
		if entry == "[playlist]":
			while True:
				entry = plsfile.readline().strip()
				if entry == "":
					break
				if entry[0:4] == "File":
					pos = entry.find('=') + 1
					newentry = entry[pos:]
					SongList.append((Item(text = newentry, filename = newentry),))
		else:
			SongList = self.readM3U(filename)
		plsfile.close()
		return SongList

	def green_pressed(self):
		SongList = []
		count = 0
		for root, subFolders, files in os_walk(self["list"].getCurrentDirectory()):
			files.sort()
			for filename in files:
				if filename.lower().endswith(".mp3") or filename.lower().endswith(".flac") or filename.lower().endswith(".m4a") or filename.lower().endswith(".ogg"):
					SongList.append((Item(text = filename, filename = os_path.join(root,filename)),))
		if self.player is not None:
			self.player.doClose()
			self.player = None
		self.startMerlinPlayerScreenTimer.stop()
		count = len(SongList)
		if count:
			self.player = self.session.instantiateDialog(MerlinMusicPlayerScreen,SongList, 0, False, self.currentService, self.serviceList)
			self.session.execDialog(self.player)
		else:
			self.session.open(MessageBox, _("No music files found!"), type = MessageBox.TYPE_INFO,timeout = 20 )

	def ok(self):
		if self["list"].canDescent():
			self["list"].descent()
			self.updateTarget()
		else:
			SongList = []
			foundIndex = 0
			count = 0
			index = 0
			currentFilename = self["list"].getFilename()
 			if currentFilename.lower().endswith(".m3u"):
				SongList = self.readM3U(os_path.join(self["list"].getCurrentDirectory(),currentFilename))
			elif currentFilename.lower().endswith(".pls"):
				SongList = self.readPLS(os_path.join(self["list"].getCurrentDirectory(),currentFilename))
			elif currentFilename.lower().endswith(".cue"):
				SongList = self.readCUE(os_path.join(self["list"].getCurrentDirectory(),currentFilename))
			else:
				files = os_listdir(self["list"].getCurrentDirectory())
				files.sort()
				for filename in files:
					if filename.lower().endswith(".mp3") or filename.lower().endswith(".flac") or filename.lower().endswith(".m4a") or filename.lower().endswith(".ogg"):
						SongList.append((Item(text = filename, filename = os_path.join(self["list"].getCurrentDirectory(),filename)),))
						if self["list"].getFilename() == filename:
							foundIndex = index
						index += 1

			if self.player is not None:
				self.player.doClose()
				self.player = None
			self.startMerlinPlayerScreenTimer.stop()
			count = len(SongList)
			if count:
				self.player = self.session.instantiateDialog(MerlinMusicPlayerScreen, SongList, foundIndex, False, self.currentService, self.serviceList)
				self.session.execDialog(self.player)
			else:
				self.session.open(MessageBox, _("No music files found!"), type = MessageBox.TYPE_INFO,timeout = 20 )

	def config(self):
		self.startMerlinPlayerScreenTimer.stop()
		self.session.open(MerlinMusicPlayerSetup, True)

	def menu_pressed(self):
		self.startMerlinPlayerScreenTimer.stop()
		options = [(_("Configuration"), self.config),]
		if not self["list"].canDescent():
			filename = self["list"].getFilename()
			if filename.lower().endswith(".mp3") or filename.lower().endswith(".flac") or filename.lower().endswith(".m4a") or filename.lower().endswith(".ogg"):
				options.extend(((_("Clear current songlist and play selected entry"), self.stopPlayingAndAppendFileToSongList),))
				options.extend(((_("Append file to current songlist"), self.appendFileToSongList),))
				if self.player is not None and self.player.songList:
					options.extend(((_("Insert file to current songlist and play next"), self.insertFileToSongList),))
		self.session.openWithCallback(self.menuCallback, ChoiceBox,list = options)

	def menuCallback(self, ret):
		ret and ret[1]()

	def stopPlayingAndAppendFileToSongList(self):
		self.startMerlinPlayerScreenTimer.stop()
		if self.player is not None:
			self.player.doClose()
			self.player = None
		self.appendFileToSongList()	
		self.startMerlinPlayerScreenTimer.start(START_MERLIN_PLAYER_SCREEN_TIMER_VALUE)

	def appendFileToSongList(self):
		playerAvailable =  self.player is not None and self.player.songList
		filename = self["list"].getFilename()
		if filename.lower().endswith(".mp3") or filename.lower().endswith(".flac") or filename.lower().endswith(".m4a") or filename.lower().endswith(".ogg"):
			SongList = []
			a = Item(text = filename, filename = os_path.join(self["list"].getCurrentDirectory(),filename))
			if playerAvailable:
				self.player.songList.append((a,))
				self.player.origSongList.append((a,))
			else:
				SongList.append((a,))
			if not playerAvailable:
				if self.player is not None:
					self.player.doClose()
					self.player = None
				self.player = self.session.instantiateDialog(MerlinMusicPlayerScreen,SongList, 0, False, self.currentService, self.serviceList)
				self.player.playSong(self.player.songList[self.player.currentIndex][0].filename)
				self.player["coverArt"].onShow()
				self.player.init = 1
			else:
				self.player["nextTitle"].setText(self.player.getNextTitle())
				self.session.open(MessageBox, _("%s\nappended to songlist")%a.text, type = MessageBox.TYPE_INFO,timeout = 3 )

	def insertFileToSongList(self):
		if self.player is not None and self.player.songList:
			index = self.player.currentIndex
			filename = self["list"].getFilename()
			if filename.lower().endswith(".mp3") or filename.lower().endswith(".flac") or filename.lower().endswith(".m4a") or filename.lower().endswith(".ogg"):
				a = Item(text = filename, filename = os_path.join(self["list"].getCurrentDirectory(),filename))
				self.player.songList.insert(index+1,(a,))
				self.player.origSongList.insert(index+1,(a,))
				self.player["nextTitle"].setText(self.player.getNextTitle())
				self.session.open(MessageBox, _("%s\ninserted and will be played as next song")%a.text, type = MessageBox.TYPE_INFO,timeout = 3 )
		else:
			self.appendFileToSongList()

	def info_pressed(self):
		self.startMerlinPlayerScreenTimer.stop()
		if self.player is not None:
			if self.player.songList:
				self.session.execDialog(self.player)

	def moveright(self):
		self["list"].pageDown()
		self.lcdupdate()

	def moveleft(self):
		self["list"].pageUp()
		self.lcdupdate()
		
	def moveup(self):
		self["list"].up()
		self.lcdupdate()

	def movedown(self):
		self["list"].down()
		self.lcdupdate()

	def updateTarget(self):
		currFolder = self["list"].getCurrentDirectory()
		if currFolder is None:
			currFolder = _("Invalid Location")
		self["headertext"].setText(_("Filelist: %s") % currFolder)
		self.lcdupdate()

	def lcdupdate(self):
		self.startMerlinPlayerScreenTimer.start(START_MERLIN_PLAYER_SCREEN_TIMER_VALUE)
		index = self["list"].getSelectionIndex()
		sel = self["list"].list[index]
		text = sel[1][7]
		if sel[0][1] == True:
			text = "/" + text
		self.summaries.setText(text,1)
		# voheriges
		index -= 1
		if index < 0:
			index = len(self["list"].list) -1
		sel = self["list"].list[index]
		text = sel[1][7]
		if sel[0][1] == True:
			text = "/" + text
		self.summaries.setText(text,3)
		# naechstes
		index = self["list"].getSelectionIndex() + 1
		if index > (len(self["list"].list) -1):
			index = 0
		sel = self["list"].list[index]
		text = sel[1][7]
		if sel[0][1] == True:
			text = "/" + text
		self.summaries.setText(text,4)

	def __onClose(self):
		self.startMerlinPlayerScreenTimer.stop()
		if self.player is not None:
			self.player.closePlayer()
			self.player.doClose()
			self.player = None
		if self.serviceList is None:
			self.session.nav.playService(self.currentService, adjust=False)
		else:
			current = ServiceReference(self.serviceList.getCurrentSelection())
			self.session.nav.playService(current.ref, adjust=False)
		if config.plugins.merlinmusicplayer.rememberlastfilebrowserpath.value:
			try:
				config.plugins.merlinmusicplayer.defaultfilebrowserpath.value = self["list"].getCurrentDirectory()
				config.plugins.merlinmusicplayer.defaultfilebrowserpath.save()
			except:
				pass

	def createSummary(self):
		return MerlinMusicPlayerLCDScreenText

def main(session,**kwargs):
	servicelist = InfoBar.instance and InfoBar.instance.servicelist
	session.open(iDreamMerlin, servicelist)

def merlinmusicplayerfilelist(session,**kwargs):
	servicelist = InfoBar.instance and InfoBar.instance.servicelist
	session.open(MerlinMusicPlayerFileList, servicelist)

def menu_merlinmusicplayerfilelist(menuid, **kwargs):
	if menuid == "mainmenu" and config.plugins.merlinmusicplayer.merlinmusicplayermainmenu.value:
		return [(_("Merlin Music Player"), merlinmusicplayerfilelist, "merlin_music_player", 46)]
	return []

def menu_idream(menuid, **kwargs):
	if menuid == "mainmenu" and config.plugins.merlinmusicplayer.idreammainmenu.value:
		return [(_("iDream"), main, "idream", 47)]
	return []

def Plugins(**kwargs):
	list = [PluginDescriptor(name= _("iDream"), description=_("Receiver Music Database"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "iDream.png", fnc=main)]
	list.append(PluginDescriptor(name= _("Merlin Music Player"), description=_("Merlin music player"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "MerlinMusicPlayer.png", fnc=merlinmusicplayerfilelist))
	if config.plugins.merlinmusicplayer.idreamextendedpluginlist.value:
		list.append(PluginDescriptor(name= _("iDream"), description=_("Receiver Music Database"), where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main))
	if config.plugins.merlinmusicplayer.merlinmusicplayerextendedpluginlist.value:
		list.append(PluginDescriptor(name= _("Merlin Music Player"), description=_("Merlin music player"), where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=merlinmusicplayerfilelist))
	list.append(PluginDescriptor(name= _("Merlin Music Player"), description=_("Merlin music player"), where = [PluginDescriptor.WHERE_MENU], fnc=menu_merlinmusicplayerfilelist))
	list.append(PluginDescriptor(name= _("iDream"), description=_("Receiver Music Database"), where = [PluginDescriptor.WHERE_MENU], fnc=menu_idream))
	return list
