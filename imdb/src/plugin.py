# -*- coding: UTF-8 -*-
# for localized messages
from __future__ import print_function
from . import _

from Plugins.Plugin import PluginDescriptor
from Tools.Downloader import downloadWithProgress
from enigma import ePicLoad, eServiceCenter
from Screens.Screen import Screen
from Screens.Setup import Setup
from Screens.HelpMenu import HelpableScreen
from Screens.ChoiceBox import ChoiceBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import HelpableActionMap
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
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, isPluginInstalled
import os
import re
import six

from six.moves.urllib.parse import quote_plus

try:
	import htmlentitydefs
except ImportError as ie:
	from html import entities as htmlentitydefs
	unichr = chr


# Configuration
from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigText
from Components.PluginComponent import plugins


config.plugins.imdb = ConfigSubsection()
config.plugins.imdb.showinplugins = ConfigYesNo(default=False)
config.plugins.imdb.showsetupinplugins = ConfigYesNo(default=True)
config.plugins.imdb.showinmovielist = ConfigYesNo(default=True)
config.plugins.imdb.force_english = ConfigYesNo(default=False)
config.plugins.imdb.ignore_tags = ConfigText(visible_width=50, fixed_size=False)
config.plugins.imdb.showlongmenuinfo = ConfigYesNo(default=False)
config.plugins.imdb.showepisodeinfo = ConfigYesNo(default=False)


