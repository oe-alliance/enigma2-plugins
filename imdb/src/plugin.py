# -*- coding: UTF-8 -*-
# for localized messages
from . import _

from Plugins.Plugin import PluginDescriptor
from Tools.Downloader import downloadWithProgress
from enigma import ePicLoad, eServiceReference, eServiceCenter
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.EpgSelection import EPGSelection
from Screens.ChannelSelection import SimpleChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.AVSwitch import AVSwitch
from Components.MenuList import MenuList
from Components.Language import language
from Components.ProgressBar import ProgressBar
from Components.Sources.StaticText import StaticText
from Components.Sources.Boolean import Boolean
from Components.MovieList import KNOWN_EXTENSIONS
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
import os, re
try:
	import htmlentitydefs
	from urllib import quote_plus
	iteritems = lambda d: d.iteritems()
except ImportError as ie:
	from html import entities as htmlentitydefs
	from urllib.parse import quote_plus
	iteritems = lambda d: d.items()
	unichr = chr
import os, gettext

# Configuration
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigYesNo, ConfigText
from Components.ConfigList import ConfigListScreen
from Components.PluginComponent import plugins
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from HTMLParser import HTMLParser

def transHTML(text):
	h = HTMLParser()
	return h.unescape(text)

config.plugins.imdb = ConfigSubsection()
config.plugins.imdb.showinplugins = ConfigYesNo(default = False)
config.plugins.imdb.showsetupinplugins = ConfigYesNo(default = True)
config.plugins.imdb.showinmovielist = ConfigYesNo(default = True)
config.plugins.imdb.force_english = ConfigYesNo(default=False)
config.plugins.imdb.ignore_tags = ConfigText(visible_width = 50, fixed_size = False)
config.plugins.imdb.showlongmenuinfo = ConfigYesNo(default = False)
config.plugins.imdb.showepisodeinfo = ConfigYesNo(default = False)

def quoteEventName(eventName, safe="/()" + ''.join(map(chr,range(192,255)))):
	# BBC uses '\x86' markers in program names, remove them
	try:
		text = eventName.decode('utf8').replace(u'\x86', u'').replace(u'\x87', u'').encode('utf8')
	except:
		text = eventName
	# IMDb doesn't seem to like urlencoded characters at all, hence the big "safe" list
	return quote_plus(text, safe=safe)

class IMDBChannelSelection(SimpleChannelSelection):
	def __init__(self, session):
		SimpleChannelSelection.__init__(self, session, _("Channel Selection"))
		self.skinName = "SimpleChannelSelection"

		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"],
			{
				"showEPGList": self.channelSelected
			}
		)

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.enterPath(ref)
		elif not (ref.flags & eServiceReference.isMarker):
			info = eServiceCenter.getInstance().info(ref)
			evt = info and info.getEvent(ref, -1)
			event_id = evt and evt.getEventId() or None
			self.session.openWithCallback(
				self.epgClosed,
				IMDBEPGSelection,
				ref,
				eventid=event_id,
				openPlugin = False
			)

	def epgClosed(self, ret = None):
		if ret:
			self.close(ret)

class IMDBEPGSelection(EPGSelection):
	def __init__(self, session, ref, eventid=None, openPlugin = True):
		EPGSelection.__init__(self, session, ref.toString(), eventid=eventid)
		self.skinName = "EPGSelection"
		self["key_green"].setText(_("Lookup"))
		self.openPlugin = openPlugin

	def infoKeyPressed(self):
		self.greenButtonPressed()

	def timerAdd(self):
		self.greenButtonPressed()

	def greenButtonPressed(self):
		self.closeEventViewDialog()
		from Screens.InfoBar import InfoBar
		InfoBarInstance = InfoBar.instance
		if not InfoBarInstance.LongButtonPressed:
			cur = self["list"].getCurrent()
			evt = cur[0]
			sref = cur[1]
			if not evt:
				return

			if self.openPlugin:
				self.session.open(
					IMDB,
					evt.getEventName()
				)
			else:
				self.close(evt.getEventName())

	def onSelectionChanged(self):
		super(IMDBEPGSelection, self).onSelectionChanged()
		self["key_green"].setText(_("Lookup"))

