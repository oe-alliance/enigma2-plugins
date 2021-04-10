############################################################################
#    Copyright (C) 2008 by Volker Christian                                #
#    Volker.Christian@fh-hagenberg.at                                      #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

from Screens.Screen import Screen

from Components.config import config
from Components.config import Config
from Components.config import ConfigSelection
from Components.config import ConfigText
from Components.config import getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Button import Button

from ConfigTextWithSuggestions import ConfigTextWithSuggestions

from . import _

searchContext = Config()
searchContext.searchTerm = ConfigTextWithSuggestions("", False, threaded=True)
searchContext.orderBy = ConfigSelection(
				[
				 ("relevance", _("Relevance")),
				 ("viewCount", _("View Count")),
				 ("published", _("Published")),
				 ("rating", _("Rating"))
				], "relevance")
searchContext.time = ConfigSelection(
				[
				 ("all_time", _("All Time")),
				 ("this_month", _("This Month")),
				 ("this_week", _("This Week")),
				 ("today", _("Today"))
				], "all_time")
searchContext.racy = ConfigSelection(
				[
				 ("include", _("Yes")),
				 ("exclude", _("No"))
				], "exclude")
searchContext.categories = ConfigSelection(
				[
				 (None, _("All")),
				 ("Autos", _("Autos & Vehicles")),
				 ("Music", _("Music")),
				 ("Animals", _("Pets & Animals")),
				 ("Sports", _("Sports")),
				 ("Travel", _("Travel & Events")),
				 ("Shortmov", _("Short Movies")),
				 ("Games", _("Gaming")),
				 ("Comedy", _("Comedy")),
				 ("People", _("People & Blogs")),
				 ("News", _("News & Politics")),
				 ("Entertainment", _("Entertainment")),
				 ("Education", _("Education")),
				 ("Howto", _("Howto & Style")),
				 ("Nonprofit", _("Nonprofits & Activism")),
				 ("Tech", _("Science & Technology")),
				 ("Movies_Anime_animation", _("Movies - Anime/Animation")),
				 ("Movies", _("Movies")),
				 ("Movies_Comedy", _("Moview - Comedy")),
				 ("Movies_Documentary", _("Movies - Documentary")),
				 ("Movies_Action_adventure", _("Movies - Action/Adventure")),
				 ("Movies_Classics", _("Movies - Classics")),
				 ("Movies_Foreign", _("Movies - Foreign")),
				 ("Movies_Horror", _("Movies - Horror")),
				 ("Movies_Drama", _("Movies - Drama")),
				 ("Movies_Family", _("Movies - Family")),
				 ("Movies_Shorts", _("Movies - Shorts")),
				 ("Movies_Sci_fi_fantasy", _("Movies - Sci-Fi/Fantasy")),
				 ("Movies_Thriller", _("Movies - Thriller"))
				], None)