def quoteEventName(eventName, safe="/()" + ''.join(map(chr, list(range(192, 255))))):
	# BBC uses '\x86' markers in program names, remove them
	try:
		text = eventName.decode('utf8').replace(u'\x86', u'').replace(u'\x87', u'').encode('utf8')
	except:
		text = eventName
	# IMDb doesn't seem to like urlencoded characters at all, hence the big "safe" list
	return quote_plus(text, safe="+")


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
	NBSP = six.unichr(htmlentitydefs.name2codepoint['nbsp'])
	RAQUO = six.unichr(htmlentitydefs.name2codepoint['raquo'])
	HELLIP = six.unichr(htmlentitydefs.name2codepoint['hellip'])
	if six.PY2:
		NBSP = NBSP.encode("utf8")
		RAQUO = RAQUO.encode("utf8")
		HELLIP = HELLIP.encode("utf8")

	def __init__(self, session, eventName, callbackNeeded=False, save=False, savepath=None, localpath=None):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		for tag in config.plugins.imdb.ignore_tags.getValue().split(','):
			eventName = eventName.replace(tag, '')

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
		self["key_help"] = Boolean(True) # for auto buttons
		self["key_menu"] = Boolean(True) # for auto buttons

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
			self.generalinfomask = [re.compile(
			'<h1 class="".*?>(?P<title>.*?)</h1>'
			'(?:.*?<h4 class="inline">\s*(?P<g_director>Regisseur|Directors?):\s*</h4>(?P<director>.*?)</div>)?'
			'(?:.*?<h4 class="inline">\s*(?P<g_creator>Sch\S*?pfer|Creators?):\s*</h4>\s*(?P<creator>.*?)</div>)?'
			'(?:.*?(?P<g_episodes>Episode Guide)</div>\s*<span.*?>(?P<episodes>.*?)<)?'
			'(?:.*?<h4 class="float-left">\s*(?P<g_seasons>Seasons?)\s*</h4>.*?<a .*?>(?P<seasons>.*?)</div>)?'
			'(?:.*?<h4 class="inline">\s*(?P<g_writer>Drehbuch|Writers?):\s*</h4>(?P<writer>.*?)</div>)?'
			'(?:.*?<h4 class="inline">\s*(?P<g_country>Land|Country):\s*</h4>.*?(?P<country>.*?)</div>)?'
			'(?:.*?<h4 class="inline">\s*(?P<g_premiere>Premiere|Release Date).*?</h4>\s+(?P<premiere>.*?)\s*<span)?'
			'(?:.*?<h4 class="inline">\s*(?P<g_alternativ>Auch bekannt als|Also Known As):\s*</h4>\s*(?P<alternativ>.*?)\s*<span)?', re.DOTALL),
			re.compile(
			'<h1.*?hero-title-block__title" class=.*?>(?P<title>.*?)</h1>'
			'(?:.*?>(?P<g_episodes>Episodes)<span.*?>(?P<episodes>.*?)</span>)?'
			'(?:.*?>(?P<seasons>\d+) (?P<g_seasons>[Ss]easons?)<)?'
			'(?:.*?>(?P<g_director>Regisseur|Directors?)</span><div.*?<ul.*?>(?P<director>.*?)</ul>)?'
			'(?:.*?>(?P<g_creator>Sch\S*?pfer|Creators?)</span><div.*?<ul.*?>(?P<creator>.*?)</ul>)?'
			'(?:.*?>(?P<g_writer>Drehbuch|Writers?)</span><div.*?<ul.*?>(?P<writer>.*?)</ul>)?'
			'(?:.*?>(?P<g_premiere>Premiere|Release date)</a><div.*?<ul.*?>(?P<premiere>.*?)</ul>)?'
			'(?:.*?>(?P<g_country>Land|Countr.*?of origin)</span><div.*?<ul.*?>(?P<country>.*?)</ul>)?'
			'(?:.*?>(?P<g_alternativ>Auch bekannt als|Also known as)</a><div.*?<ul.*?>(?P<alternativ>.*?)</ul>)?', re.DOTALL)]

			self.awardsmask = [re.compile('<span class="awards-blurb">(?P<awards>.+?)</span>', re.DOTALL),
			re.compile('data-testid="award_information".*?><a.*?>(?P<awards>.+?)</span></li>', re.DOTALL)]

			self.extrainfomask = [re.compile(
			'(?:.*?<div class="summary_text">(?P<outline>.+?)</div>)?'
			'(?:.*?<h2>(?P<g_synopsis>Storyline)</h2>.*?<span>(?P<synopsis>.+?)</span>)?'
			'(?:.*?<h4 class="inline">(?P<g_keywords>Plot Keywords):</h4>(?P<keywords>.+?)(?:(?:Mehr|See All) \(\d+\)</a>|</div>))?'
			'(?:.*?<h4 class="inline">(?P<g_tagline>Werbezeile|Taglines?):</h4>\s*(?P<tagline>.+?)<)?'
			'(?:.*?<h4 class="inline">(?P<g_cert>Altersfreigabe|Certificate):</h4>\s*<span itemprop="contentRating">(?P<cert>.+?)</span>)?'
			'(?:.*?<h4>(?P<g_trivia>Dies und das|Trivia)</h4>\s*(?P<trivia>.+?)(?:Mehr|See more</a>|</div>))*'
			'(?:.*?<h4>(?P<g_goofs>Pannen|Goofs)</h4>\s*(?P<goofs>.+?)(?:Mehr|See more</a>|</div>))*'
			'(?:.*?<h4>(?P<g_quotes>Dialogzitate|Quotes)</h4>\s*(?P<quotes>.+?)(?:Mehr|See more</a>|</div>))?'
			'(?:.*?<h4>(?P<g_connections>Bez\S*?ge zu anderen Titeln|Connections)</h4>\s*(?P<connections>.+?)(?:Mehr|See more</a>|</div>))?'
			'(?:.*?<h2>(?P<g_comments>Nutzerkommentare|User Review)s</h2>.*?<strong>(?P<commenttitle>.*?)</strong>.*?<div class="comment-meta">(?P<commenter>.+?)</span></a>.*?<p.*?>(?P<comment>.+?)</p>)?'
			'(?:.*?<h4 class="inline">(?P<g_language>Sprache|Language):</h4>\s*(?P<language>.+?)</div>)?'
			'(?:.*?<h4 class="inline">(?P<g_locations>Drehorte|Filming Locations):</h4>.*?<a.*?>(?P<locations>.+?)</a>)?'
			'(?:.*?<h4 class="inline">(?P<g_company>Firma|Production Co):</h4>\s*(?P<company>.+?)(?:Mehr|See more</a>|</div>))?'
			'(?:.*?<h4 class="inline">(?P<g_runtime>L\S*?nge|Runtime):</h4>\s*(?P<runtime>.+?)</div>)?'
			'(?:.*?<h4 class="inline">(?P<g_sound>Tonverfahren|Sound Mix):</h4>\s*(?P<sound>.+?)</div>)?'
			'(?:.*?<h4 class="inline">(?P<g_color>Farbe|Color):</h4>\s*(?P<color>.+?)</div>)?'
			'(?:.*?<h4 class="inline">(?P<g_aspect>Seitenverh\S*?ltnis|Aspect Ratio):</h4>\s*(?P<aspect>.+?)(?:Mehr|See more</a>|</div>))?', re.DOTALL),
			re.compile(
			'(?:.*?data-testid="plot-xl".*?>(?P<outline>.+?)</span)?'
			#'(?:.*?<h3 class="ipc-title__text">(?P<g_synopsis>Storyline)</h3>.*?<div class="ipc-html-content-inner-div">(?P<synopsis>.+?)</div)?'
			#'(?:.*?data-testid="storyline-plot-keywords">(?P<keywords>.+?)\d+\s+(?:mehr|more).*?</div>)?'
			'(?:.*?<a.*?>(?P<g_tagline>Werbezeile|Taglines?)</a>.*?<li.*?<span.*?>(?P<tagline>.+?)<)?'
			'(?:.*?<a.*?>(?P<g_cert>Altersfreigabe|Certificate|Motion Picture Rating \(MPAA\))</a>.*?<div.*?<ul.*?<li.*?<span.*?>(?P<cert>.*?)</span>)?'
			'(?:.*?<a.*?>(?P<g_trivia>Dies und das|Trivia)</a><div.*?<div.*?<div.*?<div.*?>(?P<trivia>.+?)</div>)?'
			'(?:.*?<a.*?>(?P<g_goofs>Pannen|Goofs)</a><div.*?<div.*?<div.*?<div.*?>(?P<goofs>.+?)</div>)?'
			'(?:.*?<a.*?>(?P<g_quotes>Dialogzitate|Quotes)</a><div.*?<div.*?<div.*?<div.*?>(?P<quotes>.+?)</div>)?'
			'(?:.*?<a.*?>(?P<g_connections>Bez\S*?ge zu anderen Titeln|Connections)</a><div.*?<div.*?<div.*?<div.*?>(?P<connections>.+?)</div>)?'
			'(?:.*?<h3.*?>(?P<g_comments>Nutzerkommentare|User reviews).*?</h3>(?:.*?</svg>(?P<g_rating>[0-9]+?)<span class="ipc-rating-star--maxRating">/.*?(?P<g_maxrating>[0-9]+?)</span>)?.*?<span.*?review-summary.*?>(?P<commenttitle>.*?)</span>.*?<div class="ipc-html-content-inner-div">(?P<comment>.+?)</div>.*?<a.*?"author-link">(?P<commenter>.+?)</a>)?' # no match, slow
			'(?:.*?<span.*?>(?P<g_language>Sprachen?|Languages?)</span>.*?<div.*?<ul.*?>(?P<language>.*?)</ul>)?'
			'(?:.*?<a.*?>(?P<g_locations>Drehorte?|Filming locations?)</a>.*?<div.*?<ul.*?>(?P<locations>.*?)</ul>)?'
			'(?:.*?<a.*?>(?P<g_company>Firm\S*?|Production compan.*?)</a>.*?<div.*?<ul.*?>(?P<company>.*?)</ul>)?'
			'(?:.*?<span.*?>(?P<g_runtime>L\S*?nge|Runtime)</span>.*?<div.*?>(?P<runtime>.*?)</div>)?'
			'(?:.*?<span.*?>(?P<g_color>Farbe|Color)</span>.*?<a.*?>(?P<color>.*?)</a>)?'
			'(?:.*?<span.*?>(?P<g_sound>Tonverfahren|Sound mix)</span>.*?<div.*?<ul.*?>(?P<sound>.*?)</ul>)?'
			'(?:.*?<span.*?>(?P<g_aspect>Seitenverh\S*?ltnis|Aspect ratio)</span>.*?<div.*?<ul.*?<li.*?<span.*?>(?P<aspect>.*?)</span>)?', re.DOTALL)]

			self.genreblockmask = [re.compile('<h4 class="inline">(Genres?:</h4>\s*?.*?)\s+?(?:Mehr|See more|</p|<a class|</div>)', re.DOTALL),
			re.compile('storyline-genres.*?><span.*?>(Genres?</span><div.*?><ul.*?>.*?)</ul>', re.DOTALL)]
			self.ratingmask = [re.compile('<div class="ratingValue">.*?<span itemprop="ratingValue">(?P<rating>.*?)</span>', re.DOTALL),
			re.compile('aggregate-rating__score.*?><span.*?>(?P<rating>.*?)</span>', re.DOTALL)]
			self.castmask = [re.compile('<td>\s*<a href=.*?>(?P<actor>.*?)\s*</a>\s*</td>.*?<td class="character">(?P<character>.*?)(?:<a href="#"\s+class="toggle-episodes".*?>(?P<episodes>.*?)</a>.*?)?</td>', re.DOTALL),
			re.compile('title-cast-item__actor.*?>(?P<actor>.*?)</a>(?:<div.*?<ul.*?>(?P<character>.*?)</span.*?</ul></div>)?(?:<a.*?><span><span.*?>(?P<episodes>.*?)</span></span>)?', re.DOTALL)]
			self.postermask = [re.compile('<div class="poster">.*?<img .*?src=\"(http.*?)\"', re.DOTALL),
			re.compile('"hero-media__poster".*?><div.*?<img.*?ipc-image.*?src="(http.*?)"', re.DOTALL)]

		self.htmltags = re.compile('<.*?>', re.DOTALL)
		self.allhtmltags = re.compile('<.*>', re.DOTALL)
		self.fontescapes = re.compile(r'\\([cnrt])')
		self.fontescsub = r'\\\r\1'

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
		if (self.Page == 1 or self.Page == 2) and self.resultlist:
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
		self.generalinfos = self.generalinfomask[self.re_index].search(self.inhtml)
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
			fetchurl = "https://www.imdb.com/title/" + link
			print("[IMDB] showDetails() downloading query " + fetchurl + " to " + localfile)
			download = downloadWithProgress(fetchurl, localfile)
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

		if isPluginInstalled("YTTrailer"):
			list.extend((
				(_("Play Trailer"), self.openYttrailer),
				(_("Search Trailer"), self.searchYttrailer),
			))

		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			title=_("IMDb Menu"),
			list=list,
		)

	def menuCallback(self, ret=None):
		ret and ret[1]()

	def saveHtmlDetails(self):
		try:
			if self.savingpath is not None:
				isave = self.savingpath + ".imdbquery2.html"
				if self.fetchurl is not None:
					download = downloadWithProgress(self.fetchurl, isave)
					download.start().addCallback(self.IMDBsave).addErrback(self.http_failed)
		except Exception as e:
			print('[IMDb] saveHtmlDetails exception failure: ', str(e))

	def saveTxtDetails(self):
		try:
			if self.savingpath is not None:
				getTXT = self.IMDBsavetxt()
				if getTXT is not None:
					open(self.savingpath + ".txt", 'w').write(getTXT)
				else:
					from Screens.MessageBox import MessageBox
					self.session.open(MessageBox, (_('IMDb can not get Movie Information to write to .txt file!')), MessageBox.TYPE_INFO, 10)
		except Exception as e:
			print('[IMDb] saveTxtDetails exception failure: ', str(e))

	def savePosterTxtDetails(self):
		try:
			if self.savingpath is not None:
				getTXT = self.IMDBsavetxt(True)
				if getTXT is not None:
					open(self.savingpath + ".txt", 'w').write(getTXT)
				else:
					from Screens.MessageBox import MessageBox
					self.session.open(MessageBox, (_('IMDb can not get Movie Information to write to .jpg and .txt files!')), MessageBox.TYPE_INFO, 10)
		except Exception as e:
			print('[IMDb] savePosterTxtDetails exception failure: ', str(e))

	def IMDBsave(self, string):
		self["statusbar"].setText(_("IMDb Save - Download completed"))
		self.html2utf8(open("/tmp/imdbquery2.html", "r").read())
		self.generalinfos = self.generalinfomask[self.re_index].search(self.inhtml)
		self.IMDBparse()

	def IMDBsavetxt(self, poster=False):
		overview = ""
		runtime = ""
		genre = ""
		country = ""
		release = ""
		rating = ""

		if self.generalinfos:
			extrainfos = self.extrainfomask[self.re_index].search(self.inhtml)
			if extrainfos:
				# get entry 1 = Overview(details)
				try:
					text = ' '.join(self.htmltags.sub('', extrainfos.group("synopsis").replace("\n", ' ').replace("<br>", '\n').replace("<br />", '\n')).replace(' |' + self.NBSP, '').replace(self.NBSP, ' ').split()) + "\n"
					overview = _("Content:") + " " + text
				except Exception as e:
					print('[IMDb] IMDBsavetxt exception failure in get overview: ', str(e))
					overview = (_("Content:"))
