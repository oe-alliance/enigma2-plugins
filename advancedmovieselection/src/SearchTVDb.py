from __init__ import _
import datetime
import re
import os
import shutil
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from enigma import getDesktop, iServiceInformation, eTimer
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.GUIComponent import GUIComponent
from enigma import RT_WRAP, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, gFont, eListbox, eListboxPythonMultiContent
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Tools.Directories import pathExists
from enigma import ePicLoad
from Components.ProgressBar import ProgressBar
from os import environ
from Source.ServiceProvider import ServiceCenter
from Source.EventInformationTable import createEITtvdb
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN
from SearchTMDb import InfoLoadChoice
from Source.Globals import pluginPresent, SkinTools
from Source.MovieDB import tvdb, downloadCover
from Source.PicLoader import PicLoader
temp_dir = '/tmp/TheTVDB_temp/'
if environ['LANGUAGE'] == 'de' or environ['LANGUAGE'] == 'de_DE':
    nocover = resolveFilename(SCOPE_CURRENT_PLUGIN, 'Extensions/AdvancedMovieSelection/images/nocover_de.png')
else:
    nocover = resolveFilename(SCOPE_CURRENT_PLUGIN, 'Extensions/AdvancedMovieSelection/images/nocover_en.png')


def getImage(serie):
    thumb = serie['poster']
    if not thumb:
        thumb = serie['banner']
    if not thumb:
        thumb = serie['fanart']
    filename = None
    if thumb:
        thumb = thumb.encode('utf-8', 'ignore')
        filename = TheTVDBMain.htmlToFile(thumb)
        downloadCover(thumb, filename)
    if filename and os.path.exists(filename):
        return filename
    else:
        return nocover


class ListBase(GUIComponent, object):

    def __init__(self):
        GUIComponent.__init__(self)
        self.picloader = PicLoader(95, 138)

    def destroy(self):
        self.picloader.destroy()
        GUIComponent.destroy(self)

    GUI_WIDGET = eListbox

    def postWidgetCreate(self, instance):
        instance.setContent(self.l)

    def preWidgetRemove(self, instance):
        instance.setContent(None)

    def getCurrentIndex(self):
        return self.instance.getCurrentIndex()

    def setList(self, _list):
        self.list = _list
        self.l.setList(_list)

    def getCurrent(self):
        return self.l.getCurrentSelection()

    def getLength(self):
        return len(self.list)

    def moveSelectionTo(self, index):
        if index > -1:
            self.instance.moveSelectionTo(index)


class SeriesList(ListBase):

    def __init__(self):
        ListBase.__init__(self)
        self.l = eListboxPythonMultiContent()
        self.l.setBuildFunc(self.buildMovieSelectionListEntry)
        self.l.setFont(0, gFont('Regular', 24))
        self.l.setFont(1, gFont('Regular', 20))
        self.l.setItemHeight(140)

    def buildMovieSelectionListEntry(self, movie, series_id):
        width = self.l.getItemSize().width()
        res = [None]
        serie = movie['Serie'][0]
        desc = serie['Overview']
        if desc:
            desc_txt = desc.encode('utf-8', 'ignore')
        else:
            desc_txt = _('Sorry, no description found at www.thetvdb.com!')
        name = serie['SeriesName'].encode('utf-8', 'ignore')
        id_txt = _('ID: %s') % series_id.encode('utf-8', 'ignore')
        filename = getImage(serie)
        png = self.picloader.load(filename)
        res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST,
         0,
         1,
         95,
         138,
         png))
        res.append((eListboxPythonMultiContent.TYPE_TEXT,
         100,
         2,
         width - 250,
         26,
         0,
         RT_HALIGN_LEFT,
         '%s' % name))
        res.append((eListboxPythonMultiContent.TYPE_TEXT,
         width - 255,
         2,
         250,
         26,
         0,
         RT_HALIGN_RIGHT,
         '%s' % id_txt))
        res.append((eListboxPythonMultiContent.TYPE_TEXT,
         100,
         40,
         width - 100,
         95,
         1,
         RT_HALIGN_LEFT | RT_WRAP,
         '%s' % desc_txt))
        return res


