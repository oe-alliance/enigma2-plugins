from __init__ import _
import shutil
import os
from enigma import RT_WRAP, RT_VALIGN_CENTER, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, gFont, eListbox, eListboxPythonMultiContent
from Components.GUIComponent import GUIComponent
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Components.ActionMap import HelpableActionMap
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from os import path as os_path, mkdir as os_mkdir
from enigma import ePicLoad, eTimer
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Screens.MessageBox import MessageBox
from Components.config import config
from Components.ProgressBar import ProgressBar
from os import environ
from Source.PicLoader import PicLoader
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN
from Screens.ChoiceBox import ChoiceBox
from Source.Globals import pluginPresent, SkinTools
from Source.MovieDB import tmdb, downloadCover
import datetime
IMAGE_TEMPFILE = '/tmp/TMDb_temp'
if environ['LANGUAGE'] == 'de' or environ['LANGUAGE'] == 'de_DE':
    nocover = resolveFilename(SCOPE_CURRENT_PLUGIN, 'Extensions/AdvancedMovieSelection/images/nocover_de.png')
else:
    nocover = resolveFilename(SCOPE_CURRENT_PLUGIN, 'Extensions/AdvancedMovieSelection/images/nocover_en.png')


class InfoChecker:
    INFO = 1
    COVER = 2
    BOTH = INFO | COVER

    def __init__(self):
        pass

    @classmethod
    def check(self, file_name):
        present = 0
        if InfoChecker.checkExtension(file_name, '.eit'):
            present |= InfoChecker.INFO
        if InfoChecker.checkExtension(file_name, '.jpg'):
            present |= InfoChecker.COVER
        return present

    @classmethod
    def checkExtension(self, file_name, ext):
        import os
        if not os.path.isdir(file_name):
            f_name = os.path.splitext(file_name)[0]
        else:
            f_name = file_name
        file_name = f_name + ext
        return os.path.exists(file_name)


class InfoLoadChoice:

    def __init__(self, callback):
        self.__callback = callback
        self.__timer = eTimer()
        self.__timer.callback.append(self.__timerCallback)

    def checkExistEnce(self, file_name):
        list = []
        present = InfoChecker.check(file_name)
        default = (False, False)
        if False:
            self.startTimer(default)
            return
        list.append((_('Only those, which are not available!'), default))
        if present & InfoChecker.BOTH == InfoChecker.BOTH:
            list.append((_('Overwrite both (description & cover)'), (True, True)))
        if present & InfoChecker.INFO:
            list.append((_('Overwrite movie description'), (True, False)))
        if present & InfoChecker.COVER:
            list.append((_('Overwrite movie cover'), (False, True)))
        if present & InfoChecker.BOTH != 0:
            self.session.openWithCallback(self.startTimer, ChoiceBox, title=_('Data already exists! Should anything be updated?'), list=list)
        else:
            self.__callback(('Default', default))

    def startTimer(self, answer):
        print('InfoLoadChoice %s' % answer)
        self.answer = answer
        self.__timer.start(100, True)

    def __timerCallback(self):
        self.__callback(self.answer)