#				print('[IMDb] IMDBsavetxt overview: ', overview)

				# get entry 2 = Runtime
				try:
					time = ' '.join(self.htmltags.sub('', extrainfos.group(category).replace("\n", ' ').replace("<br>", '\n').replace("<br />", '\n')).replace(' |' + self.NBSP, '').replace(self.NBSP, ' ').split())
					runtime = _("Runtime:") + " " + time
				except Exception as e:
					print('[IMDb] IMDBsavetxt exception failure in get runtime: ', str(e))
					runtime = (_("Runtime:"))
#				print('[IMDb] IMDBsavetxt runtime: ', runtime)

			# get entry 3 = Genre
			genreblock = self.genreblockmask[self.re_index].search(self.inhtml)
			if genreblock:
				if self.re_index == 1:
					genres = re.sub(r'\|+', ' | ', self.htmltags.sub('|', genreblock.group(1)).strip('|'))
					genres = genres.replace(' |', ':', 1)  # first one is the category
				else:
					genres = ' '.join(self.htmltags.sub('', genreblock.group(1)).replace(self.NBSP, ' ').split())
			else:
				genre = (_("Genre:"))
#			print('[IMDb] IMDBsavetxt genre: ', genre)

			# get entry 4 = Country
			try:
				land = ' '.join(self.htmltags.sub('', self.generalinfos.group("country").replace('\n', ' ')).split())
				country = _("Production Countries:") + " " + land
			except Exception as e:
				print('[IMDb] IMDBsavetxt exception failure in get country: ', str(e))
				country = (_("Production Countries:"))
