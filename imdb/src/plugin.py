# -*- coding: UTF-8 -*-
from Plugins.Plugin import PluginDescriptor
from twisted.web.client import downloadPage
from enigma import ePicLoad, eServiceReference
from Screens.Screen import Screen
from Screens.EpgSelection import EPGSelection
from Screens.ChannelSelection import SimpleChannelSelection
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.AVSwitch import AVSwitch
from Components.MenuList import MenuList
from Components.Language import language
from Components.ProgressBar import ProgressBar
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from os import environ as os_environ
import re
import htmlentitydefs
import urllib
import gettext

def localeInit():
	lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
	os_environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain("IMDb", resolveFilename(SCOPE_PLUGINS, "Extensions/IMDb/locale"))

def _(txt):
	t = gettext.dgettext("IMDb", txt)
	if t == txt:
		print "[IMDb] fallback to default translation for", txt 
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

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
			self.session.openWithCallback(
				self.epgClosed,
				IMDBEPGSelection,
				ref,
				openPlugin = False
			)

	def epgClosed(self, ret = None):
		if ret:
			self.close(ret)

class IMDBEPGSelection(EPGSelection):
	def __init__(self, session, ref, openPlugin = True):
		EPGSelection.__init__(self, session, ref)
		self.skinName = "EPGSelection"
		self["key_green"].setText(_("Lookup"))
		self.openPlugin = openPlugin

	def infoKeyPressed(self):
		self.timerAdd()

	def timerAdd(self):
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
		pass