class TMDbList(GUIComponent, object):

    def __init__(self):
        GUIComponent.__init__(self)
        self.l = eListboxPythonMultiContent()
        self.l.setBuildFunc(self.buildMovieSelectionListEntry)
        self.l.setFont(0, gFont('Regular', 20))
        self.l.setFont(1, gFont('Regular', 17))
        self.l.setItemHeight(140)
        self.picloader = PicLoader(92, 138)

    def destroy(self):
        self.picloader.destroy()
        GUIComponent.destroy(self)

    def buildMovieSelectionListEntry(self, movie):
        width = self.l.getItemSize().width()
        res = [None]
        try:
            name = movie.title
            overview = movie.overview
            released = None
            if isinstance(movie.releasedate, datetime.datetime):
                released = movie.releasedate.year
            cover_url = movie.poster_url
            if overview:
                overview = overview.encode('utf-8', 'ignore')
            else:
                overview = ''
            if released:
                released_text = released
            else:
                released_text = ''
            if not cover_url:
                png = self.picloader.load(nocover)
            else:
                parts = cover_url.split('/')
                filename = os_path.join(IMAGE_TEMPFILE, str(movie.id) + str(parts[-1]))
                print(filename)
                if downloadCover(cover_url, filename):
                    png = self.picloader.load(filename)
                else:
                    png = self.picloader.load(nocover)
            res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST,
             0,
             1,
             92,
             138,
             png))
            res.append((eListboxPythonMultiContent.TYPE_TEXT,
             100,
             5,
             width - 100,
             20,
             0,
             RT_HALIGN_LEFT | RT_VALIGN_CENTER,
             '%s' % name.encode('utf-8', 'ignore')))
            res.append((eListboxPythonMultiContent.TYPE_TEXT,
             width - 140,
             5,
             130,
             20,
             1,
             RT_HALIGN_RIGHT | RT_VALIGN_CENTER,
             '%s' % released_text))
            res.append((eListboxPythonMultiContent.TYPE_TEXT,
             100,
             30,
             width - 100,
             100,
             1,
             RT_WRAP,
             '%s' % overview))
        except:
            from Source.Globals import printStackTrace
            printStackTrace()

        return res

    GUI_WIDGET = eListbox

    def postWidgetCreate(self, instance):
        instance.setContent(self.l)

    def preWidgetRemove(self, instance):
        instance.setContent(None)

    def getCurrentIndex(self):
        return self.instance.getCurrentIndex()

    def setList(self, list):
        self.list = list
        self.l.setList(list)

    def getCurrent(self):
        return self.l.getCurrentSelection()

    def getLength(self):
        return len(self.list)

    def moveUp(self):
        self.instance.moveSelection(self.instance.moveUp)

    def moveDown(self):
        self.instance.moveSelection(self.instance.moveDown)