#			print('[IMDb] IMDBsavetxt country: ', country)

			# get entry 5 = ReleaseDate
			try:
				date = ' '.join(self.htmltags.sub('', self.generalinfos.group("premiere").replace('\n', ' ')).split())
				release = _("Release Date:") + " " + date
			except Exception as e:
				print('[IMDb] IMDBsavetxt exception failure in get release: ', str(e))
				release = (_("Release Date:"))
#			print('[IMDb] IMDBsavetxt release: ', release)

			# get entry 5 = Vote
			ratingtext = self.ratingmask[self.re_index].search(self.inhtml)
			if ratingtext:
				ratingtext = ratingtext.group("rating")
				if ratingtext != '<span id="voteuser"></span>':
					text = ratingtext                                # + " / 10"
					rating = _("User Rating") + ": " + text
			else:
				rating = (_("User Rating") + ": ")
#			print('[IMDb] IMDBsavetxt rating: ', rating)

			# get the poster.jpg
			if poster:
				try:
					posterurl = self.postermask[self.re_index].search(self.inhtml)
					if posterurl and posterurl.group(1).find("jpg") > 0:
						posterurl = posterurl.group(1)
						postersave = self.savingpath + ".poster.jpg"
#						print("[IMDB] downloading poster " + posterurl + " to " + postersave)
						download = downloadWithProgress(posterurl, postersave)
						download.start().addErrback(self.http_failed)
				except Exception as e:
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
			title=_("Enter text to search for"),
			text=self.eventName
		)

	def gotSearchString(self, ret=None):
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
		if not isinstance(self.eventName, six.string_types):
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
				self.eventName = self.eventName.replace('.', ' ')
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
				fetchurl = "https://www.imdb.com/find?q=" + quoteEventName(self.eventName) + "&s=tt&site=aka"