class EpisodesList(ListBase):

    def __init__(self):
        ListBase.__init__(self)
        self.l = eListboxPythonMultiContent()
        self.l.setBuildFunc(self.buildMovieSelectionListEntry)
        self.l.setFont(0, gFont('Regular', 20))
        self.l.setFont(1, gFont('Regular', 17))
        self.l.setItemHeight(140)

    def buildMovieSelectionListEntry(self, episode, episode_name, episode_number, episode_season_number, episode_id, episode_overview):
        width = self.l.getItemSize().width()
        res = [None]
        id_txt = _('ID: %s') % episode_id
        season = _('Season: %s') % episode_season_number
        episode_txt = _('Episode: %s') % episode_number
        res.append((eListboxPythonMultiContent.TYPE_TEXT,
         5,
         2,
         width - 250,
         23,
         0,
         RT_HALIGN_LEFT,
         '%s' % episode_name))
        res.append((eListboxPythonMultiContent.TYPE_TEXT,
         width - 255,
         2,
         250,
         23,
         0,
         RT_HALIGN_RIGHT,
         '%s' % id_txt))
        res.append((eListboxPythonMultiContent.TYPE_TEXT,
         5,
         27,
         width - 250,
         23,
         0,
         RT_HALIGN_LEFT,
         '%s' % season))
        res.append((eListboxPythonMultiContent.TYPE_TEXT,
         width - 255,
         26,
         250,
         23,
         0,
         RT_HALIGN_RIGHT,
         '%s' % episode_txt))
        res.append((eListboxPythonMultiContent.TYPE_TEXT,
         5,
         52,
         width - 5,
         79,
         1,
         RT_HALIGN_LEFT | RT_WRAP,
         '%s' % episode_overview))
        return res


