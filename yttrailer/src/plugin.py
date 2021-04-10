#  YTTrailer
#
#  Coded by Dr.Best (c) 2011
#  Support: www.dreambox-tools.info
#
#  All Files of this Software are licensed under the Creative Commons
#  Attribution-NonCommercial-ShareAlike 3.0 Unported
#  License if not stated otherwise in a Files Head. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.

#  Additionally, this plugin may only be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.

from __init__ import decrypt_block, validate_cert, read_random, rootkey, l2key
from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from Components.Sources.StaticText import StaticText
from Components.GUIComponent import GUIComponent
from enigma import eServiceReference,  RT_WRAP, RT_VALIGN_CENTER, RT_HALIGN_LEFT, gFont, eListbox, eListboxPythonMultiContent, eTPM

import gdata.youtube
import gdata.youtube.service
from socket import gaierror, error as sorcket_error
from urllib2 import Request, URLError, urlopen as urlopen2
from urllib import unquote_plus
from httplib import HTTPException
from urlparse import parse_qs

from Components.config import config, ConfigSubsection, ConfigSelection, getConfigListEntry, configfile, ConfigText, ConfigInteger, ConfigYesNo
from Components.ConfigList import ConfigListScreen

from Screens.InfoBarGenerics import InfoBarShowHide, InfoBarSeek, InfoBarAudioSelection, InfoBarNotifications, InfoBarServiceNotifications, InfoBarPVRState, InfoBarMoviePlayerSummarySupport
from Components.ServiceEventTracker import InfoBarBase

# for localized messages
from . import _

config.plugins.yttrailer = ConfigSubsection()
config.plugins.yttrailer.show_in_extensionsmenu = ConfigYesNo(default=False)
config.plugins.yttrailer.best_resolution = ConfigSelection(default="2", choices=[("0", _("1080p")),("1", _("720p")), ("2", _("No HD streaming"))])
config.plugins.yttrailer.ext_descr = ConfigText(default="german", fixed_size=False)
config.plugins.yttrailer.max_results =  ConfigInteger(5,limits=(1, 10))
config.plugins.yttrailer.close_player_with_exit =  ConfigYesNo(default=False)

from Screens.EventView import EventViewBase
baseEventViewBase__init__ = None

from Screens.EpgSelection import EPGSelection
baseEPGSelection__init__ = None
etpm = eTPM()


def autostart(reason, **kwargs):
	global l2key
	l2cert = etpm.getData(eTPM.DT_LEVEL2_CERT)
	if l2cert:
		l2key = validate_cert(l2cert, rootkey)
		if l2key:
			global baseEventViewBase__init__, baseEPGSelection__init__
			if baseEventViewBase__init__ is None:
				baseEventViewBase__init__ = EventViewBase.__init__
			EventViewBase.__init__ = EventViewBase__init__
			EventViewBase.showTrailer = showTrailer
			EventViewBase.showTrailerList = showTrailerList
			EventViewBase.showConfig = showConfig

			if baseEPGSelection__init__ is None:
				baseEPGSelection__init__ = EPGSelection.__init__
			EPGSelection.__init__ = EPGSelection__init__
			EPGSelection.showTrailer = showTrailer
			EPGSelection.showConfig = showConfig
			EPGSelection.showTrailerList = showTrailerList


def setup(session,**kwargs):
	session.open(YTTrailerSetup)

def Plugins(**kwargs):

	list = [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=autostart)]
	list.append(PluginDescriptor(name="YTTrailer Setup", description=_("YouTube-Trailer Setup"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=setup, icon="YTtrailer.png"))
	if config.plugins.yttrailer.show_in_extensionsmenu.value:
		list.append(PluginDescriptor(name="YTTrailer Setup", description=_("YouTube-Trailer Setup"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=setup, icon="YTtrailer.png"))
	return list

def EventViewBase__init__(self, Event, Ref, callback=None, similarEPGCB=None):
	baseEventViewBase__init__(self, Event, Ref, callback, similarEPGCB)
	self["trailerActions"] = ActionMap(["InfobarActions", "InfobarTeletextActions"],
	{
		"showTv": self.showTrailer,
		"showRadio": self.showTrailerList,
		"startTeletext": self.showConfig
	})


def EPGSelection__init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None, EPGtype=None):
	baseEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB, EPGtype)
	self["trailerActions"] = ActionMap(["InfobarActions", "InfobarTeletextActions"],
	{
		"showTv": self.showTrailer,
		"showRadio": self.showTrailerList,
		"startTeletext": self.showConfig
	})