#				print("[IMDB] getIMDB() Downloading Query " + fetchurl + " to " + localfile)
				download = downloadWithProgress(fetchurl, localfile)
				download.start().addCallback(self.IMDBquery).addErrback(self.http_failed)

			else:
				self["statusbar"].setText(_("Could't get event name"))

	def html2utf8(self, in_html):
		utf8 = ('charSet="utf-8"' in in_html or 'charset="utf-8"' in in_html or
				'charSet=utf-8' in in_html or 'charset=utf-8' in in_html)

		if 'hero-title-block__title' in in_html:
			self.re_index = 1
			start = in_html.find('<nav id="imdbHeader"')
			if start == -1:
				start = 0
			end = in_html.find('<section data-testid="contribution"')
			if end == -1:
				end = in_html.find('<div id="taboola_wrapper">')
			if end == -1:
				end = len(in_html)
			in_html = in_html[start:end]  # speed up re searches by trimming irrelevant text
		else:
			self.re_index = 0

		in_html = re.sub(r'(?s)<(script|style|svg).*?</\1>', '', in_html)
		entitydict = {}

		entities = re.finditer(r'&(?:([A-Za-z0-9]+)|#x([0-9A-Fa-f]+)|#([0-9]+));', in_html)
		for x in entities:
			key = x.group(0)
			if key not in entitydict:
				if x.group(1):
					if x.group(1) in htmlentitydefs.name2codepoint:
						entitydict[key] = htmlentitydefs.name2codepoint[x.group(1)]
				elif x.group(2):
					entitydict[key] = str(int(x.group(2), 16))
				else:  # x.group(3)
					entitydict[key] = x.group(3)

		if utf8:
			for key, codepoint in six.iteritems(entitydict):
				cp = six.unichr(int(codepoint))
				if six.PY2:
					cp = cp.encode('utf8')
				in_html = in_html.replace(key, cp)
			self.inhtml = in_html
		else:
			for key, codepoint in six.iteritems(entitydict):
				cp = six.unichr(int(codepoint))
				if six.PY2:
					cp = cp.encode('latin-1', 'ignore')
				in_html = in_html.replace(key, cp)