searchContext.lr = ConfigSelection(
				[
				 (None, _("All")),
				 ("om", _("Afan (Oromo)")),
				 ("ab", _("Abkhazian")),
				 ("aa", _("Afar")),
				 ("af", _("Afrikaans")),
				 ("sq", _("Albanian")),
				 ("am", _("Amharic")),
				 ("ar", _("Arabic")),
				 ("hy", _("Armenian")),
				 ("as", _("Assamese")),
				 ("ay", _("Aymara")),
				 ("az", _("Azerbaijani")),
				 ("ba", _("Bashkir")),
				 ("eu", _("Basque")),
				 ("bn", _("Bengali")),
				 ("dz", _("Bhutani")),
				 ("bh", _("Bihari")),
				 ("bi", _("Bislama")),
				 ("br", _("Breton")),
				 ("bg", _("Bulgarian")),
				 ("my", _("Burmese")),
				 ("be", _("Byelorussian")),
				 ("km", _("Cambodian")),
				 ("ca", _("Catalan")),
				 ("zh", _("Chinese")),
				 ("co", _("Corsican")),
				 ("hr", _("Croatian")),
				 ("cs", _("Czech")),
				 ("da", _("Danish")),
				 ("nl", _("Dutch")),
				 ("en", _("English")),
				 ("eo", _("Esperanto")),
				 ("et", _("Estonian")),
				 ("fo", _("Faeroese")),
				 ("fj", _("Fiji")),
				 ("fi", _("Finnish")),
				 ("fr", _("French")),
				 ("fy", _("Frisian")),
				 ("gl", _("Galician")),
				 ("ka", _("Georgian")),
				 ("de", _("German")),
				 ("el", _("Greek")),
				 ("kl", _("Greenlandic")),
				 ("gn", _("Guarani")),
				 ("gu", _("Gujarati")),
				 ("ha", _("Hausa")),
				 ("he", _("Hebrew")),
				 ("hi", _("Hindi")),
				 ("hu", _("Hungarian")),
				 ("is", _("Icelandic")),
				 ("id", _("Indonesian")),
				 ("ia", _("Interlingua")),
				 ("ie", _("Interlingue")),
				 ("ik", _("Inupiak")),
				 ("iu", _("Inuktitut (Eskimo)")),
				 ("ga", _("Irish")),
				 ("it", _("Italian")),
				 ("ja", _("Japanese")),
				 ("jw", _("Javanese")),
				 ("kn", _("Kannada")),
				 ("ks", _("Kashmiri")),
				 ("kk", _("Kazakh")),
				 ("rw", _("Kinyarwanda")),
				 ("ky", _("Kirghiz")),
				 ("rn", _("Kirundi")),
				 ("ko", _("Korean")),
				 ("ku", _("Kurdish")),
				 ("lo", _("Laothian")),
				 ("la", _("Latin")),
				 ("lv", _("Latvian")),
				 ("ln", _("Lingala")),
				 ("lt", _("Lithuanian")),
				 ("mk", _("Macedonian")),
				 ("mg", _("Malagasy")),
				 ("ms", _("Malay")),
				 ("ml", _("Malayalam")),
				 ("mt", _("Maltese")),
				 ("mi", _("Maori")),
				 ("mr", _("Marathi")),
				 ("mo", _("Moldavian")),
				 ("mn", _("Mongolian")),
				 ("na", _("Nauru")),
				 ("ne", _("Nepali")),
				 ("no", _("Norwegian")),
				 ("oc", _("Occitan")),
				 ("or", _("Oriya")),
				 ("ps", _("Pashto")),
				 ("fa", _("Persian")),
				 ("pl", _("Polish")),
				 ("pt", _("Portuguese")),
				 ("pa", _("Punjabi")),
				 ("qu", _("Quechua")),
				 ("rm", _("Rhaeto-Romance")),
				 ("ro", _("Romanian")),
				 ("ru", _("Russian")),
				 ("sm", _("Samoan")),
				 ("sg", _("Sangro")),
				 ("sa", _("Sanskrit")),
				 ("gd", _("Scots Gaelic")),
				 ("sr", _("Serbian")),
				 ("sh", _("Serbo-Croatian")),
				 ("st", _("Sesotho")),
				 ("tn", _("Setswana")),
				 ("sn", _("Shona")),
				 ("sd", _("Sindhi")),
				 ("si", _("Singhalese")),
				 ("ss", _("Siswati")),
				 ("sk", _("Slovak")),
				 ("sl", _("Slovenian")),
				 ("so", _("Somali")),
				 ("es", _("Spanish")),
				 ("su", _("Sudanese")),
				 ("sw", _("Swahili")),
				 ("sv", _("Swedish")),
				 ("tl", _("Tagalog")),
				 ("tg", _("Tajik")),
				 ("ta", _("Tamil")),
				 ("tt", _("Tatar")),
				 ("te", _("Tegulu")),
				 ("th", _("Thai")),
				 ("bo", _("Tibetan")),
				 ("ti", _("Tigrinya")),
				 ("to", _("Tonga")),
				 ("ts", _("Tsonga")),
				 ("tr", _("Turkish")),
				 ("tk", _("Turkmen")),
				 ("tw", _("Twi")),
				 ("ug", _("Uigur")),
				 ("uk", _("Ukrainian")),
				 ("ur", _("Urdu")),
				 ("uz", _("Uzbek")),
				 ("vi", _("Vietnamese")),
				 ("vo", _("Volapuk")),
				 ("cy", _("Welch")),
				 ("wo", _("Wolof")),
				 ("xh", _("Xhosa")),
				 ("yi", _("Yiddish")),
				 ("yo", _("Yoruba")),
				 ("za", _("Zhuang")),
				 ("zu", _("Zulu")) 
				], None)
searchContext.sortOrder = ConfigSelection(
				[
				 ("ascending", _("Ascanding")),
				 ("descending", _("Descending"))
				], "ascending")


SEARCH = 1
STDFEEDS = 2
PLAYLISTS = 3
FAVORITES = 4
CANCEL = 5