class IMDB(Screen, HelpableScreen):
	skin = """
		<screen name="IMDB" position="center,center" size="600,420" title="Internet Movie Database Details Plugin" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/key_menu.png" position="565,5" zPosition="0" size="35,25" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#9f1313" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#a08500" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#18188b" transparent="1" />
			<widget source="title" render="Label" position="10,40" size="330,45" valign="center" font="Regular;22"/>
			<widget name="detailslabel" position="105,90" size="485,140" font="Regular;18" />
			<widget name="castlabel" position="10,235" size="580,155" font="Regular;18" />
			<widget name="extralabel" position="10,40" size="580,350" font="Regular;18" />
			<widget name="ratinglabel" position="340,62" size="250,20" halign="center" font="Regular;18" foregroundColor="#f0b400"/>
			<widget name="statusbar" position="10,404" size="580,16" font="Regular;16" foregroundColor="#cccccc" />
			<widget name="poster" position="4,90" size="96,140" alphatest="on" />
			<widget name="menu" position="10,115" size="580,275" zPosition="3" scrollbarMode="showOnDemand" />
			<widget name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IMDb/starsbar_empty.png" position="340,40" zPosition="0" size="210,21" transparent="1" alphatest="on" />
			<widget name="stars" position="340,40" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IMDb/starsbar_filled.png" transparent="1" />
		</screen>"""

	# Some HTML entities as utf-8
	NBSP = unichr(htmlentitydefs.name2codepoint['nbsp']).encode("utf8")
	RAQUO = unichr(htmlentitydefs.name2codepoint['raquo']).encode("utf8")
	HELLIP = unichr(htmlentitydefs.name2codepoint['hellip']).encode("utf8")

	def __init__(self, session, eventName, callbackNeeded=False, save=False, savepath=None, localpath=None):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		for tag in config.plugins.imdb.ignore_tags.getValue().split(','):
			eventName = eventName.replace(tag,'')

		eventName = ' '.join(eventName.split()).strip()

		self.eventName = eventName

		self.callbackNeeded = callbackNeeded
		self.callbackData = ""
		self.callbackGenre = ""

		self.saving = save
		self.savingpath = savepath
		self.localpath = localpath
		self.fetchurl = None

		self.dictionary_init()

		self["poster"] = Pixmap()
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintPosterPixmapCB)

		self["stars"] = ProgressBar()
		self["starsbg"] = Pixmap()
		self["stars"].hide()
		self["starsbg"].hide()
		self.ratingstars = -1

		self["title"] = StaticText(_("The Internet Movie Database"))
		# map new source -> old component
		def setText(txt):
			StaticText.setText(self["title"], txt)
			self["titellabel"].setText(txt)
		self["title"].setText = setText
		self["titellabel"] = Label()
		self["detailslabel"] = ScrollLabel("")
		self["castlabel"] = ScrollLabel("")
		self["extralabel"] = ScrollLabel("")
		self["statusbar"] = Label("")
		self["ratinglabel"] = Label("")
		self.resultlist = []
		self["menu"] = MenuList(self.resultlist)
		self["menu"].hide()

		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		# 0 = multiple query selection menu page
		# 1 = movie info page
		# 2 = extra infos page
		self.Page = 0

		self["actionsOk"] = HelpableActionMap(self, "OkCancelActions",
		{
			"ok": (self.showDetails, _("Show movie and series basic details")),
			"cancel": (self.exit, _("Exit IMDb search")),
		}, -1)
		self["actionsColor"] = HelpableActionMap(self, "ColorActions",
		{
			"red": (self.exit, _("Exit IMDb search")),
			"green": (self.showMenu, _("Show list of matched movies an series")),
			"yellow": (self.showDetails, _("Show movie and series basic details")),
			"blue": (self.showExtras, _("Show movie and series extra details")),
		}, -1)
		self["actionsMovieSel"] = HelpableActionMap(self, "MovieSelectionActions",
		{
			"contextMenu": (self.contextMenuPressed, _("Menu")),
			"showEventInfo": (self.showDetails, _("Show movie and series basic details")),
		}, -1)
		self["actionsDir"] = HelpableActionMap(self, "DirectionActions",
		{
			"down": (self.pageDown, _("Page down")),
			"up": (self.pageUp, _("Page up")),
		}, -1)

		self.getIMDB()

		if self.localpath is not None:                                # otherwise the stars are not correctly shown if we call details directly
			self.onLayoutFinish.append(self._layoutFinished)

	def _layoutFinished(self):
		self["menu"].hide()
		self["extralabel"].hide()
		self["stars"].setValue(self.ratingstars)

	def exit(self):
		if fileExists("/tmp/poster.jpg"):
			os.remove("/tmp/poster.jpg")
		if fileExists("/tmp/imdbquery.html"):
			os.remove("/tmp/imdbquery.html")
		if fileExists("/tmp/imdbquery2.html"):
			os.remove("/tmp/imdbquery2.html")
		if self.callbackNeeded:
			self.close([self.callbackData, self.callbackGenre])
		else:
			self.close()


	def dictionary_init(self):
		syslang = language.getLanguage()
		if 1: #"de" not in syslang or config.plugins.imdb.force_english.value is True:
			self.generalinfomask = re.compile(
			'<h1 class="".*?>(?P<title>.*?)<.*?/h1>*'
			'(?:.*?<h4 class="inline">\s*(?P<g_director>Regisseur|Directors?):\s*</h4>(?P<director>.*?)</div>)?'
			'(?:.*?<h4 class="inline">\s*(?P<g_creator>Sch\S*?pfer|Creators?):\s*</h4>\s*(?P<creator>.*?)</div>)?'
			'(?:.*?<h4 class="float-left">\s*(?P<g_seasons>Seasons?)\s*</h4>.*?<a .*?>(?P<seasons>.*?)</div>)?'
			'(?:.*?<h4 class="inline">\s*(?P<g_writer>Drehbuch|Writers?):\s*</h4>(?P<writer>.*?)</div>)?'
			'(?:.*?<h4 class="inline">\s*(?P<g_country>Land|Country):\s*</h4>.*?(?P<country>.*?)</div>)?'
			'(?:.*?<h4 class="inline">\s*(?P<g_premiere>Premiere|Release Date).*?</h4>\s+(?P<premiere>.*?)\s*<span)?'
			'(?:.*?<h4 class="inline">\s*(?P<g_alternativ>Auch bekannt als|Also Known As):\s*</h4>\s*(?P<alternativ>.*?)\s*<span)?'
			, re.DOTALL)

			self.awardsmask = re.compile('<span itemprop="awards">\s*(?:<b>)?\s*(?P<awards>.+?)\s*(?:</b>)?\s*</span>', re.DOTALL)

			self.extrainfomask = re.compile(
			'(?:.*?<div class="summary_text">(?P<outline>.+?)</div>)?'
			'(?:.*?<h2>(?P<g_synopsis>Storyline)</h2>.*?<span>(?P<synopsis>.+?)</span>)?'
			'(?:.*?<h4 class="inline">(?P<g_keywords>Plot Keywords):</h4>(?P<keywords>.+?)(?:(?:Mehr|See All) \(\d+\)</a>|</div>))?'
			'(?:.*?<h4 class="inline">(?P<g_tagline>Werbezeile|Taglines?):</h4>\s*(?P<tagline>.+?)<)?'
			'(?:.*?<h4 class="inline">(?P<g_cert>Altersfreigabe|Certificate):</h4>\s*<span itemprop="contentRating">(?P<cert>.+?)</span>)?'
			'(?:.*?<h4>(?P<g_trivia>Dies und das|Trivia)</h4>\s*(?P<trivia>.+?)(?:Mehr|See more</a>|</div>))*'
			'(?:.*?<h4>(?P<g_goofs>Pannen|Goofs)</h4>\s*(?P<goofs>.+?)(?:Mehr|See more</a>|</div>))*'
			'(?:.*?<h4>(?P<g_quotes>Dialogzitate|Quotes)</h4>\s*(?P<quotes>.+?)(?:Mehr|See more</a>|</div>))?'
			'(?:.*?<h4>(?P<g_connections>Bez\S*?ge zu anderen Titeln|Connections)</h4>\s*(?P<connections>.+?)(?:Mehr|See more</a>|</div>))?'
			'(?:.*?<h2>(?P<g_comments>Nutzerkommentare|User Reviews)</h2>.*?<strong>(?P<commenttitle>.*?)</strong>.*?<div class="comment-meta">(?P<commenter>.+?)</span></a>.*?<p.*?>(?P<comment>.+?)</p>)?'
			'(?:.*?<h4 class="inline">(?P<g_language>Sprache|Language):</h4>\s*(?P<language>.+?)</div>)?'
			'(?:.*?<h4 class="inline">(?P<g_locations>Drehorte|Filming Locations):</h4>.*?<a.*?>(?P<locations>.+?)</a>)?'
			'(?:.*?<h4 class="inline">(?P<g_company>Firma|Production Co):</h4>\s*(?P<company>.+?)(?:Mehr|See more</a>|</div>))?'
			'(?:.*?<h4 class="inline">(?P<g_runtime>L\S*?nge|Runtime):</h4>\s*(?P<runtime>.+?)</div>)?'
			'(?:.*?<h4 class="inline">(?P<g_sound>Tonverfahren|Sound Mix):</h4>\s*(?P<sound>.+?)</div>)?'
			'(?:.*?<h4 class="inline">(?P<g_color>Farbe|Color):</h4>\s*(?P<color>.+?)</div>)?'
			'(?:.*?<h4 class="inline">(?P<g_aspect>Seitenverh\S*?ltnis|Aspect Ratio):</h4>\s*(?P<aspect>.+?)(?:Mehr|See more</a>|</div>))?'
			, re.DOTALL)

			self.genreblockmask = re.compile('<h4 class="inline">Genres?:</h4>\s*?(.*?)\s+?(?:Mehr|See more|</p|<a class|</div>)', re.DOTALL)
			self.ratingmask = re.compile('<div class="ratingValue">.*?<span itemprop="ratingValue">(?P<rating>.*?)</span>', re.DOTALL)
			self.castmask = re.compile('<td>\s*<a href=.*?>(?P<actor>.*?)\s*</a>\s*</td>.*?<td class="character">(?P<character>.*?)(?:<a href="#"\s+class="toggle-episodes".*?>(?P<episodes>.*?)</a>.*?)?</td>', re.DOTALL)
			#self.postermask = re.compile('<td .*?id="img_primary">.*?<img .*?src=\"(http.*?)\"', re.DOTALL)
			self.postermask = re.compile('<div class="poster">.*?<img .*?src=\"(http.*?)\"', re.DOTALL)

		self.htmltags = re.compile('<.*?>', re.DOTALL)

	def resetLabels(self):
		self["detailslabel"].setText("")
		self["ratinglabel"].setText("")
		self["title"].setText("")
		self["castlabel"].setText("")
		self["titellabel"].setText("")
		self["extralabel"].setText("")
		self.ratingstars = -1

	def pageUp(self):
		if self.Page == 0:
			self["menu"].instance.moveSelection(self["menu"].instance.moveUp)
		if self.Page == 1:
			self["castlabel"].pageUp()
			self["detailslabel"].pageUp()
		if self.Page == 2:
			self["extralabel"].pageUp()

	def pageDown(self):
		if self.Page == 0:
			self["menu"].instance.moveSelection(self["menu"].instance.moveDown)
		if self.Page == 1:
			self["castlabel"].pageDown()
			self["detailslabel"].pageDown()
		if self.Page == 2:
			self["extralabel"].pageDown()

	def showMenu(self):
		if ( self.Page is 1 or self.Page is 2 ) and self.resultlist:
			self["menu"].show()
			self["stars"].hide()
			self["starsbg"].hide()
			self["ratinglabel"].hide()
			self["castlabel"].hide()
			self["poster"].hide()
			self["extralabel"].hide()
			self["title"].setText(_("Ambiguous results"))
			self["detailslabel"].setText(_("Please select the matching entry"))
			self["detailslabel"].show()
			self["key_blue"].setText("")
			self["key_green"].setText(_("Title Menu"))
			self["key_yellow"].setText(_("Details"))
			self.Page = 0

	def getLocalDetails(self):
		localfile = self.localpath
		self.html2utf8(open(localfile, "r").read())
		self.generalinfos = self.generalinfomask.search(self.inhtml)
		self.IMDBparse()
		if self.ratingstars > 0:
			self["starsbg"].show()
			self["stars"].show()
		self.Page = 1

	def showDetails(self):
		self["ratinglabel"].show()
		self["castlabel"].show()
		self["detailslabel"].show()

		if self.resultlist and self.Page == 0:
			link = self["menu"].getCurrent()[1]
			title = self["menu"].getCurrent()[0]
			self["statusbar"].setText(_("Re-Query IMDb: %s...") % (title))
			localfile = "/tmp/imdbquery2.html"
			fetchurl = "http://imdb.com/title/" + link
			print("[IMDB] showDetails() downloading query " + fetchurl + " to " + localfile)
			download = downloadWithProgress(fetchurl,localfile)
			download.start().addCallback(self.IMDBquery2).addErrback(self.http_failed)
			self.fetchurl = fetchurl
			self["menu"].hide()
			self.resetLabels()
			self.Page = 1

		if self.Page == 2:
			self["extralabel"].hide()
			self["poster"].show()
			if self.ratingstars > 0:
				self["starsbg"].show()
				self["stars"].show()
				self["stars"].setValue(self.ratingstars)

			self.Page = 1

	def showExtras(self):
		if self.Page == 1:
			self["extralabel"].show()
			self["detailslabel"].hide()
			self["castlabel"].hide()
			self["poster"].hide()
			self["stars"].hide()
			self["starsbg"].hide()
			self["ratinglabel"].hide()
			self.Page = 2

	def contextMenuPressed(self):
		list = [
			(_("Enter search"), self.openVirtualKeyBoard),
			(_("Select from EPG"), self.openChannelSelection),
			(_("Setup"), self.setup),
		]

		if self.saving:
			if self.savingpath is not None:
				# TODO: save Poster also as option for .html
				list.extend((
					(_("Save current Details as .html for offline use"), self.saveHtmlDetails),
					(_("Save current Details as .txt"), self.saveTxtDetails),
					(_("Save current Poster and Details as .txt"), self.savePosterTxtDetails),
				))

		if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/YTTrailer/plugin.py")):
			list.extend((
				(_("Play Trailer"), self.openYttrailer),
				(_("Search Trailer"), self.searchYttrailer),
			))

		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			title=_("IMDb Menu"),
			list = list,
		)

	def menuCallback(self, ret = None):
		ret and ret[1]()

	def saveHtmlDetails(self):
		try:
			if self.savingpath is not None:
				isave = self.savingpath + ".imdbquery2.html"
				if self.fetchurl is not None:
					download = downloadWithProgress(self.fetchurl,isave)
					download.start().addCallback(self.IMDBsave).addErrback(self.http_failed)
		except Exception, e:
			print('[IMDb] saveHtmlDetails exception failure: ', str(e))

	def saveTxtDetails(self):
		try:
			if self.savingpath is not None:
				getTXT = self.IMDBsavetxt()
				if getTXT is not None:
					file(self.savingpath + ".txt",'w').write(getTXT)
				else:
					from Screens.MessageBox import MessageBox
					self.session.open(MessageBox, (_('IMDb can not get Movie Information to write to .txt file!')), MessageBox.TYPE_INFO, 10)
		except Exception, e:
			print('[IMDb] saveTxtDetails exception failure: ', str(e))

	def savePosterTxtDetails(self):
		try:
			if self.savingpath is not None:
				getTXT = self.IMDBsavetxt(True)
				if getTXT is not None:
					file(self.savingpath + ".txt",'w').write(getTXT)
				else:
					from Screens.MessageBox import MessageBox
					self.session.open(MessageBox, (_('IMDb can not get Movie Information to write to .jpg and .txt files!')), MessageBox.TYPE_INFO, 10)
		except Exception, e:
			print('[IMDb] savePosterTxtDetails exception failure: ', str(e))

	def IMDBsave(self,string):
		self["statusbar"].setText(_("IMDb Save - Download completed"))
		self.html2utf8(open("/tmp/imdbquery2.html", "r").read())
		self.generalinfos = self.generalinfomask.search(self.inhtml)
		self.IMDBparse()

	def IMDBsavetxt(self, poster=False):
		overview = ""
		runtime = ""
		genre = ""
		country = ""
		release = ""
		rating = ""

		if self.generalinfos:
			extrainfos = self.extrainfomask.search(self.inhtml)
			if extrainfos:
				# get entry 1 = Overview(details)
				try:
					text = ' '.join(self.htmltags.sub('',extrainfos.group("synopsis").replace("\n",' ').replace("<br>", '\n').replace("<br />",'\n')).replace(' |' + self.NBSP, '').replace(self.NBSP, ' ').split()) + "\n"
					overview = _("Content:") + " " + text
				except Exception, e:
					print('[IMDb] IMDBsavetxt exception failure in get overview: ', str(e))
					overview = (_("Content:"))