class TMDbMain(Screen, HelpableScreen, InfoLoadChoice):
    SHOW_DETAIL_TEXT = _('Show movie detail')
    SHOW_SEARCH_RESULT_TEXT = _('Show search result')
    MANUAL_SEARCH_TEXT = _('Manual search')
    INFO_SAVE_TEXT = _('Info/Cover save')
    TRAILER_SEARCH_TEXT = _('Trailer search')
    SHOW_SEARCH = 0
    SHOW_SEARCH_NO_RESULT = 1
    SHOW_RESULT_LIST = 2
    SHOW_MOVIE_DETAIL = 3

    def __init__(self, session, searchTitle, service=None):
        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
        InfoLoadChoice.__init__(self, self.callback_green_pressed)
        self.skinName = SkinTools.appendResolution('TMDbMain')
        self.service = service
        self.movies = []
        if not os_path.exists(IMAGE_TEMPFILE):
            os_mkdir(IMAGE_TEMPFILE)
        self['ColorActions'] = HelpableActionMap(self, 'ColorActions', {'red': (self.ok_pressed, _('Toggle detail and list view')),
         'green': (self.green_pressed, _('Save info/cover')),
         'yellow': (self.yellow_pressed, _('Manual search')),
         'blue': (self.blue_pressed, _('Trailer search'))}, -1)
        self['WizardActions'] = HelpableActionMap(self, 'WizardActions', {'ok': (self.ok_pressed, _('Toggle detail and list view')),
         'back': (self.cancel, _('Close')),
         'up': (self.moveUp, _('Move up')),
         'down': (self.moveDown, _('Move down'))}, -1)
        self['WizardActions2'] = HelpableActionMap(self, 'WizardActions', {'left': (self.left, _('Show previous cover')),
         'right': (self.right, _('Show next cover'))}, -1)
        self['ChannelSelectBaseActions'] = HelpableActionMap(self, 'ChannelSelectBaseActions', {'nextMarker': (self.right, _('Show next cover')),
         'prevMarker': (self.left, _('Show previous cover'))}, -1)
        self['list'] = TMDbList()
        self['tmdblogo'] = Pixmap()
        self['cover'] = Pixmap()
        self.picload = ePicLoad()
        self.picload.PictureData.get().append(self.paintCoverPixmapCB)
        self['description'] = ScrollLabel()
        self['extended'] = Label()
        self['status'] = Label()
        self['stars'] = ProgressBar()
        self['no_stars'] = Pixmap()
        self['vote'] = Label()
        self['result_txt'] = Label()
        self['seperator'] = Pixmap()
        self['button_red'] = Pixmap()
        self['button_green'] = Pixmap()
        self['button_yellow'] = Pixmap()
        self['button_blue'] = Pixmap()
        self['key_red'] = StaticText('')
        self['key_green'] = StaticText('')
        self['key_yellow'] = StaticText('')
        self['key_blue'] = StaticText('')
        self.ratingstars = -1
        self.searchTitle = searchTitle
        self.downloadItems = {}
        self.useTMDbInfoAsEventInfo = True
        self.timer = eTimer()
        self.timer.callback.append(self.searchForMovies)
        self.blue_button_timer = eTimer()
        self.blue_button_timer.callback.append(self.callback_blue_pressed)
        self.onClose.append(self.deleteTempDir)
        self.onLayoutFinish.append(self.layoutFinished)
        self.view_mode = self.SHOW_SEARCH
        self.tmdb3 = tmdb.init_tmdb3()
        self.updateView()
        self.startSearch()

    def layoutFinished(self):
        self['tmdblogo'].instance.setPixmapFromFile(resolveFilename(SCOPE_CURRENT_PLUGIN, 'Extensions/AdvancedMovieSelection/images/tmdb.png'))
        self.picload.setPara((self['cover'].instance.size().width(),
         self['cover'].instance.size().height(),
         1,
         1,
         False,
         1,
         '#ff000000'))

    def deleteTempDir(self):
        del self.picload
        try:
            shutil.rmtree(IMAGE_TEMPFILE)
        except Exception as e:
            print('[AdvancedMovieSelection] ERROR deleting: %s / %s' % (IMAGE_TEMPFILE, str(e)))

    def startSearch(self):
        self.updateView(self.SHOW_SEARCH)
        self.setTitle(_('TMDb Info & D/L'))
        self['status'].setText(_("Searching for ' %s ' on TMDb, please wait ...") % self.searchTitle)
        self['status'].show()
        self.timer.start(100, True)

    def cancel(self, retval=None):
        self.close(False)

    def searchForMovies(self):
        try:
            title = self.searchTitle
            results = self.tmdb3.searchMovie(title)
            if len(results) == 0 and ' - ' in self.searchTitle:
                title = self.searchTitle.split(' - ')[0].strip()
                results = self.tmdb3.searchMovie(title)
                if len(results) > 0:
                    self.searchTitle = title
            if len(results) == 0 and ' & ' in self.searchTitle:
                title = self.searchTitle.split(' & ')[0].strip()
                results = self.tmdb3.searchMovie(title)
                if len(results) > 0:
                    self.searchTitle = title
            if len(results) == 0 and self.searchTitle.endswith('.ts'):
                title = self.searchTitle[:-3]
                results = self.tmdb3.searchMovie(title)
                if len(results) > 0:
                    self.searchTitle = title
            print('[SerchTMDB] %s %s' % (title, str(len(results))))
            if len(results) == 0:
                self.updateView(self.SHOW_SEARCH_NO_RESULT)
                self['status'].setText(_("No data found for ' %s ' at themoviedb.org!") % self.searchTitle)
                self.session.openWithCallback(self.askForSearchCallback, MessageBox, _("No data found for ' %s ' at themoviedb.org!\nDo you want to edit the search name?") % self.searchTitle)
                return
            self.movies = []
            for movie in results:
                if movie is not None:
                    self.movies.append((movie,))

            self['list'].setList(self.movies)
            self.showMovieList()
        except Exception as e:
            from Source.Globals import printStackTrace
            printStackTrace()
            self['status'].setText(_('Error!\n%s' % e))
            self['status'].show()
            return

    def showMovieList(self):
        count = self['list'].getLength()
        if count == 1:
            txt = _('Total %s') % count + ' ' + _('movie found')
            cur = self['list'].getCurrent()
            if cur is not None:
                self.getMovieInfo(cur[0])
                self.updateView(self.SHOW_MOVIE_DETAIL)
        else:
            self.updateView(self.SHOW_RESULT_LIST)
            txt = _('Total %s') % count + ' ' + _('movies found')
        self['result_txt'].setText(txt)

    def pageUp(self):
        self['description'].pageUp()

    def pageDown(self):
        self['description'].pageDown()

    def moveUp(self):
        if self.view_mode == self.SHOW_RESULT_LIST:
            self['list'].moveUp()
        else:
            self['description'].pageUp()

    def moveDown(self):
        if self.view_mode == self.SHOW_RESULT_LIST:
            self['list'].moveDown()
        else:
            self['description'].pageDown()

    def askForSearchCallback(self, val):
        if val:
            self.yellow_pressed()
        else:
            self.close()

    def newSearchFinished(self, text=None):
        if text:
            self.searchTitle = text
            self.searchForMovies()

    def getMovieInfo(self, movie):
        try:
            if movie:
                extended = ''
                name = movie.title.encode('utf-8', 'ignore')
                description = movie.overview
                released = movie.releasedate.year
                rating = movie.userrating
                runtime = movie.runtime
                if description:
                    description_text = description.encode('utf-8', 'ignore')
                    self['description'].setText(description_text)
                else:
                    self['description'].setText(_("No description for ' %s ' at themoviedb.org found!") % name)
                if released:
                    extended = _('Appeared: %s') % released + ' / '
                if runtime:
                    extended += _('Runtime: %s minutes') % runtime + ' / '
                certification = tmdb.decodeCertification(movie.releases)
                if certification:
                    extended += _('Certification: %s') % _(certification) + ' / '
                rating = str(movie.userrating)
                extended += _('Rating: %s\n') % rating
                self.ratingstars = int(10 * round(float(rating.replace(',', '.')), 1))
                if self.ratingstars > 0:
                    self['stars'].setValue(self.ratingstars)
                genres = [x.name.encode('utf-8', 'ignore') for x in movie.genres]
                if len(genres) > 0:
                    extended += _('Genre: %s\n') % ', '.join(genres)
                studios = [x.name.encode('utf-8', 'ignore') for x in movie.studios]
                if len(studios) > 0:
                    extended += _('Studio: %s') % ', '.join(studios) + ' / '
                crew = [x.name.encode('utf-8', 'ignore') for x in movie.crew if x.job == 'Director']
                if len(crew) > 0:
                    extended += _('Director: %s') % ', '.join(crew) + ' / '
                crew = [x.name.encode('utf-8', 'ignore') for x in movie.crew if x.job == 'Producer']
                if len(crew) > 0:
                    extended += _('Production: %s\n') % ', '.join(crew)
                cast = [x.name.encode('utf-8', 'ignore') for x in movie.cast]
                if len(cast) > 0:
                    extended += _('Actors: %s\n') % ', '.join(cast)
                if movie.votes != 0:
                    self['vote'].setText(_('Voted: %s') % str(movie.votes) + ' ' + _('times'))
                else:
                    self['vote'].setText(_('No user voted!'))
                if extended:
                    self['extended'].setText(extended)
                else:
                    self['extended'].setText(_('Unknown error!!'))
            self.updateView(self.SHOW_MOVIE_DETAIL)
            self.updateCover(movie)
        except Exception as e:
            from Source.Globals import printStackTrace
            printStackTrace()
            self['status'].setText(_('Error!\n%s' % e))
            self['status'].show()
            return

    def paintCoverPixmapCB(self, picInfo=None):
        ptr = self.picload.getData()
        if ptr is not None:
            self['cover'].instance.setPixmap(ptr)
            self['cover'].show()

    def updateCover(self, movie):
        if self.view_mode != self.SHOW_MOVIE_DETAIL:
            return
        cover_url = movie.poster_url
        if cover_url is None:
            self.picload.startDecode(nocover)
        else:
            parts = cover_url.split('/')
            filename = os_path.join(IMAGE_TEMPFILE, str(movie.id) + str(parts[-1]))
            if downloadCover(cover_url, filename):
                self.picload.startDecode(filename)
            else:
                self.picload.startDecode(nocover)

    def updateImageIndex(self, method):
        if len(self.movies) == 0:
            return
        index = self['list'].getCurrentIndex()
        cur = self['list'].getCurrent()
        movie = cur[0]
        if len(movie.poster_urls) == 0:
            return
        method(movie)
        self['list'].l.invalidateEntry(index)
        self.updateCover(movie)

    def dummy(self):
        print('Dummy')

    def left(self):
        self.updateImageIndex(tmdb.prevImageIndex)

    def right(self):
        self.updateImageIndex(tmdb.nextImageIndex)

    def checkConnection(self):
        try:
            import socket
            print(socket.gethostbyname('www.google.com'))
            return True
        except:
            self.session.openWithCallback(self.close, MessageBox, _('No internet connection available!'), MessageBox.TYPE_ERROR)
            return False

    def buttonAction(self, text):
        if text == self.SHOW_DETAIL_TEXT:
            cur = self['list'].getCurrent()
            if cur is not None:
                self.getMovieInfo(cur[0])
        elif text == self.SHOW_SEARCH_RESULT_TEXT:
            self.searchForMovies()
        elif text == self.TRAILER_SEARCH_TEXT:
            if pluginPresent.YTTrailer:
                current_movie = self['list'].getCurrent()[0]
                title = current_movie.title.encode('utf-8')
                if self.view_mode == self.SHOW_RESULT_LIST:
                    self.setTitle(_('Search result for: %s') % self.searchTitle)
                else:
                    self.setTitle(_('Details for: %s') % title)
                from Plugins.Extensions.YTTrailer.plugin import YTTrailerList
                self.session.open(YTTrailerList, title)

    def ok_pressed(self):
        if self.view_mode == self.SHOW_RESULT_LIST:
            cur = self['list'].getCurrent()
            if cur is not None:
                self.getMovieInfo(cur[0])
                self.updateView(self.SHOW_MOVIE_DETAIL)
        else:
            self.updateView(self.SHOW_RESULT_LIST)

    def green_pressed(self):
        if self.service is None:
            return
        self.setTitle(_("Save Info/Cover for ' %s ', please wait ...") % self.searchTitle)
        self.checkExistEnce(self.service.getPath())

    def callback_green_pressed(self, answer=None):
        if self.checkConnection() is False or not self['list'].getCurrent():
            return
        overwrite_eit, overwrite_jpg = answer and answer[1] or (False, False)
        from Source.EventInformationTable import createEIT
        current_movie = self['list'].getCurrent()[0]
        title = current_movie.title.encode('utf-8')
        if self.service is not None:
            createEIT(self.service.getPath(), title, movie=current_movie, overwrite_jpg=overwrite_jpg, overwrite_eit=overwrite_eit)
            self.close(False)
        else:
            self.session.openWithCallback(self.close, MessageBox, _('Sorry, no info/cover found for title: %s') % title, MessageBox.TYPE_ERROR)

    def yellow_pressed(self):
        from AdvancedKeyboard import AdvancedKeyBoard
        self.session.openWithCallback(self.newSearchFinished, AdvancedKeyBoard, title=_('Enter new moviename to search for'), text=self.searchTitle)

    def blue_pressed(self):
        text = self['key_blue'].getText()
        current_movie = self['list'].getCurrent()[0]
        title = current_movie.title.encode('utf-8')
        if text == self.TRAILER_SEARCH_TEXT:
            self.setTitle(_("Search trailer for ' %s ', please wait ...") % title)
        self.blue_button_timer.start(100, True)

    def callback_blue_pressed(self):
        text = self['key_blue'].getText()
        self.buttonAction(text)

    def hideAll(self):
        self['list'].hide()
        self['tmdblogo'].hide()
        self['cover'].hide()
        self['description'].hide()
        self['extended'].hide()
        self['status'].hide()
        self['stars'].hide()
        self['no_stars'].hide()
        self['vote'].hide()
        self['result_txt'].hide()
        self['seperator'].hide()
        self['button_red'].hide()
        self['button_green'].hide()
        self['button_yellow'].hide()
        self['button_blue'].hide()

    def movieDetailView(self):
        self['WizardActions2'].setEnabled(True)
        current_movie = self['list'].getCurrent()[0]
        title = current_movie.title.encode('utf-8')
        self.setTitle(_('Details for: %s') % title)
        self.hideAll()
        self['seperator'].show()
        self['description'].show()
        self['extended'].show()
        if self.ratingstars > 0:
            self['stars'].show()
            self['no_stars'].show()
            self['vote'].show()

    def movieListView(self):
        self['WizardActions2'].setEnabled(False)
        self.setTitle(_('Search result for: %s') % self.searchTitle)
        self.hideAll()
        self['seperator'].show()
        self['tmdblogo'].show()
        self['result_txt'].show()
        self['list'].show()

    def updateView(self, mode=None):
        if mode:
            self.view_mode = mode
        if self.view_mode == self.SHOW_SEARCH:
            self.hideAll()
            self['key_red'].setText('')
            self['key_green'].setText('')
            self['key_yellow'].setText('')
            self['key_blue'].setText('')
            self['tmdblogo'].show()
        elif self.view_mode == self.SHOW_SEARCH_NO_RESULT:
            self.hideAll()
            self['key_red'].setText('')
            self['key_green'].setText('')
            self['key_yellow'].setText(self.MANUAL_SEARCH_TEXT)
            self['key_blue'].setText('')
            self['button_yellow'].show()
            self['tmdblogo'].show()
            self['seperator'].show()
            self['status'].show()
        elif self.view_mode == self.SHOW_RESULT_LIST:
            self.movieListView()
            self['key_red'].setText(self.SHOW_DETAIL_TEXT)
            self['key_green'].setText(self.INFO_SAVE_TEXT if self.service is not None else '')
            self['key_yellow'].setText(self.MANUAL_SEARCH_TEXT)
            if pluginPresent.YTTrailer:
                self['key_blue'].setText(self.TRAILER_SEARCH_TEXT)
                self['button_blue'].show()
            else:
                self['key_blue'].setText('')
                self['button_blue'].hide()
            self['button_red'].show()
            if self.service is not None:
                self['button_green'].show()
            self['button_yellow'].show()
        elif self.view_mode == self.SHOW_MOVIE_DETAIL:
            self.movieDetailView()
            self['key_red'].setText(self.SHOW_SEARCH_RESULT_TEXT)
            self['key_green'].setText(self.INFO_SAVE_TEXT if self.service is not None else '')
            self['key_yellow'].setText(self.MANUAL_SEARCH_TEXT)
            if pluginPresent.YTTrailer:
                self['key_blue'].setText(self.TRAILER_SEARCH_TEXT)
                self['button_blue'].show()
            else:
                self['key_blue'].setText('')
                self['button_blue'].hide()
            self['button_red'].show()
            if self.service is not None:
                self['button_green'].show()
            self['button_yellow'].show()