class IMDB(Screen):
	skin = """
		<screen name="IMDB" position="90,95" size="560,420" title="Internet Movie Database Details Plugin" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#9f1313" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#a08500" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#18188b" transparent="1" />
			<widget name="titellabel" position="10,40" size="330,45" valign="center" font="Regular;22"/>
			<widget name="detailslabel" position="105,90" size="445,140" font="Regular;18" />
			<widget name="castlabel" position="10,235" size="540,155" font="Regular;18" />
			<widget name="extralabel" position="10,40" size="540,350" font="Regular;18" />
			<widget name="ratinglabel" position="340,62" size="210,20" halign="center" font="Regular;18" foregroundColor="#f0b400"/>
			<widget name="statusbar" position="10,404" size="540,16" font="Regular;16" foregroundColor="#cccccc" />
			<widget name="poster" position="4,90" size="96,140" alphatest="on" />
			<widget name="menu" position="10,115" size="540,275" zPosition="3" scrollbarMode="showOnDemand" />
			<widget name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IMDb/starsbar_empty.png" position="340,40" zPosition="0" size="210,21" transparent="1" alphatest="on" />
			<widget name="stars" position="340,40" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IMDb/starsbar_filled.png" transparent="1" />
		</screen>"""

	def __init__(self, session, eventName, callbackNeeded=False):
		Screen.__init__(self, session)

		self.eventName = eventName
		
		self.callbackNeeded = callbackNeeded
		self.callbackData = ""
		self.callbackGenre = ""

		self.dictionary_init()

		self["poster"] = Pixmap()
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintPosterPixmapCB)

		self["stars"] = ProgressBar()
		self["starsbg"] = Pixmap()
		self["stars"].hide()
		self["starsbg"].hide()
		self.ratingstars = -1

		self["titellabel"] = Label(_("The Internet Movie Database"))
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

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "MovieSelectionActions", "DirectionActions"],
		{
			"ok": self.showDetails,
			"cancel": self.exit,
			"down": self.pageDown,
			"up": self.pageUp,
			"red": self.exit,
			"green": self.showMenu,
			"yellow": self.showDetails,
			"blue": self.showExtras,
			"contextMenu": self.openChannelSelection,
			"showEventInfo": self.showDetails
		}, -1)

		self.getIMDB()

	def exit(self):
		if self.callbackNeeded:
			self.close([self.callbackData, self.callbackGenre])
		else:
			self.close()

	def dictionary_init(self):
		syslang = language.getLanguage()
		if "de" not in syslang:
			self.IMDBlanguage = ""  # set to empty ("") for english version
		else:
			self.IMDBlanguage = "german." # it's a subdomain, so add a '.' at the end

		self.htmltags = re.compile('<.*?>')

		self.generalinfomask = re.compile(
		'<h1>(?P<title>.*?) <.*?</h1>.*?'
		'(?:.*?<h5>(?P<g_director>Regisseur|Directors?):</h5>.*?>(?P<director>.*?)</a>)*'
		'(?:.*?<h5>(?P<g_creator>Sch\S*?pfer|Creators?):</h5>.*?>(?P<creator>.*?)</a>)*'
		'(?:.*?<h5>(?P<g_seasons>Seasons):</h5>(?:.*?)<a href=\".*?\">(?P<seasons>\d+?)</a>\s+?(?:<a class|\|\s+?<a href="episodes#season-unknown))*'
		'(?:.*?<h5>(?P<g_writer>Drehbuch|Writer).*?</h5>.*?>(?P<writer>.*?)</a>)*'
		'(?:.*?<h5>(?P<g_premiere>Premiere|Release Date).*?</h5>\s.*?\n?(?P<premiere>.*?)\n\s.*?<)*'
		'(?:.*?<h5>(?P<g_alternativ>Alternativ|Also Known As):</h5>(?P<alternativ>.*?)<br>\s{0,8}<a.*?>(?:mehr|more))*'
		'(?:.*?<h5>(?P<g_country>Produktionsland|Country):</h5>.*?<a.*?>(?P<country>.*?)</a>(?:.*?mehr|\n</div>))*'
		, re.DOTALL)

		self.extrainfomask = re.compile(
		'(?:.*?<h5>(?P<g_tagline>Werbezeile|Tagline?):</h5>\n(?P<tagline>.+?)<)*'
		'(?:.*?<h5>(?P<g_outline>Kurzbeschreibung|Plot Outline):</h5>(?P<outline>.+?)<)*'
		'(?:.*?<h5>(?P<g_synopsis>Plot Synopsis):</h5>(?:.*?)(?:<a href=\".*?\">)*?(?P<synopsis>.+?)(?:</a>|</div>))*'
		'(?:.*?<h5>(?P<g_keywords>Plot Keywords):</h5>(?P<keywords>.+?)(?:mehr|more</a>|</div>))*'
		'(?:.*?<h5>(?P<g_awards>Filmpreise|Awards):</h5>(?P<awards>.+?)(?:mehr|more</a>|</div>))*'
		'(?:.*?<h5>(?P<g_runtime>L\S*?nge|Runtime):</h5>(?P<runtime>.+?)<)*'
		'(?:.*?<h5>(?P<g_language>Sprache|Language):</h5>(?P<language>.+?)</div>)*'
		'(?:.*?<h5>(?P<g_color>Farbe|Color):</h5>(?P<color>.+?)</div>)*'
		'(?:.*?<h5>(?P<g_aspect>Seitenverh\S*?ltnis|Aspect Ratio):</h5>(?P<aspect>.+?)(?:mehr|more</a>|</div>))*'
		'(?:.*?<h5>(?P<g_sound>Tonverfahren|Sound Mix):</h5>(?P<sound>.+?)</div>)*'
		'(?:.*?<h5>(?P<g_cert>Altersfreigabe|Certification):</h5>(?P<cert>.+?)</div>)*'
		'(?:.*?<h5>(?P<g_locations>Drehorte|Filming Locations):</h5>(?P<locations>.+?)(?:mehr|more</a>|</div>))*'
		'(?:.*?<h5>(?P<g_company>Firma|Company):</h5>(?P<company>.+?)(?:mehr|more</a>|</div>))*'
		'(?:.*?<h5>(?P<g_trivia>Dies und das|Trivia):</h5>(?P<trivia>.+?)(?:mehr|more</a>|</div>))*'
		'(?:.*?<h5>(?P<g_goofs>Pannen|Goofs):</h5>(?P<goofs>.+?)(?:mehr|more</a>|</div>))*'
		'(?:.*?<h5>(?P<g_quotes>Dialogzitate|Quotes):</h5>(?P<quotes>.+?)(?:mehr|more</a>|</div>))*'
		'(?:.*?<h5>(?P<g_connections>Bez\S*?ge zu anderen Titeln|Movie Connections):</h5>(?P<connections>.+?)(?:mehr|more</a>|</div>))*'
		'(?:.*?<h3>(?P<g_comments>Nutzerkommentare|User Comments)</h3>.*?<a href="/user/ur\d{7,7}/comments">(?P<commenter>.+?)\n</div>.*?<p>(?P<comment>.+?)</p>)*'
		, re.DOTALL)

	def resetLabels(self):
		self["detailslabel"].setText("")
		self["ratinglabel"].setText("")
		self["titellabel"].setText("")
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
			self["titellabel"].setText(_("Ambiguous results"))
			self["detailslabel"].setText(_("Please select the matching entry"))
			self["detailslabel"].show()
			self["key_blue"].setText("")
			self["key_green"].setText(_("Title Menu"))
			self["key_yellow"].setText(_("Details"))
			self.Page = 0

	def showDetails(self):
		self["ratinglabel"].show()
		self["castlabel"].show()
		self["detailslabel"].show()

		if self.resultlist and self.Page == 0:
			link = self["menu"].getCurrent()[1]
			title = self["menu"].getCurrent()[0]
			self["statusbar"].setText(_("Re-Query IMDb: %s...") % (title))
			localfile = "/tmp/imdbquery2.html"
			fetchurl = "http://" + self.IMDBlanguage + "imdb.com/title/" + link
			print "[IMDB] downloading query " + fetchurl + " to " + localfile
			downloadPage(fetchurl,localfile).addCallback(self.IMDBquery2).addErrback(self.fetchFailed)
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

	def openChannelSelection(self):
		self.session.openWithCallback(
			self.channelSelectionClosed,
			IMDBChannelSelection
		)

	def channelSelectionClosed(self, ret = None):
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
			self.getIMDB()

	def getIMDB(self):
		self.resetLabels()
		if self.eventName is "":
			s = self.session.nav.getCurrentService()
			info = s.info()
			event = info.getEvent(0) # 0 = now, 1 = next
			if event:
				self.eventName = event.getEventName()
		if self.eventName is not "":
			self["statusbar"].setText(_("Query IMDb: %s...") % (self.eventName))
			event_quoted = urllib.quote(self.eventName.decode('utf8').encode('latin-1','ignore'))
			localfile = "/tmp/imdbquery.html"
			fetchurl = "http://" + self.IMDBlanguage + "imdb.com/find?q=" + event_quoted + "&s=tt&site=aka"
			print "[IMDB] Downloading Query " + fetchurl + " to " + localfile
			downloadPage(fetchurl,localfile).addCallback(self.IMDBquery).addErrback(self.fetchFailed)
		else:
			self["statusbar"].setText(_("Could't get Eventname"))

	def fetchFailed(self,string):
		print "[IMDB] fetch failed " + string
		self["statusbar"].setText(_("IMDb Download failed"))

	def html2utf8(self,in_html):
		htmlentitynumbermask = re.compile('(&#(\d{1,5}?);)')
		htmlentityhexmask = re.compile('(&#x([0-9A-Fa-f]{2,2}?);)')
		htmlentitynamemask = re.compile('(&([^#]\D{1,5}?);)')
		entitydict = {}
		entityhexdict = {}
		entities = htmlentitynamemask.finditer(in_html)

		for x in entities:
			entitydict[x.group(1)] = x.group(2)
		for key, name in entitydict.items():
			entitydict[key] = htmlentitydefs.name2codepoint[name]
		entities = htmlentityhexmask.finditer(in_html)

		for x in entities:
			entityhexdict[x.group(1)] = x.group(2)

		for key, name in entityhexdict.items():
			entitydict[key] = "%d" % int(key[3:5], 16)
			print "key:", key, "before:", name, "after:", entitydict[key]
		
		entities = htmlentitynumbermask.finditer(in_html)
		for x in entities:
			entitydict[x.group(1)] = x.group(2)
		for key, codepoint in entitydict.items():
			in_html = in_html.replace(key, (unichr(int(codepoint)).encode('latin-1')))
		self.inhtml = in_html.decode('latin-1').encode('utf8')

	def IMDBquery(self,string):
		print "[IMDBquery]"
		self["statusbar"].setText(_("IMDb Download completed"))

		self.html2utf8(open("/tmp/imdbquery.html", "r").read())

		self.generalinfos = self.generalinfomask.search(self.inhtml)

		if self.generalinfos:
			self.IMDBparse()
		else:
			if re.search("<title>(?:IMDb.{0,9}Search|IMDb Titelsuche)</title>", self.inhtml):
				searchresultmask = re.compile("<tr> <td.*?img src.*?>.*?<a href=\".*?/title/(tt\d{7,7})/\".*?>(.*?)</td>", re.DOTALL)
				searchresults = searchresultmask.finditer(self.inhtml)
				self.resultlist = [(self.htmltags.sub('',x.group(2)), x.group(1)) for x in searchresults]
				self["menu"].l.setList(self.resultlist)
				if len(self.resultlist) > 1:
					self.Page = 1
					self.showMenu()
				else:
					self["detailslabel"].setText(_("No IMDb match."))
					self["statusbar"].setText(_("No IMDb match."))
			else:
				splitpos = self.eventName.find('(')
				if splitpos > 0 and self.eventName.endswith(')'):
					self.eventName = self.eventName[splitpos+1:-1]
					self["statusbar"].setText(_("Re-Query IMDb: %s...") % (self.eventName))
					event_quoted = urllib.quote(self.eventName.decode('utf8').encode('latin-1','ignore'))
					localfile = "/tmp/imdbquery.html"
					fetchurl = "http://" + self.IMDBlanguage + "imdb.com/find?q=" + event_quoted + "&s=tt&site=aka"
					print "[IMDB] Downloading Query " + fetchurl + " to " + localfile
					downloadPage(fetchurl,localfile).addCallback(self.IMDBquery).addErrback(self.fetchFailed)
				else:
					self["detailslabel"].setText(_("IMDb query failed!"))

	def IMDBquery2(self,string):
		self["statusbar"].setText(_("IMDb Re-Download completed"))
		self.html2utf8(open("/tmp/imdbquery2.html", "r").read())
		self.generalinfos = self.generalinfomask.search(self.inhtml)
		self.IMDBparse()

	def IMDBparse(self):
		print "[IMDBparse]"
		self.Page = 1
		Detailstext = _("No details found.")
		if self.generalinfos:
			self["key_yellow"].setText(_("Details"))
			self["statusbar"].setText(_("IMDb Details parsed"))
			Titeltext = self.generalinfos.group("title")
			if len(Titeltext) > 57:
				Titeltext = Titeltext[0:54] + "..."
			self["titellabel"].setText(Titeltext)

			Detailstext = ""

			genreblockmask = re.compile('<h5>Genre:</h5>(.*?)(?:mehr|more|</div>)', re.DOTALL)
			genreblock = genreblockmask.findall(self.inhtml)
			genremask = re.compile('(?:\">|\s)(.*?)(?:</a|\s)')
			if genreblock:
				genres = genremask.finditer(genreblock[0])
				if genres:
					Detailstext += "Genre: "
					self.callbackGenre = ""
					for x in genres:
						Detailstext += x.group(1) + " "
						self.callbackGenre += x.group(1) + " "

			for category in ("director", "creator", "writer", "premiere", "seasons", "country"):
				if self.generalinfos.group('g_'+category):
					Detailstext += "\n" + self.generalinfos.group('g_'+category) + ": " + self.generalinfos.group(category)

			if self.generalinfos.group("alternativ"):
				Detailstext += "\n" + self.generalinfos.group("g_alternativ") + ": " + self.htmltags.sub('',(self.generalinfos.group("alternativ").replace('\n','').replace("<br>",'\n').replace("  ",' ')))

			ratingmask = re.compile('<h5>(?P<g_rating>Nutzer-Bewertung|User Rating):</h5>.*?<b>(?P<rating>.*?)/10</b>', re.DOTALL)
			rating = ratingmask.search(self.inhtml)
			Ratingtext = _("no user rating yet")
			if rating:
				Ratingtext = rating.group("g_rating") + ": " + rating.group("rating") + " / 10"
				self.ratingstars = int(10*round(float(rating.group("rating").replace(',','.')),1))
				self["stars"].show()
				self["stars"].setValue(self.ratingstars)
				self["starsbg"].show()
			self["ratinglabel"].setText(Ratingtext)
			castmask = re.compile('<td class="nm">.*?>(.*?)</a>.*?<td class="char">(?:<a.*?>)?(.*?)(?:</a>)?</td>', re.DOTALL)
			castresult = castmask.finditer(self.inhtml)
			if castresult:
				Casttext = ""
				for x in castresult:
					Casttext += "\n" + self.htmltags.sub('', x.group(1))
					if x.group(2):
						Casttext += _(" as ") + self.htmltags.sub('', x.group(2).replace('/ ...',''))
				if Casttext is not "":
					Casttext = _("Cast: ") + Casttext
				else:
					Casttext = _("No cast list found in the database.")
				self["castlabel"].setText(Casttext)
			postermask = re.compile('<div class="photo">.*?<img .*? src=\"(http.*?)\" .*?>', re.DOTALL)
			posterurl = postermask.search(self.inhtml)
			if posterurl and posterurl.group(1).find("jpg") > 0:
				posterurl = posterurl.group(1)
				self["statusbar"].setText(_("Downloading Movie Poster: %s...") % (posterurl))
				localfile = "/tmp/poster.jpg"
				print "[IMDB] downloading poster " + posterurl + " to " + localfile
				downloadPage(posterurl,localfile).addCallback(self.IMDBPoster).addErrback(self.fetchFailed)
			else:
				self.IMDBPoster("kein Poster")
			extrainfos = self.extrainfomask.search(self.inhtml)

			if extrainfos:
				Extratext = "Extra Info\n"

				for category in ("tagline","outline","synopsis","keywords","awards","runtime","language","color","aspect","sound","cert","locations","company","trivia","goofs","quotes","connections"):
					if extrainfos.group('g_'+category):
						Extratext += extrainfos.group('g_'+category) + ": " + self.htmltags.sub('',extrainfos.group(category).replace("\n",'').replace("<br>",'\n')) + "\n"
				if extrainfos.group("g_comments"):
					Extratext += extrainfos.group("g_comments") + " [" + self.htmltags.sub('',extrainfos.group("commenter")) + "]: " + self.htmltags.sub('',extrainfos.group("comment").replace("\n",' ')) + "\n"

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
			self["poster"].instance.setPixmap(ptr.__deref__())
			self["poster"].show()

	def createSummary(self):
		return IMDbLCDScreen