#				print'[IMDb] IMDBsavetxt overview: ', overview

				# get entry 2 = Runtime
				try:
					time = ' '.join(self.htmltags.sub('',extrainfos.group(category).replace("\n",' ').replace("<br>", '\n').replace("<br />",'\n')).replace(' |' + self.NBSP, '').replace(self.NBSP, ' ').split())
					runtime = _("Runtime:") + " " + time
				except Exception, e:
					print('[IMDb] IMDBsavetxt exception failure in get runtime: ', str(e))
					runtime = (_("Runtime:"))
#				print'[IMDb] IMDBsavetxt runtime: ', runtime

			# get entry 3 = Genre
			genreblock = self.genreblockmask.search(self.inhtml)
			if genreblock:
				genres = ' '.join(self.htmltags.sub('', genreblock.group(0)).replace(self.NBSP, ' ').split())
				if genres:
					genre = _("Genre:") + " " + genres
			else:
				genre = (_("Genre:"))
#			print'[IMDb] IMDBsavetxt genre: ', genre

			# get entry 4 = Country
			try:
				land = ' '.join(self.htmltags.sub('', self.generalinfos.group("country").replace('\n',' ')).split())
				country = _("Production Countries:") + " " + land
			except Exception, e:
				print('[IMDb] IMDBsavetxt exception failure in get country: ', str(e))
				country = (_("Production Countries:"))