class TheTVDBMain(Screen, InfoLoadChoice):
    SHOW_DETAIL_TEXT = _('Show serie detail')
    SHOW_EPISODE_TEXT = _('Show episode detail')
    SHOW_ALL_EPISODES_TEXT = _('Show episodes overview')
    SHOW_ALL_SERIES_TEXT = _('Show search result')
    MANUAL_SEARCH_TEXT = _('Manual search')
    INFO_SAVE_TEXT = _('Info/Cover save')
    TRAILER_SEARCH_TEXT = _('Trailer search')
    SHOW_SERIE_NO_RESULT = 0
    SHOW_SERIE_LIST = 1
    SHOW_SERIE_DETAIL = 2
    SHOW_EPISODE_NO_RESULT = 3
    SHOW_EPISODE_LIST = 4
    SHOW_EPISODE_DETAIL = 5
    SHOW_SEARCH = 6

    def __init__(self, session, service, eventName=None, shortDescription=None):
        Screen.__init__(self, session)
        InfoLoadChoice.__init__(self, self.callback_green_pressed)
        self.skinName = SkinTools.appendResolution('TheTVDBMain')
        if not pathExists(temp_dir):
            os.mkdir(temp_dir, 511)
        self['setupActions'] = ActionMap(['ColorActions',
         'DirectionActions',
         'SetupActions',
         'OkCancelActions'], {'exit': self.cancel,
         'ok': self.ok_pressed,
         'red': self.red_pressed,
         'green': self.green_pressed,
         'blue': self.blue_pressed,
         'yellow': self.yellow_pressed,
         'cancel': self.cancel,
         'upUp': self.pageUp,
         'leftUp': self.pageUp,
         'downUp': self.pageDown,
         'rightUp': self.pageDown})
        self.service = service
        self.ratingstars = -1
        self.searchTitle = eventName
        self.description = shortDescription
        if service is not None:
            info = ServiceCenter.getInstance().info(service)
            self.searchTitle = info.getName(service)
            self.description = info.getInfoString(service, iServiceInformation.sDescription)
        print('[tvdb] %s-%s' % (str(self.searchTitle), str(self.description)))
        if self.description == self.searchTitle:
            self.description = ''
        self.picload = ePicLoad()
        self.picload.PictureData.get().append(self.paintPosterPixmapCB)
        self.picload2 = ePicLoad()
        self.picload2.PictureData.get().append(self.paintBannerPixmapCB)
        self['cover'] = Pixmap()
        self['banner'] = Pixmap()
        self['stars'] = ProgressBar()
        self['no_stars'] = Pixmap()
        self['description'] = ScrollLabel('')
        self['description_episode'] = ScrollLabel('')
        self['extended'] = Label('')
        self['extended_episode'] = Label('')
        self['status'] = Label('')
        self['result_txt'] = Label('')
        self['voted'] = Label('')
        self['list'] = SeriesList()
        self['episodes_list'] = EpisodesList()
        self['seperator'] = Pixmap()
        self['thetvdb_logo'] = Pixmap()
        self['button_red'] = Pixmap()
        self['button_green'] = Pixmap()
        self['button_yellow'] = Pixmap()
        self['button_blue'] = Pixmap()
        self['key_red'] = StaticText('')
        self['key_green'] = StaticText('')
        self['key_yellow'] = StaticText('')
        self['key_blue'] = StaticText('')
        self.timer = eTimer()
        self.timer.callback.append(self.getSeriesList)
        self.red_button_timer = eTimer()
        self.red_button_timer.callback.append(self.callback_red_pressed)
        self.blue_button_timer = eTimer()
        self.blue_button_timer.callback.append(self.callback_blue_pressed)
        self.onLayoutFinish.append(self.layoutFinished)
        self.onClose.append(self.deleteTempDir)
        self.view_mode = self.SHOW_SEARCH
        self.updateView()
        self.startSearch()

    def layoutFinished(self):
        self['thetvdb_logo'].instance.setPixmapFromFile(resolveFilename(SCOPE_CURRENT_PLUGIN, 'Extensions/AdvancedMovieSelection/images/thetvdb_logo.png'))
        self.picload.setPara((self['cover'].instance.size().width(),
         self['cover'].instance.size().height(),
         1,
         1,
         False,
         1,
         '#ff000000'))
        self.picload2.setPara((self['banner'].instance.size().width(),
         self['banner'].instance.size().height(),
         1,
         1,
         False,
         1,
         '#ff000000'))

    def startSearch(self):
        self.updateView(self.SHOW_SEARCH)
        self.setTitle(_('TheTVDB Info & D/L'))
        self['status'].setText(_("Searching for ' %s ' on TheTVDB.com, please wait ...") % self.searchTitle)
        self['status'].show()
        self.timer.start(100, True)

    def pageUp(self):
        self['description'].pageUp()
        self['description_episode'].pageUp()

    def pageDown(self):
        self['description'].pageDown()
        self['description_episode'].pageDown()

    def deleteTempDir(self):
        del self.picload
        del self.picload2
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print('[AdvancedMovieSelection] ERROR deleting: %s / %s' % (temp_dir, str(e)))

    def cancel(self):
        self.close(False)

    def getInfoText(self):
        if self.description != '' and self.description != self.searchTitle:
            return self.searchTitle + ' - ' + self.description
        else:
            return self.searchTitle

    def getSeriesList(self):
        searchTitle = self.searchTitle
        tmpList = []
        try:
            results = tvdb.search(searchTitle)
            if len(results) > 0:
                for searchResult in results:
                    movie = tvdb.getMovieInfo(searchResult['id'])
                    _id = movie['Serie'][0]['id']
                    tmpList.append((movie, _id))

        except Exception as e:
            print(str(e))

        if len(tmpList) > 0:
            self['list'].setList(tmpList)
            self.showSeriesList()
        elif ' - ' in searchTitle:
            self.searchTitle = searchTitle.split(' - ')[0].strip()
            self.getSeriesList()
        else:
            self.updateView(self.SHOW_SERIE_NO_RESULT)
            self['status'].setText(_('Sorry, no data found at TheTVDB.com!'))
            self['status'].show()
            self['thetvdb_logo'].show()
            self['result_txt'].setText('')
            self['result_txt'].hide()
            self['seperator'].show()
            self['key_yellow'].setText(self.MANUAL_SEARCH_TEXT)
            self['button_yellow'].show()

    def showSeriesList(self):
        self.updateView(self.SHOW_SERIE_LIST)
        count = self['list'].getLength()
        if count == 1:
            txt = _('Total %s') % count + ' ' + _('show found')
        else:
            txt = _('Total %s') % count + ' ' + _('shows found')
        self['result_txt'].setText(txt)

    def showEpisodeList(self, movie):
        searchTitle = self.searchTitle
        self.setTitle(_('Episodes for: %s') % self.getInfoText())
        results = tvdb.search(searchTitle)
        tmpEpisodeList = []
        episodeIndex = -1
        if len(results) > 0:
            try:
                for episode in movie['Episode']:
                    episode_name = ''
                    name = episode['EpisodeName']
                    if name:
                        episode_name = name.encode('utf-8', 'ignore')
                    episode_number = episode['EpisodeNumber']
                    if episode_number:
                        episode_number = episode_number.encode('utf-8', 'ignore')
                    season_number = episode['SeasonNumber']
                    if season_number:
                        episode_season_number = season_number.encode('utf-8', 'ignore')
                    id_txt = episode['id']
                    if id_txt:
                        episode_id = id_txt.encode('utf-8', 'ignore')
                    episode_overview = ''
                    overview = episode['Overview']
                    if overview:
                        episode_overview = str(overview).encode('utf-8', 'ignore')
                    else:
                        episode_overview = _('Sorry, no description for this episode at TheTVDB.com available!')
                    if episode_name != '' and self.description != '':
                        if episode_name == self.description:
                            episodeIndex = len(tmpEpisodeList)
                    tmpEpisodeList.append((episode,
                     episode_name,
                     episode_number,
                     episode_season_number,
                     episode_id,
                     episode_overview))

            except Exception as e:
                print(str(e))

        if len(tmpEpisodeList) > 0:
            self.updateView(self.SHOW_EPISODE_LIST)
            self['episodes_list'].setList(tmpEpisodeList)
            self['episodes_list'].moveSelectionTo(episodeIndex)
            if len(tmpEpisodeList) == 1:
                txt = _('Total %s') % len(tmpEpisodeList) + ' ' + _('episode found')
            else:
                txt = _('Total %s') % len(tmpEpisodeList) + ' ' + _('episodes found')
            self['result_txt'].setText(txt)
        else:
            self.updateView(self.SHOW_EPISODE_NO_RESULT)

    def showEpisodeDetails(self, movie):
        if movie:
            if movie['EpisodeName']:
                name = movie['EpisodeName'].encode('utf-8', 'ignore')
                self.setTitle(_('Episode details for: %s') % (name + ' / ' + self.searchTitle))
            else:
                self.setTitle(_('Sorry, no episode titel available!'))
            try:
                overview = movie['Overview']
                if overview:
                    overview = str(overview).encode('utf-8', 'ignore')
                else:
                    overview = _('Sorry, no description for this episode at TheTVDB.com available!')
                extended = ''
                director = movie['Director']
                if director:
                    director = director.replace('|', ', ')
                    extended = _('Regie: %s') % director.encode('utf-8', 'ignore') + ' / '
                writer = movie['Writer']
                if writer:
                    writer = writer.replace('|', ', ')
                    extended += _('Writer: %s\n') % writer.encode('utf-8', 'ignore')
                guest_stars = movie['GuestStars']
                if guest_stars:
                    if guest_stars.startswith('|'):
                        guest_stars = guest_stars[1:-1].replace('|', ', ')
                    else:
                        guest_stars = guest_stars.replace('|', ', ')
                    extended += _('Guest Stars: %s\n') % guest_stars.encode('utf-8', 'ignore')
                first_aired = movie['FirstAired']
                if first_aired:
                    extended += _('First Aired: %s') % first_aired.encode('utf-8', 'ignore')
                image = movie['filename']
                if image:
                    cover_file = self.downloadBanner(image)
                    self.setBanner(cover_file)
                else:
                    cover_file = ''
                    self.setBanner(cover_file)
                self['description_episode'].setText(overview)
                self['extended_episode'].setText(extended)
                self.updateView(self.SHOW_EPISODE_DETAIL)
            except Exception as e:
                print(str(e))
                self.updateView(self.SHOW_EPISODE_NO_RESULT)

    def searchManual(self):
        from AdvancedKeyboard import AdvancedKeyBoard
        self.session.openWithCallback(self.newSearchCallback, AdvancedKeyBoard, title=_('Enter new movie name for search:'), text=self.searchTitle)

    def newSearchCallback(self, text=None):
        if text:
            self.searchTitle = text
            self.startSearch()

    def showSeriesDetails(self, movie):
        serie = movie['Serie'][0]
        try:
            self.updateView(self.SHOW_SERIE_DETAIL)
            overview = serie['Overview']
            if overview:
                overview = overview.encode('utf-8', 'ignore')
            else:
                overview = _("Sorry, no description for ' %s ' at TheTVDB.com found!") % self.name
            cover_file = self.downloadCover(serie)
            self.setPoster(cover_file)
            self['description'].setText(overview)
            extended = ''
            first_aired = TheTVDBMain.convert_date(serie['FirstAired'])
            if first_aired:
                extended = _('First Aired: %s') % first_aired + ' / '
            airs_day = serie['Airs_DayOfWeek']
            if airs_day:
                extended += _('Air Day: %s') % airs_day.encode('utf-8', 'ignore') + ' / '
            else:
                extended += ''
            airs_time = TheTVDBMain.convert_time(serie['Airs_Time'])
            if airs_time:
                extended += _('Air Time: %s') % airs_time + ' / '
            runtime = serie['Runtime']
            if runtime:
                extended += _('Runtime: %s minutes\n') % runtime.encode('utf-8', 'ignore')
            network = serie['Network']
            if network:
                extended += _('Broadcast TV network: %s') % network.encode('utf-8', 'ignore') + ' / '
            else:
                extended += ''
            if serie['Genre']:
                genre = ' ,'.join(serie['Genre'])
                extended += _('Genre: %s\n') % str(genre).encode('utf-8', 'ignore')
            content_rating = serie['ContentRating']
            if content_rating:
                extended += _('Certification: %s') % content_rating.encode('utf-8', 'ignore') + ' / '
            rating = serie['Rating']
            if rating:
                rating = rating.encode('utf-8', 'ignore')
                self.ratingstars = int(10 * round(float(rating.replace(',', '.')), 1))
                self['stars'].show()
                self['stars'].setValue(self.ratingstars)
                self['no_stars'].show()
                extended += _('Rating: %s\n') % rating
            if serie['Actors']:
                genre = ' ,'.join(serie['Actors']).encode('utf-8', 'ignore')
                extended += _('Actors: %s\n') % genre
            last_updated = serie['lastupdated']
            if last_updated is not None:
                last_updated = datetime.datetime.fromtimestamp(int(last_updated))
                extended += _('\nLast modified at TheTVDB.com: %s') % last_updated
            if extended:
                self['extended'].setText(extended)
            user_rating = serie['RatingCount']
            if user_rating:
                self['voted'].setText(_('Voted: %s') % user_rating.encode('utf-8', 'ignore') + ' ' + _('times'))
            else:
                self['voted'].setText(_('No user voted!'))
        except Exception as e:
            print(str(e))
            self.updateView(self.SHOW_SERIE_NO_RESULT)

    def downloadBanner(self, image):
        if image:
            filename = self.htmlToFile(image)
            downloadCover(image, filename)
            return filename

    def setBanner(self, filename):
        if not filename or not os.path.exists(filename):
            filename = nocover
        self.picload2.startDecode(filename)

    def paintBannerPixmapCB(self, picInfo=None):
        ptr = self.picload2.getData()
        if ptr is not None:
            self['banner'].instance.setPixmap(ptr)
            self['banner'].show()

    def downloadCover(self, serie):
        thumb = serie['poster']
        if thumb:
            filename = self.htmlToFile(thumb)
            downloadCover(thumb, filename)
            return filename

    def setPoster(self, filename):
        if not filename or not os.path.exists(filename):
            filename = nocover
        self.picload.startDecode(filename)

    def paintPosterPixmapCB(self, picInfo=None):
        ptr = self.picload.getData()
        if ptr is not None:
            self['cover'].instance.setPixmap(ptr)
            self['cover'].show()

    @staticmethod
    def convert_time(time_string):
        """Convert a thetvdb time string into a datetime.time object."""
        time_res = [re.compile('\\D*(?P<hour>\\d{1,2})(?::(?P<minute>\\d{2}))?.*(?P<ampm>a|p)m.*', re.IGNORECASE), re.compile('\\D*(?P<hour>\\d{1,2}):?(?P<minute>\\d{2}).*')]
        for r in time_res:
            m = r.match(time_string.encode('utf-8', 'ignore'))
            if m:
                gd = m.groupdict()
                if 'hour' in gd and 'minute' in gd and gd['minute'] and 'ampm' in gd:
                    hour = int(gd['hour'])
                    if gd['ampm'].lower() == 'p':
                        hour += 12
                    return datetime.time(hour, int(gd['minute']))
                if 'hour' in gd and 'ampm' in gd:
                    hour = int(gd['hour'])
                    if gd['ampm'].lower() == 'p':
                        hour += 12
                    return datetime.time(hour, 0)
                if 'hour' in gd and 'minute' in gd:
                    return datetime.time(int(gd['hour']), int(gd['minute']))

    @staticmethod
    def convert_date(date_string):
        """Convert a thetvdb date string into a datetime.date object."""
        first_aired = None
        try:
            first_aired = datetime.date(*map(int, date_string.encode('utf-8', 'ignore').split('-')))
        except Exception as e:
            print(str(e))

        return first_aired

    @staticmethod
    def htmlToFile(address):
        if address:
            return temp_dir + address.split('/')[-1]

    def checkConnection(self):
        try:
            import socket
            print(socket.gethostbyname('www.google.com'))
            return True
        except:
            self.session.openWithCallback(self.close, MessageBox, _('No internet connection available!'), MessageBox.TYPE_ERROR)
            return False

    def hideAll(self):
        self['cover'].hide()
        self['banner'].hide()
        self['stars'].hide()
        self['no_stars'].hide()
        self['description'].hide()
        self['description_episode'].hide()
        self['extended'].hide()
        self['extended_episode'].hide()
        self['status'].hide()
        self['result_txt'].hide()
        self['voted'].hide()
        self['list'].hide()
        self['episodes_list'].hide()
        self['seperator'].hide()
        self['thetvdb_logo'].hide()
        self['button_red'].hide()
        self['button_green'].hide()
        self['button_yellow'].hide()
        self['button_blue'].hide()

    def serieDetailView(self):
        self.setTitle(_('Details for: %s') % self.getInfoText())
        self.hideAll()
        self['seperator'].show()
        self['description'].show()
        self['extended'].show()
        self['voted'].show()

    def episodeDetailView(self):
        self.hideAll()
        self['seperator'].show()
        self['banner'].show()
        self['description_episode'].show()
        self['extended_episode'].show()

    def serieListView(self):
        self.setTitle(_('Search result for: %s') % self.getInfoText())
        self.hideAll()
        self['seperator'].show()
        self['thetvdb_logo'].show()
        self['result_txt'].show()
        self['list'].show()

    def episodeListView(self):
        self.hideAll()
        self['seperator'].show()
        self['thetvdb_logo'].show()
        self['result_txt'].show()
        self['episodes_list'].show()

    def updateView(self, mode=None):
        if mode:
            self.view_mode = mode
        if self.view_mode == self.SHOW_SERIE_NO_RESULT or self.view_mode == self.SHOW_EPISODE_NO_RESULT:
            self.hideAll()
            self['key_red'].setText('')
            self['key_green'].setText('')
            self['key_blue'].setText('')
        elif self.view_mode == self.SHOW_SERIE_LIST:
            self.serieListView()
            self['key_red'].setText(self.SHOW_DETAIL_TEXT)
            self['key_green'].setText(self.INFO_SAVE_TEXT if self.service is not None else '')
            self['key_yellow'].setText(self.MANUAL_SEARCH_TEXT)
            self['key_blue'].setText(self.SHOW_ALL_EPISODES_TEXT)
            self['button_red'].show()
            self['button_green'].show()
            self['button_yellow'].show()
            self['button_blue'].show()
        elif self.view_mode == self.SHOW_SERIE_DETAIL:
            self.serieDetailView()
            if pluginPresent.YTTrailer:
                self['key_red'].setText(self.TRAILER_SEARCH_TEXT)
                self['button_red'].show()
            else:
                self['key_red'].setText('')
                self['button_red'].hide()
            self['key_green'].setText(self.INFO_SAVE_TEXT if self.service is not None else '')
            self['key_yellow'].setText(self.MANUAL_SEARCH_TEXT)
            self['key_blue'].setText(self.SHOW_ALL_EPISODES_TEXT)
            self['button_green'].show()
            self['button_yellow'].show()
            self['button_blue'].show()
        elif self.view_mode == self.SHOW_EPISODE_LIST:
            self.episodeListView()
            self['key_red'].setText(self.SHOW_ALL_SERIES_TEXT)
            self['key_green'].setText(self.INFO_SAVE_TEXT if self.service is not None else '')
            self['key_yellow'].setText(self.MANUAL_SEARCH_TEXT)
            self['key_blue'].setText(self.SHOW_EPISODE_TEXT)
            self['button_red'].show()
            self['button_green'].show()
            self['button_yellow'].show()
            self['button_blue'].show()
        elif self.view_mode == self.SHOW_EPISODE_DETAIL:
            self.episodeDetailView()
            self['key_red'].setText(self.SHOW_ALL_SERIES_TEXT)
            self['key_green'].setText(self.INFO_SAVE_TEXT if self.service is not None else '')
            self['key_yellow'].setText(self.MANUAL_SEARCH_TEXT)
            self['key_blue'].setText(self.SHOW_ALL_EPISODES_TEXT)
            self['button_red'].show()
            self['button_green'].show()
            self['button_yellow'].show()
            self['button_blue'].show()
        elif self.view_mode == self.SHOW_SEARCH:
            self.hideAll()
            self['key_red'].setText('')
            self['key_green'].setText('')
            self['key_yellow'].setText('')
            self['key_blue'].setText('')
            self['thetvdb_logo'].show()

    def ok_pressed(self):
        cur_serie = self['list'].getCurrent()
        cur_episode = self['episodes_list'].getCurrent()
        if self.view_mode == self.SHOW_SERIE_LIST and cur_serie:
            self.showSeriesDetails(cur_serie[0])
        elif self.view_mode == self.SHOW_EPISODE_LIST and cur_episode:
            self.showEpisodeDetails(cur_episode[0])
        elif self.view_mode == self.SHOW_EPISODE_DETAIL and cur_episode:
            self.showEpisodeList(cur_serie[0])
        elif self.view_mode == self.SHOW_SERIE_DETAIL:
            self.showSeriesList()

    def buttonAction(self, text):
        if text == self.TRAILER_SEARCH_TEXT:
            if pluginPresent.YTTrailer:
                self.setTitle(_('Details for: %s') % self.getInfoText())
                from Plugins.Extensions.YTTrailer.plugin import YTTrailerList
                self.session.open(YTTrailerList, self.searchTitle)
        elif text == self.SHOW_ALL_SERIES_TEXT:
            self.showSeriesList()
        elif text == self.SHOW_ALL_EPISODES_TEXT:
            cur = self['list'].getCurrent()
            self.showEpisodeList(cur[0])
        elif text == self.SHOW_DETAIL_TEXT:
            cur = self['list'].getCurrent()
            self.showSeriesDetails(cur[0])
        elif text == self.SHOW_EPISODE_TEXT:
            cur = self['episodes_list'].getCurrent()
            self.showEpisodeDetails(cur[0])

    def yellow_pressed(self):
        self.searchManual()

    def green_pressed(self):
        if self.service is None:
            return
        self.setTitle(_("Save Info/Cover for ' %s ', please wait ...") % self.searchTitle)
        self.checkExistEnce(self.service.getPath())

    def callback_green_pressed(self, answer=None):
        cur = self['list'].getCurrent()
        if not self.checkConnection() or not cur:
            return
        overwrite_eit, overwrite_jpg = answer and answer[1] or (False, False)
        current_movie = cur[0]['Serie'][0]
        title = current_movie['SeriesName'].encode('utf-8', 'ignore')
        episode = None
        cur_epi = self['episodes_list'].getCurrent()
        if cur_epi and (self.view_mode == self.SHOW_EPISODE_LIST or self.view_mode == self.SHOW_EPISODE_DETAIL):
            episode = cur_epi[0]
        if self.service is not None:
            createEITtvdb(self.service.getPath(), title, serie=current_movie, episode=episode, overwrite_jpg=overwrite_jpg, overwrite_eit=overwrite_eit)
            self.close(False)

    def red_pressed(self):
        text = self['key_red'].getText()
        if text == self.SHOW_DETAIL_TEXT:
            self.setTitle(_("Getting show details for ' %s ', please wait ...") % self.getInfoText())
        elif text == self.TRAILER_SEARCH_TEXT:
            self.setTitle(_("Search trailer for ' %s ', please wait ...") % self.getInfoText())
        elif text == self.SHOW_ALL_SERIES_TEXT:
            self.setTitle(_("Getting search result for ' %s ', please wit ...") % self.getInfoText())
        self.red_button_timer.start(100, True)

    def callback_red_pressed(self):
        text = self['key_red'].getText()
        self.buttonAction(text)

    def blue_pressed(self):
        text = self['key_blue'].getText()
        if text == self.SHOW_ALL_EPISODES_TEXT:
            self.setTitle(_("Getting episodes list for ' %s ', please wait ...") % self.getInfoText())
        elif text == self.SHOW_EPISODE_TEXT:
            cur_episode = self['episodes_list'].getCurrent()
            name = cur_episode[1]
            self.setTitle(_("Getting episodes details for ' %s ', please wait ...") % name)
        self.blue_button_timer.start(100, True)

    def callback_blue_pressed(self):
        text = self['key_blue'].getText()
        self.buttonAction(text)