class YouTubeSearchDialog(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)

		self.session = session

		self.propagateUpDownNormally = True
		
		self["actions"] = ActionMap(["YouTubeSearchDialogActions"],
		{
			"standard": self.keyStdFeeds,
			"search": self.keySearch,
			"playlists": self.keyPlaylists,
			"favorites": self.keyFavorites,

			"cancel": self.keyCancel,
			"left": self.keyLeft,
			"right": self.keyRight,
			"up": self.keyUp,
			"down": self.keyDown,
		}, -2)

		self["key_red"] = Button(_("Std.Feeds"))
		self["key_green"] = Button(_("Search"))
		self["key_yellow"] = Button(_("Playlists"))
		self["key_blue"] = Button(_("Favorites"))

		searchContextEntries = []
		searchContextEntries.append(getConfigListEntry(_("Search Term(s)"), searchContext.searchTerm))
		searchContextEntries.append(getConfigListEntry(_("Video Quality"), config.plugins.youtubeplayer.quality))
		searchContextEntries.append(getConfigListEntry(_("Order by"), searchContext.orderBy))
#		searchContextEntries.append(getConfigListEntry(_("Sort Order"), searchContext.sortOrder))
#		searchContextEntries.append(getConfigListEntry(_("Search Periode"), searchContext.time))
		searchContextEntries.append(getConfigListEntry(_("Restricted Content"), searchContext.racy))
		searchContextEntries.append(getConfigListEntry(_("Category"), searchContext.categories))
		searchContextEntries.append(getConfigListEntry(_("From Region"), searchContext.lr))

		ConfigListScreen.__init__(self, searchContextEntries, session)

	def keyOK(self):
		if isinstance(self["config"].getCurrent()[1], ConfigTextWithSuggestions):
			if not self.propagateUpDownNormally:
				self.propagateUpDownNormally = True
				self["config"].getCurrent()[1].deactivateSuggestionList()
			else:
				if self["config"].getCurrent()[1].activateSuggestionList():
					self.propagateUpDownNormally = False
			self["config"].invalidateCurrent()
		else:
			ConfigListScreen.keyOK(self)

	def keyUp(self):
		if self.propagateUpDownNormally:
			self["config"].instance.moveSelection(self["config"].instance.moveUp)
		else:
			self["config"].getCurrent()[1].suggestionListUp()
			self["config"].invalidateCurrent()

	def keyDown(self):
		if self.propagateUpDownNormally:
			self["config"].instance.moveSelection(self["config"].instance.moveDown)
		else:
			self["config"].getCurrent()[1].suggestionListDown()
			self["config"].invalidateCurrent()

	def keyRight(self):
		if self.propagateUpDownNormally:
			ConfigListScreen.keyRight(self)
		else:
			self["config"].getCurrent()[1].suggestionListPageDown()
			self["config"].invalidateCurrent()

	def keyLeft(self):
		if self.propagateUpDownNormally:
			ConfigListScreen.keyLeft(self)
		else:
			self["config"].getCurrent()[1].suggestionListPageUp()
			self["config"].invalidateCurrent()

	def keyCancel(self):
		if self.propagateUpDownNormally:
			self.close(CANCEL)
		else:
			self.propagateUpDownNormally = True
			self["config"].getCurrent()[1].cancelSuggestionList()
			self["config"].invalidateCurrent()

	def keySearch(self):
		if searchContext.searchTerm.value != "":
			if isinstance(self["config"].getCurrent()[1], ConfigTextWithSuggestions) and not self.propagateUpDownNormally:
				self.propagateUpDownNormally = True
				self["config"].getCurrent()[1].deactivateSuggestionList()
			self.close(SEARCH, searchContext)

	def keyStdFeeds(self):
		if isinstance(self["config"].getCurrent()[1], ConfigTextWithSuggestions) and not self.propagateUpDownNormally:
			self.propagateUpDownNormally = True
			self["config"].getCurrent()[1].deactivateSuggestionList()
		self.close(STDFEEDS)

	def keyPlaylists(self):
		if isinstance(self["config"].getCurrent()[1], ConfigTextWithSuggestions) and not self.propagateUpDownNormally:
			self.propagateUpDownNormally = True
			self["config"].getCurrent()[1].deactivateSuggestionList()
		self.close(PLAYLISTS)

	def keyFavorites(self):
		if isinstance(self["config"].getCurrent()[1], ConfigTextWithSuggestions) and not self.propagateUpDownNormally:
			self.propagateUpDownNormally = True
			self["config"].getCurrent()[1].deactivateSuggestionList()
		self.close(FAVORITES)