#			print'[IMDb] IMDBsavetxt country: ', country

			# get entry 5 = ReleaseDate
			try:
				date = ' '.join(self.htmltags.sub('', self.generalinfos.group("premiere").replace('\n',' ')).split())
				release = _("Release Date:") + " " + date
			except Exception, e:
				print('[IMDb] IMDBsavetxt exception failure in get release: ', str(e))
				release = (_("Release Date:"))
#			print'[IMDb] IMDBsavetxt release: ', release

			# get entry 5 = Vote
			ratingtext = self.ratingmask.search(self.inhtml)
			if ratingtext:
				ratingtext = ratingtext.group("rating")
				if ratingtext != '<span id="voteuser"></span>':
					text = ratingtext                                # + " / 10"
					rating = _("User Rating") + ": " + text
			else:
				rating = (_("User Rating") + ": ")
#			print'[IMDb] IMDBsavetxt rating: ', rating

			# get the poster.jpg
			if poster:
				try:
					posterurl = self.postermask.search(self.inhtml)
					if posterurl and posterurl.group(1).find("jpg") > 0:
						posterurl = posterurl.group(1)
						postersave = self.savingpath + ".poster.jpg"
						print("[IMDB] downloading poster " + posterurl + " to " + postersave)
						download = downloadWithProgress(posterurl,postersave)
						download.start().addErrback(self.http_failed)
				except Exception, e:
					print('[IMDb] IMDBsavetxt exception failure in get poster: ', str(e))

		return overview + "\n\n" + runtime + "\n" + genre + "\n" + country + "\n" + release + "\n" + rating + "\n"

	def openYttrailer(self):
		try:
			from Plugins.Extensions.YTTrailer.plugin import YTTrailer, baseEPGSelection__init__
		except ImportError as ie:
			pass
		if baseEPGSelection__init__ is None:
			return

		ytTrailer = YTTrailer(self.session)
		ytTrailer.showTrailer(self.eventName)

	def searchYttrailer(self):
		try:
			from Plugins.Extensions.YTTrailer.plugin import YTTrailerList, baseEPGSelection__init__
		except ImportError as ie:
			pass
		if baseEPGSelection__init__ is None:
			return

		self.session.open(YTTrailerList, self.eventName)

	def openVirtualKeyBoard(self):
		self.session.openWithCallback(
			self.gotSearchString,
			VirtualKeyBoard,
			title = _("Enter text to search for"),
			text = self.eventName
		)

	def openChannelSelection(self):
		self.session.openWithCallback(
			self.gotSearchString,
			IMDBChannelSelection
		)

	def gotSearchString(self, ret = None):
		if ret:
			self.eventName = ret
			self.Page = 0
			self.resultlist = []
			self["menu"].hide()
			self["ratinglabel"].show()
			self["castlabel"].show()
			self["detailslabel"].show()
			self["poster"].hide()
			self["stars"].hide()
			self["starsbg"].hide()
			self.getIMDB(search=True)

	def getIMDB(self, search=False):
		self.resetLabels()
		if not isinstance(self.eventName, basestring):
			self["statusbar"].setText("")
			return
		if not self.eventName:
			s = self.session.nav.getCurrentService()
			info = s and s.info()
			event = info and info.getEvent(0) # 0 = now, 1 = next
			if event:
				self.eventName = event.getEventName()
			else:
				self.eventName = self.session.nav.getCurrentlyPlayingServiceReference().toString()
				self.eventName = self.eventName.split('/')
				self.eventName = self.eventName[-1]
				self.eventName = self.eventName.replace('.',' ')
				self.eventName = self.eventName.split('-')
				self.eventName = self.eventName[0]
				if self.eventName.endswith(' '):
					self.eventName = self.eventName[:-1]

		if self.localpath is not None and not search:
			if os.path.exists(self.localpath):
				self.getLocalDetails()

		else:
			if self.eventName:
				self["statusbar"].setText(_("Query IMDb: %s") % (self.eventName))
				localfile = "/tmp/imdbquery.html"
				fetchurl = "http://imdb.com/find?q=" + quoteEventName(self.eventName) + "&s=tt&site=aka"
				#print("[IMDB] getIMDB() Downloading Query " + fetchurl + " to " + localfile)
				download = downloadWithProgress(fetchurl,localfile)
				download.start().addCallback(self.IMDBquery).addErrback(self.http_failed)

			else:
				self["statusbar"].setText(_("Could't get event name"))

	def html2utf8(self,in_html):
		in_html = (re.subn(r'<(script).*?</\1>(?s)', '', in_html)[0])
		in_html = (re.subn(r'<(style).*?</\1>(?s)', '', in_html)[0])
		entitydict = {}

		entities = re.finditer('&([:_A-Za-z][:_\-.A-Za-z"0-9]*);', in_html)
		for x in entities:
			key = x.group(0)
			if key not in entitydict:
				entitydict[key] = htmlentitydefs.name2codepoint[x.group(1)]

		entities = re.finditer('&#x([0-9A-Fa-f]+);', in_html)
		for x in entities:
			key = x.group(0)
			if key not in entitydict:
				entitydict[key] = "%d" % int(x.group(1), 16)

		entities = re.finditer('&#(\d+);', in_html)
		for x in entities:
			key = x.group(0)
			if key not in entitydict:
				entitydict[key] = x.group(1)

		if 'charset="utf-8"' in in_html or 'charset=utf-8' in in_html:
			for key, codepoint in iteritems(entitydict):
				in_html = in_html.replace(key, unichr(int(codepoint)).encode('utf8'))
			self.inhtml = in_html
			return

		for key, codepoint in iteritems(entitydict):
			in_html = in_html.replace(key, unichr(int(codepoint)).encode('latin-1', 'ignore'))
		self.inhtml = in_html.decode('latin-1').encode('utf8')

	def IMDBquery(self,string):
		self["statusbar"].setText(_("IMDb Download completed"))

		self.html2utf8(open("/tmp/imdbquery.html", "r").read())

		self.generalinfos = self.generalinfomask.search(self.inhtml)

		if self.generalinfos:
			self.IMDBparse()
		else:
			if re.search("<title>Find - IMDb</title>", self.inhtml):
				pos = self.inhtml.find('<table class="findList">')
				pos2 = self.inhtml.find("</table>",pos)
				findlist = self.inhtml[pos:pos2]
				searchresultmask = re.compile('<tr class="findResult (?:odd|even)">.*?<td class="result_text"> (<a href="/title/(tt\d{7,7})/.*?"\s?>(.*?)</a>.*?)</td>', re.DOTALL)
				searchresults = searchresultmask.finditer(findlist)
				titlegroup = 1 if config.plugins.imdb.showlongmenuinfo.value else 3
				self.resultlist = [(' '.join(self.htmltags.sub('',x.group(titlegroup)).replace(self.NBSP," ").split()), x.group(2)) for x in searchresults]
				Len = len(self.resultlist)
				self["menu"].l.setList(self.resultlist)
				if Len == 1:
					self["statusbar"].setText(_("Re-Query IMDb: %s...") % (self.resultlist[0][0],))
					self.eventName = self.resultlist[0][1]
					localfile = "/tmp/imdbquery.html"
					fetchurl = "http://imdb.com/find?q=" + quoteEventName(self.eventName) + "&s=tt&site=aka"
					download = downloadWithProgress(fetchurl,localfile)
					download.start().addCallback(self.IMDBquery).addErrback(self.http_failed)
				elif Len > 1:
					self.Page = 1
					self.showMenu()
				else:
					self["detailslabel"].setText(_("No IMDb match."))
					self["statusbar"].setText(_("No IMDb match:") + ' ' + self.eventName)
			else:
				splitpos = self.eventName.find('(')
				if splitpos > 0 and self.eventName.endswith(')'):
					self.eventName = self.eventName[splitpos+1:-1]
					self["statusbar"].setText(_("Re-Query IMDb: %s...") % (self.eventName))
					# event_quoted = quoteEventName(self.eventName)
					localfile = "/tmp/imdbquery.html"
					fetchurl = "http://imdb.com/find?q=" + quoteEventName(self.eventName) + "&s=tt&site=aka"
					download = downloadWithProgress(fetchurl,localfile)
					download.start().addCallback(self.IMDBquery).addErrback(self.http_failed)
				else:
					self["detailslabel"].setText(_("IMDb query failed!"))

	def http_failed(self, failure_instance=None, error_message=""):
		text = _("IMDb Download failed")
		if error_message == "" and failure_instance is not None:
			error_message = failure_instance.getErrorMessage()
			text += ": " + error_message
		print("[IMDB] ",text)
		self["statusbar"].setText(text)

	def IMDBquery2(self,string):
		self["statusbar"].setText(_("IMDb Re-Download completed"))
		self.html2utf8(open("/tmp/imdbquery2.html", "r").read())
		self.generalinfos = self.generalinfomask.search(self.inhtml)
		self.IMDBparse()

	def IMDBparse(self):
		self.Page = 1
		Detailstext = _("No details found.")
		if self.generalinfos:
			self["key_yellow"].setText(_("Details"))
			self["statusbar"].setText(_("IMDb Details parsed"))
			Titeltext = self.generalinfos.group("title").replace(self.NBSP, ' ').strip()
			if len(Titeltext) > 57:
				Titeltext = Titeltext[0:54] + "..."
			self["title"].setText(Titeltext)

			Detailstext = ""
			addnewline = ''

			genreblock = self.genreblockmask.search(self.inhtml)
			if genreblock:
				genres = ' '.join(self.htmltags.sub('', genreblock.group(0)).replace(self.NBSP, ' ').split())
				if genres:
					Detailstext += addnewline + genres
					addnewline = "\n"
					self.callbackGenre = genres

			for category in ("director", "creator", "writer", "seasons"):
				if self.generalinfos.group(category):
					Detailstext += addnewline + self.generalinfos.group('g_'+category) + ": " + ' '.join(self.htmltags.sub('', self.generalinfos.group(category)).replace("\n", ' ').replace(self.NBSP, ' ').replace(self.RAQUO, '').replace(self.HELLIP + ' See all', '...').split())
					addnewline = "\n"

			for category in ("premiere", "country", "alternativ"):
				if self.generalinfos.group(category):
					Detailstext += addnewline + self.generalinfos.group('g_'+category) + ": " + ' '.join(self.htmltags.sub('', self.generalinfos.group(category).replace('\n',' ')).split())
					addnewline = "\n"

			rating = self.ratingmask.search(self.inhtml)
			Ratingtext = _("no user rating yet")
			if rating:
				rating = rating.group("rating")
				if rating != '<span id="voteuser"></span>':
					Ratingtext = _("User Rating") + ": " + rating + " / 10"
					self.ratingstars = int(10*round(float(rating.replace(',','.')),1))
					self["stars"].show()
					self["stars"].setValue(self.ratingstars)
					self["starsbg"].show()
			self["ratinglabel"].setText(Ratingtext)

			castresult = self.castmask.finditer(self.inhtml)
			if castresult:
				Casttext = ""
				for x in castresult:
					Casttext += "\n" + self.htmltags.sub('', x.group('actor'))
					if x.group('character'):
						chartext = self.htmltags.sub('', x.group('character').replace('/ ...','')).replace('\n', ' ').replace(self.NBSP, ' ')
						Casttext += _(" as ") + ' '.join(chartext.split())
						if config.plugins.imdb.showepisodeinfo.value and x.group('episodes'):
							Casttext += ' [' + self.htmltags.sub('', x.group('episodes')).strip() + ']'
				if Casttext:
					Casttext = _("Cast: ") + Casttext
				else:
					Casttext = _("No cast list found in the database.")
				self["castlabel"].setText(Casttext)

			posterurl = self.postermask.search(self.inhtml)
			if posterurl and posterurl.group(1).find("jpg") > 0:
				posterurl = posterurl.group(1)
				self["statusbar"].setText(_("Downloading Movie Poster: %s...") % (posterurl))
				localfile = "/tmp/poster.jpg"
				print("[IMDB] downloading poster " + posterurl + " to " + localfile)
				download = downloadWithProgress(posterurl,localfile)
				download.start().addCallback(self.IMDBPoster).addErrback(self.http_failed)
			else:
				self.IMDBPoster("kein Poster")

			Extratext = ''
			awardsresult = self.awardsmask.finditer(self.inhtml)
			if awardsresult:
				awardslist = [' '.join(x.group('awards').split()) for x in awardsresult]
				if awardslist:
					Extratext = _("Extra Info") + "\n\n" + ' | '.join(awardslist) + "\n"

			extrainfos = self.extrainfomask.search(self.inhtml)

			if extrainfos:
				if not Extratext:
					Extratext = _("Extra Info") + "\n"

				addspace = { "outline", "synopsis","tagline","runtime","locations","trivia","goofs","quotes","connections" }
				extraspace = ''

				for category in ("outline","synopsis","tagline","keywords","cert","runtime","language","color","aspect","sound","locations","company","trivia","goofs","quotes","connections"):
					if category in addspace:
						extraspace = "\n"
					if extrainfos.group(category):
						sep = ":\n" if category in ("outline", "synopsis") else ": "
						Extratext += extraspace
						if category == "outline":
							if "Add a Plot" in extrainfos.group(category):
								continue
							Extratext += _("Plot Outline")
						elif extrainfos.group('g_'+category):
							Extratext += extrainfos.group('g_'+category)
						else:
							Extratext += _("Unknown category")
						Extratext += sep  + ' '.join(self.htmltags.sub('',extrainfos.group(category).replace("\n",' ').replace("<br>", '\n').replace("<br />",'\n')).replace(' |' + self.NBSP, '').replace(self.NBSP, ' ').split()) + "\n"
						extraspace = ''
				if extrainfos.group("g_comments"):
					Extratext += "\n" + extrainfos.group("g_comments") + ":\n" + extrainfos.group("commenttitle") + " [" + ' '.join(self.htmltags.sub('',extrainfos.group("commenter")).split()) + "]: " + self.htmltags.sub('',extrainfos.group("comment").replace("\n",' ').replace(self.NBSP, ' ').replace("<br>", '\n').replace("<br/>",'\n').replace("<br />",'\n')) + "\n"

			if Extratext:
				self["extralabel"].setText(Extratext)
				self["extralabel"].hide()
				self["key_blue"].setText(_("Extra Info"))

		self["detailslabel"].setText(Detailstext)
		self.callbackData = Detailstext

	def IMDBPoster(self,string):
		self["statusbar"].setText(_("IMDb Details parsed"))
		if not string:
			filename = "/tmp/poster.jpg"
		else:
			filename = resolveFilename(SCOPE_PLUGINS, "Extensions/IMDb/no_poster.png")
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((self["poster"].instance.size().width(), self["poster"].instance.size().height(), sc[0], sc[1], False, 1, "#00000000"))
		self.picload.startDecode(filename)

	def paintPosterPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr != None:
			self["poster"].instance.setPixmap(ptr)
			self["poster"].show()

	def setup(self):
		self.session.open(IMDbSetup)

	def createSummary(self):
		return IMDbLCDScreen