#			print("[IMDB][html2utf8] decode html ")
			if six.PY2:
				self.inhtml = in_html.decode('latin-1').encode('utf8')

	def IMDBquery(self, string):
		self["statusbar"].setText(_("IMDb Download completed"))

		self.html2utf8(open("/tmp/imdbquery.html", "r").read())

		self.generalinfos = self.generalinfomask[self.re_index].search(self.inhtml)
		if self.generalinfos:
			self.IMDBparse()
		else:
			if re.search("<title>Find - IMDb</title>", self.inhtml):
				pos = self.inhtml.find('<table class="findList">')
				pos2 = self.inhtml.find("</table>", pos)
				findlist = self.inhtml[pos:pos2]
				searchresultmask = re.compile('<tr class="findResult (?:odd|even)">.*?<td class="result_text"> (<a href="/title/(tt\d{7,8}/).*?"\s?>(.*?)</a>.*?)</td>', re.DOTALL)
				searchresults = searchresultmask.finditer(findlist)
				titlegroup = 1 if config.plugins.imdb.showlongmenuinfo.value else 3
				self.resultlist = [(' '.join(self.htmltags.sub('', x.group(titlegroup)).replace(self.NBSP, " ").split()), x.group(2)) for x in searchresults]
				Len = len(self.resultlist)
				self["menu"].l.setList(self.resultlist)
				if Len == 1:
					self["statusbar"].setText(_("Re-Query IMDb: %s...") % (self.resultlist[0][0],))
					self.eventName = self.resultlist[0][0]
					localfile = "/tmp/imdbquery2.html"
					fetchurl = "https://www.imdb.com/title/" + self.resultlist[0][1]
					self.fetchurl = fetchurl
					download = downloadWithProgress(fetchurl, localfile)
					download.start().addCallback(self.IMDBquery2).addErrback(self.http_failed)
				elif Len > 1:
					self.Page = 1
					self.showMenu()
				else:
					self["detailslabel"].setText(_("No IMDb match."))
					self["statusbar"].setText(_("No IMDb match:") + ' ' + self.eventName)
			else:
				splitpos = self.eventName.find('(')
				if splitpos > 0 and self.eventName.endswith(')'):
					self.eventName = self.eventName[splitpos + 1:-1]
					self["statusbar"].setText(_("Re-Query IMDb: %s...") % (self.eventName))
					# event_quoted = quoteEventName(self.eventName)
					localfile = "/tmp/imdbquery.html"
					fetchurl = "https://www.imdb.com/find?q=" + quoteEventName(self.eventName) + "&s=tt&site=aka"
					download = downloadWithProgress(fetchurl, localfile)
					download.start().addCallback(self.IMDBquery).addErrback(self.http_failed)
				else:
					self["detailslabel"].setText(_("IMDb query failed!"))

	def http_failed(self, failure_instance=None, error_message=""):
		text = _("IMDb Download failed")
		self.postered = False 
		if error_message == "" and failure_instance is not None:
			error_message = failure_instance.getErrorMessage()
			text += ": " + error_message
#		print("[IMDB] ", text)
		self["statusbar"].setText(text)

	def IMDBquery2(self, string):
		self["statusbar"].setText(_("IMDb Re-Download completed"))
		self.html2utf8(open("/tmp/imdbquery2.html", "r").read())
		self.generalinfos = self.generalinfomask[self.re_index].search(self.inhtml)
		self.IMDBparse()

	def IMDBparse(self):
		self.Page = 1
		Detailstext = _("No details found.")
		if self.generalinfos:
			self["key_yellow"].setText(_("Details"))
			self["statusbar"].setText(_("IMDb Details parsed") + ('.' if self.re_index == 1 else ''))
			Titeltext = self.generalinfos.group("title").replace(self.NBSP, ' ').strip()
			if len(Titeltext) > 57:
				Titeltext = Titeltext[0:54] + "..."
			Titeltext = self.fontescapes.sub(self.fontescsub, Titeltext)
			self["title"].setText(Titeltext)

			Detailstext = ""
			addnewline = ''

			genreblock = self.genreblockmask[self.re_index].search(self.inhtml)
			if genreblock:
				if self.re_index == 1:
					genres = re.sub(r'\|+', ' | ', self.htmltags.sub('|', genreblock.group(1)).strip('|'))
					genres = genres.replace(' |', ':', 1)  # first one is the category
				else:
					genres = ' '.join(self.htmltags.sub('', genreblock.group(1)).replace(self.NBSP, ' ').split())
				if genres:
					Detailstext += addnewline + genres
					addnewline = "\n"
					self.callbackGenre = genres

			for category in ("director", "creator", "writer", "seasons", "episodes"):
				try:
					if self.generalinfos.group(category):