def showConfig(self):
	self.session.open(YTTrailerSetup)

def showTrailer(self):
	eventname = ""
	if isinstance(self, EventViewBase):
		if self.event:
			eventname = self.event.getEventName()
	else:
		cur = self["list"].getCurrent()
		if cur and cur[0]:
			event = cur[0]
			eventname = event.getEventName()

	ytTrailer = YTTrailer(self.session)
	ytTrailer.showTrailer(eventname)

def showTrailerList(self):
	eventname = ""
	if isinstance(self, EventViewBase):
		if self.event:
			eventname = self.event.getEventName()
	else:
		cur = self["list"].getCurrent()
		if cur and cur[0]:
			event = cur[0]
			eventname = event.getEventName()

	self.session.open(YTTrailerList, eventname)

class YTTrailer:
	def __init__(self, session):
		self.session = session
		self.l3cert = etpm.getData(eTPM.DT_LEVEL3_CERT)

	def showTrailer(self, eventname):
		if eventname:
			feeds = self.getYTFeeds(eventname, 1)
			if feeds and len(feeds.entry) >= 1:
				ref = self.setServiceReference(feeds.entry[0])
				if ref:
					self.session.open(TrailerPlayer, ref)

	def getYTFeeds(self, eventname, max_results):
		yt_service = gdata.youtube.service.YouTubeService()
		# developer key and client id taken from mytube-plugin with permission from acid_burn.
		yt_service.developer_key = 'AI39si4AjyvU8GoJGncYzmqMCwelUnqjEMWTFCcUtK-VUzvWygvwPO-sadNwW5tNj9DDCHju3nnJEPvFy4WZZ6hzFYCx8rJ6Mw'
		yt_service.client_id = 'ytapi-dream-MyTubePlayer-i0kqrebg-0'
		query = gdata.youtube.service.YouTubeVideoQuery()
		if int(config.plugins.yttrailer.best_resolution.value) <= 1:
			shd = "HD"
		else:
			shd = ""
		query.vq = "%s %s Trailer %s" % (eventname, shd, config.plugins.yttrailer.ext_descr.value)
		query.max_results = max_results
		try:
			feeds = yt_service.YouTubeQuery(query)
		except gaierror:
			feeds = None
		return feeds

	def setServiceReference(self, entry):
		url = self.getVideoUrl(entry)
		if url:
			ref = eServiceReference(4097,0,url)
			ref.setName(entry.media.title.text)
		else:
			ref = None
		return ref

	def getTubeId(self, entry):
		ret = None
		if entry.media.player:
			split = entry.media.player.url.split("=")
			ret = split.pop()
			if ret.startswith('youtube_gdata'):
				tmpval=split.pop()
				if tmpval.endswith("&feature"):
					tmp = tmpval.split("&")
					ret = tmp.pop(0)
		return ret

	def getVideoUrl(self, entry):
		std_headers = {
			'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
			'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
			'Accept-Language': 'en-us,en;q=0.5',
		}

		VIDEO_FMT_PRIORITY_MAP = {
			'18': 4, #MP4 360p
			'35': 5, #FLV 480p
			'34': 6, #FLV 360p
		}

		if int(config.plugins.yttrailer.best_resolution.value) <= 1:
			VIDEO_FMT_PRIORITY_MAP["38"] = 1 #MP4 Original (HD)
			VIDEO_FMT_PRIORITY_MAP["22"] = 3 #MP4 720p (HD)

			if int(config.plugins.yttrailer.best_resolution.value) == 0:
				VIDEO_FMT_PRIORITY_MAP["37"] = 2 #MP4 1080p (HD)

		video_url = None
		video_id = str(self.getTubeId(entry))

		# Getting video webpage
		#URLs for YouTube video pages will change from the format http://www.youtube.com/watch?v=ylLzyHk54Z0 to http://www.youtube.com/watch#!v=ylLzyHk54Z0.
		watch_url = 'http://www.youtube.com/watch?v=%s&gl=US&hl=en' % video_id
		watchrequest = Request(watch_url, None, std_headers)
		try:
			print "[YTTrailer] trying to find out if a HD Stream is available",watch_url
			watchvideopage = urlopen2(watchrequest).read()
		except (URLError, HTTPException, socket_error), err:
			print "[YTTrailer] Error: Unable to retrieve watchpage - Error code: ", str(err)
			return video_url

		# Get video info
		for el in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
			info_url = ('http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (video_id, el))
			request = Request(info_url, None, std_headers)
			try:
				infopage = urlopen2(request).read()
				videoinfo = parse_qs(infopage)
				if ('url_encoded_fmt_stream_map' or 'fmt_url_map') in videoinfo:
					break
			except (URLError, HTTPException, socket_error), err:
				print "[YTTrailer] Error: unable to download video infopage",str(err)
				return video_url

		if ('url_encoded_fmt_stream_map' or 'fmt_url_map') not in videoinfo:
			# Attempt to see if YouTube has issued an error message
			if 'reason' not in videoinfo:
				print '[YTTrailer] Error: unable to extract "url_encoded_fmt_stream_map" or "fmt_url_map" parameter for unknown reason'
			else:
				reason = unquote_plus(videoinfo['reason'][0])
				print '[YTTrailer] Error: YouTube said: %s' % reason.decode('utf-8')
			return video_url

		video_fmt_map = {}
		fmt_infomap = {}

		if videoinfo.has_key('url_encoded_fmt_stream_map'):
			tmp_fmtUrlDATA = videoinfo['url_encoded_fmt_stream_map'][0].split(',')
		else:
			tmp_fmtUrlDATA = videoinfo['fmt_url_map'][0].split(',')
		for fmtstring in tmp_fmtUrlDATA:
			fmturl = fmtid = ""
			if videoinfo.has_key('url_encoded_fmt_stream_map'):
				try:
					for arg in fmtstring.split('&'):
						if arg.find('=') >= 0:
							print arg.split('=')
							key, value = arg.split('=')
							if key == 'itag':
								if len(value) > 3:
									value = value[:2]
								fmtid = value
							elif key == 'url':
								fmturl = value

					if fmtid != "" and fmturl != "" and VIDEO_FMT_PRIORITY_MAP.has_key(fmtid):
						video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = {'fmtid': fmtid, 'fmturl': unquote_plus(fmturl)}
						fmt_infomap[int(fmtid)] = "%s" %(unquote_plus(fmturl))
					fmturl = fmtid = ""

				except:
					print "error parsing fmtstring:",fmtstring

			else:
				(fmtid,fmturl) = fmtstring.split('|')
			if VIDEO_FMT_PRIORITY_MAP.has_key(fmtid) and fmtid != "":
				video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = {'fmtid': fmtid, 'fmturl': unquote_plus(fmturl)}
				fmt_infomap[int(fmtid)] = unquote_plus(fmturl)
		print "[YTTrailer] got",sorted(fmt_infomap.iterkeys())
		if video_fmt_map and len(video_fmt_map):
			if self.l3cert:
				l3key = validate_cert(self.l3cert, l2key)
				if l3key:
					rnd = read_random()
					val = etpm.computeSignature(rnd)
					result = decrypt_block(val, l3key)
					if result[80:88] == rnd:
						print "[YTTrailer] found best available video format:",video_fmt_map[sorted(video_fmt_map.iterkeys())[0]]['fmtid']
						best_video = video_fmt_map[sorted(video_fmt_map.iterkeys())[0]]
						video_url = "%s" %(best_video['fmturl'].split(';')[0])
						print "[YTTrailer] found best available video url:",video_url

		return video_url

class YTTrailerList(Screen, YTTrailer):

	skin = """
		<screen name="YTTrailerList" position="center,center" size="580,436" title="YT Trailer-List" backgroundColor="#ff000000">
			<widget name="list" position="0,0" size="580,436" />
		</screen>"""

	def __init__(self, session, eventname):
		Screen.__init__(self, session)
		YTTrailer.__init__(self, session)

		self["actions"] = ActionMap(["WizardActions"],
		{
			"ok": self.okPressed,
			"back": self.close
		}, -1)

		self.eventName = eventname
		self["list"] = TrailerList()
		self.onLayoutFinish.append(self.startRun)


	def startRun(self):
		feeds = self.getYTFeeds(self.eventName, config.plugins.yttrailer.max_results.value)
		if feeds is not None:
			entryList = []
			for entry in feeds.entry:
				entryList.append(((entry),))
			self["list"].setList(entryList)

	def okPressed(self):
		entry = self["list"].getCurrent()
		if entry:
			ref = self.setServiceReference(entry)
			if ref:
				self.session.open(TrailerPlayer, ref)

class TrailerList(GUIComponent, object):

	GUI_WIDGET = eListbox

	def __init__(self):
		GUIComponent.__init__(self)
		self.l = eListboxPythonMultiContent()
		self.l.setBuildFunc(self.buildList)
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setItemHeight(75)

	def buildList(self, entry):
		width = self.l.getItemSize().width()
		res = [None]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, 24, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, entry.media.title.text))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 28, width, 40, 1, RT_WRAP, entry.media.description.text))
		return res

	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		self.instance.setWrapAround(True)

	def preWidgetRemove(self, instance):
		instance.setContent(None)

	def setList(self, list):
		self.l.setList(list)