class IMDbLCDScreen(Screen):
	skin = """
	<screen position="0,0" size="132,64" title="IMDB Plugin">
		<widget name="headline" position="4,0" size="128,22" font="Regular;20"/>
		<widget source="parent.title" render="Label" position="6,26" size="120,34" font="Regular;14"/>
	</screen>"""

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent)
		self["headline"] = Label(_("IMDb Plugin"))

class IMDbSetup(Screen, ConfigListScreen):
	skin = """<screen name="EPGSearchSetup" position="center,center" size="565,370">
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
		<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
		<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="config" position="5,50" size="555,250" scrollbarMode="showOnDemand" />
		<ePixmap pixmap="skin_default/div-h.png" position="0,301" zPosition="1" size="565,2" />
		<widget source="help" render="Label" position="5,305" size="555,63" font="Regular;21" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["Setup" ]

		self['footnote'] = Label(_("* = Restart Required"))
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)

		# Summary
		self.setup_title = _("IMDb Setup")
		self.onChangedEntry = []

		# Initialize widgets
		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))
		self["description"] = Label("")

		# Define Actions
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
			}, -2)

		self["VirtualKB"] = ActionMap(["VirtualKeyboardActions"],
		{
			"showVirtualKeyboard": self.KeyText,
		}, -2)
		self["VirtualKB"].setEnabled(False)

		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		self.createSetup()
		if not self.handleInputHelpers in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.handleInputHelpers)
		self.changedEntry()
		self.onLayoutFinish.append(self.layoutFinished)

	def createSetup(self):
		self.list = []
		self.list.append(getConfigListEntry(_("Show search in plugin browser"), config.plugins.imdb.showinplugins, _("Enable this to be able to access IMDb searches from within the plugin browser.")))
		self.list.append(getConfigListEntry(_("Show setup in plugin browser"), config.plugins.imdb.showsetupinplugins, _("Enable this to be able to access IMDb search setup from within the plugin browser.")))
		self.list.append(getConfigListEntry(_("Show in movie list"), config.plugins.imdb.showinmovielist, _("Enable this to be able to access IMDb searches from within the movie list."))),
		self.list.append(getConfigListEntry(_("Words / phrases to ignore "), config.plugins.imdb.ignore_tags, _("This option allows you add words/phrases for IMDb to ignore when searching. Please separate the words/phrases with commas.")))
		self.list.append(getConfigListEntry(_("Show full movie or series name in title menu"), config.plugins.imdb.showlongmenuinfo, _("Show the whole IMDb title information for a movie or series, including, for example, alternative names and whether it's a series. Takes effect after the next search of IMDb for a show name.")))
		self.list.append(getConfigListEntry(_("Show episode and year information in cast list"), config.plugins.imdb.showepisodeinfo, _("Show episode and year information for cast when available. Takes effect after the next fetch of show details.")))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def handleInputHelpers(self):
		if self["config"].getCurrent() is not None:
			try:
				if isinstance(self["config"].getCurrent()[1], ConfigText) or isinstance(self["config"].getCurrent()[1], ConfigPassword):
					if self.has_key("VKeyIcon"):
						self["VirtualKB"].setEnabled(True)
						self["VKeyIcon"].boolean = True
					if self.has_key("HelpWindow"):
						if self["config"].getCurrent()[1].help_window.instance is not None:
							helpwindowpos = self["HelpWindow"].getPosition()
							from enigma import ePoint
							self["config"].getCurrent()[1].help_window.instance.move(ePoint(helpwindowpos[0],helpwindowpos[1]))
				else:
					if self.has_key("VKeyIcon"):
						self["VirtualKB"].setEnabled(False)
						self["VKeyIcon"].boolean = False
			except:
				if self.has_key("VKeyIcon"):
					self["VirtualKB"].setEnabled(False)
					self["VKeyIcon"].boolean = False
		else:
			if self.has_key("VKeyIcon"):
				self["VirtualKB"].setEnabled(False)
				self["VKeyIcon"].boolean = False

	def HideHelp(self):
		try:
			if isinstance(self["config"].getCurrent()[1], ConfigText):
				if self["config"].getCurrent()[1].help_window.instance is not None:
					self["config"].getCurrent()[1].help_window.hide()
		except:
			pass

	def KeyText(self):
		if isinstance(self["config"].getCurrent()[1], ConfigText):
			if self["config"].getCurrent()[1].help_window.instance is not None:
				self["config"].getCurrent()[1].help_window.hide()
		self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title = self["config"].getCurrent()[0], text = self["config"].getCurrent()[1].getValue())

	def VirtualKeyBoardCallback(self, callback = None):
		if callback is not None and len(callback):
			self["config"].getCurrent()[1].setValue(callback)
			self["config"].invalidate(self["config"].getCurrent())

	def layoutFinished(self):
		self.setTitle(_(self.setup_title))

	# for summary:
	def changedEntry(self):
		self.item = self["config"].getCurrent()
		for x in self.onChangedEntry:
			x()
		try:
			if isinstance(self["config"].getCurrent()[1], ConfigYesNo) or isinstance(self["config"].getCurrent()[1], ConfigSelection):
				self.createSetup()
		except:
			pass

	def getCurrentEntry(self):
		return self["config"].getCurrent() and self["config"].getCurrent()[0] or ""

	def getCurrentValue(self):
		return self["config"].getCurrent() and str(self["config"].getCurrent()[1].getText()) or ""

	def getCurrentDescription(self):
		return self["config"].getCurrent() and len(self["config"].getCurrent()) > 2 and self["config"].getCurrent()[2] or ""

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary


	def keySave(self):
		self.saveAll()

		for pl in pluginlist:
			if not pl[0].value:
				for plugin in plugins.getPlugins(pl[1].where):
					if plugin is pl[1]:
						plugins.removePlugin(plugin)

		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
		self.close()

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

def eventinfo(session, eventName="", **kwargs):
	if not eventName:
		s = session.nav.getCurrentService()
		if s:
			info = s.info()
			event = info.getEvent(0) # 0 = now, 1 = next
			eventName = event and event.getEventName() or ''
	session.open(IMDB, eventName)

def main(session, eventName="", **kwargs):
	session.open(IMDB, eventName)

def setup(session, **kwargs):
	session.open(IMDbSetup)

def movielistSearch(session, serviceref, **kwargs):
	serviceHandler = eServiceCenter.getInstance()
	info = serviceHandler.info(serviceref)
	eventName = info and info.getName(serviceref) or ''
	(root, ext) = os.path.splitext(eventName)
	if ext in KNOWN_EXTENSIONS:
		eventName = re.sub("[\W_]+", ' ', root.decode("utf8"), 0, re.LOCALE|re.UNICODE).encode("utf8")
	session.open(IMDB, eventName)

pluginlist = (
	(
		config.plugins.imdb.showinplugins,
		PluginDescriptor(
			name=_("IMDb search"),
			description=_("Search for details from the Internet Movie Database"),
			icon="imdb.png",
			where=PluginDescriptor.WHERE_PLUGINMENU,
			fnc=main,
			needsRestart=False,
		)
	),
	(
		config.plugins.imdb.showsetupinplugins,
		PluginDescriptor(
			name=_("IMDb setup"),
			description=_("Settings for Internet Movie Database searches"),
			icon="imdb.png",
			where=PluginDescriptor.WHERE_PLUGINMENU,
			fnc=setup,
			needsRestart=False,
		)
	),
	(
		config.plugins.imdb.showinmovielist,
		PluginDescriptor(
			name=_("IMDb search"),
			description=_("IMDb search"),
			where=PluginDescriptor.WHERE_MOVIELIST,
			fnc=movielistSearch,
			needsRestart=False,
		)
	),
)

def Plugins(**kwargs):
	l = [PluginDescriptor(name=_("IMDb search") + "...",
			description=_("Search for details from the Internet Movie Database"),
			where=PluginDescriptor.WHERE_EVENTINFO,
			fnc=eventinfo,
			needsRestart=False,
			),
		]

	l += [pl[1] for pl in pluginlist if pl[0].value]

	return l