#						print("[IMDB][IMDBparse] category = %s" % category)
						if self.re_index == 1:
							if category in ('seasons', 'episodes'):
								txt = self.generalinfos.group(category)
							else:
								txt = re.sub(r'\|+', ', ', self.htmltags.sub('|', self.generalinfos.group(category).replace('</a><span class="ipc-metadata-list-item__list-content-item--subText">', ' ')).strip('|'))
						else:
							txt = ' '.join(self.htmltags.sub('', self.generalinfos.group(category)).replace("\n", ' ').replace(self.NBSP, ' ').replace(self.RAQUO, '').replace(self.HELLIP + ' See all', '...').split())
						# "1 Season", but "N seasons".
						cat = self.generalinfos.group('g_' + category)
						if cat == "seasons":
							cat = "Seasons"
						Detailstext += addnewline + cat + ": " + txt
						addnewline = "\n"
				except IndexError:
					pass

			for category in ("premiere", "country", "alternativ"):
				try:
					if self.generalinfos.group(category):
						if self.re_index == 1:
							txt = re.sub(r'\|+', ', ', self.htmltags.sub('|', self.generalinfos.group(category).replace('\n', ' ')).strip('|'))
						else:
							txt = ' '.join(self.htmltags.sub('', self.generalinfos.group(category).replace('\n', ' ')).split())
						Detailstext += addnewline + self.generalinfos.group('g_' + category) + ": " + txt
						addnewline = "\n"
				except IndexError:
					pass

			rating = self.ratingmask[self.re_index].search(self.inhtml)
			Ratingtext = _("no user rating yet")
			if rating:
				rating = rating.group("rating")
				if rating != '<span id="voteuser"></span>':
					Ratingtext = _("User Rating") + ": " + rating + " / 10"
					self.ratingstars = int(10 * round(float(rating.replace(',', '.')), 1))
					self["stars"].show()
					self["stars"].setValue(self.ratingstars)
					self["starsbg"].show()
			self["ratinglabel"].setText(Ratingtext)

			castresult = self.castmask[self.re_index].finditer(self.inhtml)
			if castresult:
				Casttext = ""
				prefix = "\n " if self.re_index == 1 else "\n"
				for x in castresult:
					Casttext += prefix + self.htmltags.sub('', x.group('actor'))
					if x.group('character'):
						chartext = self.htmltags.sub('', x.group('character').replace('/ ...', '')).replace('\n', ' ').replace(self.NBSP, ' ')
						Casttext += _(" as ") + chartext.strip()
					try:
						if config.plugins.imdb.showepisodeinfo.value and x.group('episodes'):
							Casttext += ' [' + self.htmltags.sub('', re.sub(r"[0-9]+ ep(?:s|\b)", "", x.group('episodes')).replace(' • ', ', ')).strip() + ']'
					except IndexError:
						pass
				if Casttext:
					Casttext = _("Cast: ") + self.fontescapes.sub(self.fontescsub, Casttext)
				else:
					Casttext = _("No cast list found in the database.")
				self["castlabel"].setText(Casttext)

			posterurl = self.postermask[self.re_index].search(self.inhtml)
			self.postered = False
			if posterurl and posterurl.group(1).find("jpg") > 0:
				self.postered = True
				posterurl = posterurl.group(1)
				self["statusbar"].setText(_("Downloading Movie Poster: %s...") % (posterurl))
				localfile = "/tmp/poster.jpg"
#				print("[IMDB] downloading poster " + posterurl + " to " + localfile)
				download = downloadWithProgress(posterurl, localfile)
				download.start().addCallback(self.IMDBPoster).addErrback(self.http_failed)
			else:
				self.IMDBPoster("No  Poster Art")

			Extratext = ''
			awardsresult = self.awardsmask[self.re_index].finditer(self.inhtml)
			awardslist = [x.group('awards').strip() for x in awardsresult]
			if awardslist:
#				print('[IMDB] awardslist', awardslist)
				awardstext = self.allhtmltags.sub(' | ', ''.join(awardslist))
				if awardstext.startswith("Awards | "):
					awardstext = awardstext[9:]
				Extratext = _("Extra Info") + "\n\n" + awardstext + "\n"

			extrainfos = self.extrainfomask[self.re_index].search(self.inhtml)

			if extrainfos:
				if not Extratext:
					Extratext = _("Extra Info") + "\n"

				firstnospace = True
				nospace = ("cert", "runtime", "language", "color", "aspect", "sound")
				categories = ("outline", "synopsis", "tagline", "keywords", "cert", "runtime", "language", "color", "aspect", "sound", "locations", "company", "trivia", "goofs", "quotes", "connections")
				for category in categories:
					try:
						if extrainfos.group(category):
							sep = ":\n" if category in ("outline", "synopsis") else ": "
							extraspace = "\n"
							if category in nospace:
								if firstnospace:
									firstnospace = False
								else:
									extraspace = ''
							Extratext += extraspace
							if category == "outline":
								outline = extrainfos.group("outline")
								outline = outline and self.htmltags.sub('', outline) or ''
								if outline.endswith("... Read all"):
									outline = outline[:-12]
								synopsis = extrainfos.group("synopsis") or ''
								if ("Add a Plot" in extrainfos.group(category) or
										self.htmltags.sub('', synopsis).startswith(outline)):
									Extratext = Extratext[:-len(extraspace)]
									continue
								Extratext += _("Plot Outline")
							else:
								try:
									Extratext += extrainfos.group('g_' + category)
								except IndexError:
									if category == "keywords":
										Extratext += _("Plot Keywords")
									else:
										Extratext += _("Unknown category")
							if self.re_index == 1 and category in ("quotes", "keywords", "language", "sound", "locations", "company"):
								if category == "quotes":
									txt = self.htmltags.sub('', extrainfos.group(category).replace("\n", ' ').replace("<p>", '\n').replace("<br>", '\n').replace("<br />", '\n'))
								else:
									txt = re.sub(r'\|+', category in ("keywords", "sound") and ' | ' or ', ', self.htmltags.sub('|', extrainfos.group(category).replace("\n", ' ').replace("<br>", '\n').replace("<br />", '\n')).strip('|').replace(' |' + self.NBSP, '').replace(self.NBSP, ' '))
							else:
								txt = ' '.join(self.htmltags.sub('', extrainfos.group(category).replace("\n", ' ').replace("<br>", '\n').replace("<br />", '\n')).replace(' |' + self.NBSP, '').replace(self.NBSP, ' ').split())
							Extratext += sep + txt + "\n"
					except IndexError:
						pass
				try:
					if extrainfos.group("g_comments"):
						Extratext += "\n" + extrainfos.group("g_comments") + ": " + extrainfos.group("commenttitle") + " [" + self.htmltags.sub('', extrainfos.group("commenter")).strip() + "]\n" + self.htmltags.sub('', extrainfos.group("comment").replace("\n", ' ').replace(self.NBSP, ' ').replace("<br>", '\n').replace("<br/>", '\n').replace("<br />", '\n')) + "\n"
				except IndexError:
					pass

			if Extratext:
				Extratext = self.fontescapes.sub(self.fontescsub, Extratext)
				self["extralabel"].setText(Extratext)
				self["extralabel"].hide()
				self["key_blue"].setText(_("Extra Info"))

		Detailstext = self.fontescapes.sub(self.fontescsub, Detailstext)
		self["detailslabel"].setText(Detailstext)
		self.callbackData = Detailstext

	def IMDBPoster(self, string):
		self["statusbar"].setText(_("IMDb Details parsed") + ('.' if self.re_index == 1 else ''))
		if self.postered:
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


class IMDbSetup(Setup):
	def __init__(self, session):
		Setup.__init__(self, session, "imdb", plugin="Extensions/IMDb", PluginLanguageDomain="IMDb")
		self.setTitle(_("IMDb Setup"))

	def keySave(self):
		self.saveAll()
		for pl in pluginlist:
			if not pl[0].value:
				for plugin in plugins.getPlugins(pl[1].where):
					if plugin is pl[1]:
						plugins.removePlugin(plugin)

		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
		self.close()


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
	KNOWN_EXTENSIONS2 = frozenset(('x264', '720p', '1080p', '1080i', 'PAL', 'GERMAN', 'ENGLiSH', 'WS', 'DVDRiP', 'UNRATED', 'RETAIL', 'Web-DL', 'DL', 'LD', 'MiC', 'MD', 'DVDR', 'BDRiP', 'BLURAY', 'DTS', 'UNCUT', 'ANiME', 'AC3MD', 'AC3', 'AC3D', 'TS', 'DVDSCR', 'COMPLETE', 'INTERNAL', 'DTSD', 'XViD', 'DIVX', 'DUBBED', 'LINE.DUBBED', 'DD51', 'DVDR9', 'DVDR5', 'h264', 'AVC', 'WEBHDTVRiP', 'WEBHDRiP', 'WEBRiP', 'WEBHDTV', 'WebHD', 'HDTVRiP', 'HDRiP', 'HDTV', 'ITUNESHD', 'REPACK', 'SYNC'))
	serviceHandler = eServiceCenter.getInstance()
	info = serviceHandler.info(serviceref)
	eventName = info and info.getName(serviceref) or ''
	(root, ext) = os.path.splitext(eventName)
	if ext in KNOWN_EXTENSIONS or ext in KNOWN_EXTENSIONS2:
		if six.PY2:
			root = root.decode("utf8")
			eventName = re.sub(r"[\W_]+", ' ', root, 0, re.LOCALE | re.UNICODE)
			eventName = eventName.encode("utf8")
		else:
			eventName = re.sub(r"[\W_]+", ' ', root, 0)
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