class TrailerPlayer(InfoBarBase, InfoBarShowHide, InfoBarSeek, InfoBarAudioSelection, InfoBarNotifications, InfoBarServiceNotifications, InfoBarPVRState, InfoBarMoviePlayerSummarySupport, Screen):

	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, ref):
		Screen.__init__(self, session)
		self.session = session
		self["actions"] = HelpableActionMap(self, "MoviePlayerActions",
			{
				"leavePlayer": (self.leavePlayer, _("leave movie player..."))
			})

		if config.plugins.yttrailer.close_player_with_exit.value:
			self["closeactions"] = HelpableActionMap(self, "WizardActions",
				{
					"back": (self.close, _("leave movie player..."))
				})


		self.allowPiP = False
		for x in InfoBarShowHide, InfoBarBase, InfoBarSeek, \
				InfoBarAudioSelection, InfoBarNotifications, \
				InfoBarServiceNotifications, InfoBarPVRState,  \
				InfoBarMoviePlayerSummarySupport:
			x.__init__(self)

		self.returning = False
		self.skinName = "MoviePlayer"
		self.lastservice = session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.playService(ref)
		self.onClose.append(self.__onClose)

	def leavePlayer(self):
		self.close()

	def doEofInternal(self, playing):
		self.close()

	def __onClose(self):
		self.session.nav.playService(self.lastservice)

class YTTrailerSetup(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="560,400" title="YT-Trailer Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="20,50" size="520,330" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))

		cfglist = []
		cfglist.append(getConfigListEntry(_("Show Setup in Extensions menu"), config.plugins.yttrailer.show_in_extensionsmenu))
		cfglist.append(getConfigListEntry(_("Extended search filter"), config.plugins.yttrailer.ext_descr))
		cfglist.append(getConfigListEntry(_("Best resolution"), config.plugins.yttrailer.best_resolution))
		cfglist.append(getConfigListEntry(_("Max. results in list-mode"), config.plugins.yttrailer.max_results))
		cfglist.append(getConfigListEntry(_("Close Player with exit-key"), config.plugins.yttrailer.close_player_with_exit))


		ConfigListScreen.__init__(self, cfglist, session)
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyClose
		}, -2)

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		self.close()

	def keyClose(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()