class IMDbLCDScreen(Screen):
	skin = """
	<screen position="0,0" size="132,64" title="IMDB Plugin">
		<widget name="headline" position="4,0" size="128,22" font="Regular;20"/>
		<widget source="session.Event_Now" render="Label" position="6,26" size="120,34" font="Regular;14" >
			<convert type="EventName">Name</convert>
		</widget>
	</screen>"""

	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self["headline"] = Label(_("IMDb Plugin"))

def eventinfo(session, servicelist, **kwargs):
	ref = session.nav.getCurrentlyPlayingServiceReference()
	session.open(IMDBEPGSelection, ref)

def main(session, eventName="", **kwargs):
	session.open(IMDB, eventName)

def Plugins(**kwargs):
	try:
		return [PluginDescriptor(name="IMDb Details",
				description=_("Query details from the Internet Movie Database"),
				icon="imdb.png",
				where = PluginDescriptor.WHERE_PLUGINMENU,
				fnc = main),
				PluginDescriptor(name="IMDb Details",
				description=_("Query details from the Internet Movie Database"),
				where = PluginDescriptor.WHERE_EVENTINFO,
				fnc = eventinfo)
				]
	except AttributeError:
		wherelist = [PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU]
		return PluginDescriptor(name="IMDb Details",
				description=_("Query details from the Internet Movie Database"),
				icon="imdb.png",
				where = wherelist,
				fnc=main)	
