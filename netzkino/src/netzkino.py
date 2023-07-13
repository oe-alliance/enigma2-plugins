# -*- coding: UTF-8 -*-
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from datetime import timedelta
from enigma import eServiceReference, ePicLoad, gPixmapPtr, getDesktop
from Screens.InfoBar import MoviePlayer
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox
from twisted.internet.reactor import callInThread
from os.path import exists, join as pathjoin
from json import loads
from socket import setdefaulttimeout
from six import ensure_str
from requests import get
import os
PLUGINPATH = '/usr/lib/enigma2/python/Plugins/Extensions/Netzkino/'
setdefaulttimeout(2)
FHD = getDesktop(0).size().height() > 720
if FHD:
    skin = PLUGINPATH + 'skin_FHD.xml'
else:
    skin = PLUGINPATH + 'skin_HD.xml'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Accept-Language': 'de,en-US;q=0.7,en;q=0.3', 'Accept-Encoding': 'gzip, deflate'}
API = 'https://api.netzkino.de.simplecache.net/capi-2.0a/'


def geturl(url):
    try:
        response = get(url, headers=HEADERS)
        return response.content
    except Exception as e:
        print(str(e))
        return ''


def cleanurl(t):
    return t.replace('ä', '%C3%A4').replace('ö', '%C3%B6').replace('ü', '%C3%BC').replace('ß', '%C3%9F').replace('\\', '/').replace(' ', '%20').strip()


class netzkino(Screen):
    def __init__(self, session):
        self.skin = open(skin, 'r').read()
        Screen.__init__(self, session)
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ChannelSelectBaseActions'], {'up': self.up, 'down': self.down, 'left': self.left, 'right': self.right, 'nextBouquet': self.p_up, 'prevBouquet': self.p_down, 'ok': self.ok, 'cancel': self.exit}, -1)
        self['movielist'] = List()
        self['cover'] = Pixmap()
        self['handlung'] = ScrollLabel()
        self.currentList = 'Menu'
        if not exists('/tmp/cover/'):
            os.mkdir('/tmp/cover/')
        self.onLayoutFinish.append(self.HauptMenu)

    def HauptMenu(self):
        self.currentList = 'Menu'
        cat = [('Suche', 'NetzkinoSuche', '', '', ''), ('Neu bei Netzkino', 'neu-frontpage', '', '', ''), ('Filme mit Auszeichnungen', 'filme_mit_auszeichnungen-frontpage', '', '', ''), ('Exklusiv bei Netzkino', 'frontpage-exklusiv-frontpage', '', '', ''), ('Letzte Chance - Nur noch kurze Zeit verfügbar', '10633', '', '', ''), ('Unsere Empfehlungen der Woche', 'empfehlungen_woche-frontpage', '', '', ''), ('Beste Bewertung', 'beste-bewertung-frontpage', '', '', ''), ('Meistgesehene Filme', 'meisgesehene_filme-frontpage', '', '', ''), ('Top IMDB', 'top-20-frontpage', '', '', ''), ('Featured', 'featured', '', '', ''), ('Highlights', 'highlights-frontpage', '', '', ''), ('Themenkino', 'themenkino-frontpage', '', '', ''), ('Blockbuster & Kultfilme', 'blockbuster-kultfilme-frontpage', '', '', ''), ('Mockbuster', 'mockbuster-frontpage', '', '', ''), ('Komödien', 'komodien-frontpage', '', '', ''), ('Beliebte Animes', 'beliebte-animes-frontpage', '', '', ''), ('Animekino', 'animekino', '', '', ''), ('Actionkino', 'actionkino', '', '', ''), ('Dramakino', 'dramakino', '', '', ''), ('Thrillerkino', 'thrillerkino', '', '', ''), ('Liebesfilmkino', 'liebesfilmkino', '', '', ''), ('Scifikino', 'scifikino', '', '', ''), ('Arthousekino', 'arthousekino', '', '', ''), ('Spasskino', 'spasskino', '', '', ''), ('Asiakino', 'asiakino', '', '', ''), ('Horrorkino', 'horrorkino', '', '', ''), ('Kinderkino', 'kinderkino', '', '', ''), ('Kino ab 18', 'kinoab18', '', '', ''), ('Themenkino Genre', 'themenkino-genre', '', '', '')]
        self['movielist'].setList(cat)
        self['movielist'].setIndex(1)

    def load(self, url):
        liste = []
        data = geturl(url)
        if data:
            data = loads(ensure_str(data))
        if data and 'posts' in data:
            for item in data.get('posts'):
                Duration = ''
                if 'title' not in item or 'custom_fields' not in item:
                    continue
                fields = item.get('custom_fields')
                title = item.get('title')
                image = cleanurl(item.get('thumbnail', ''))
                url = cleanurl(fields.get('Streaming')[0])
                if fields.get('Adaptives_Streaming')[0]:
                    title += ' (' + fields.get('Adaptives_Streaming')[0] + ')'
                if fields.get('Jahr')[0]:
                    title += ' (' + fields.get('Jahr')[0] + ')'
                info = item.get('content', '')
                if fields.get('FSK')[0]:
                    info += '\n FSK: ' + fields.get('FSK')[0]
                if fields.get('Regisseur')[0]:
                    info += '\n Regisseur: ' + fields.get('Regisseur')[0]
                if fields.get('Stars')[0]:
                    info += '\n Stars: ' + fields.get('Stars')[0]
                if fields.get('Duration')[0].isdigit():
                    Duration = str(timedelta(seconds=int(fields.get('Duration')[0])))
                if url:
                    liste.append((str(title), str(url), str(info), str(image), str(Duration)))
        if liste:
            self.currentList = 'Play'
            self['movielist'].setList(liste)
            self['movielist'].setIndex(0)
            self.infos()
        elif self['movielist'].getCurrent()[0] == 'Suche':
            self.session.open(MessageBox, 'Keine Suchergebnisse', MessageBox.TYPE_INFO, timeout=5)
        else:
            self.session.open(MessageBox, 'Fehler beim Lesen der Daten', MessageBox.TYPE_ERROR)

    def ok(self):
        if self.currentList == 'Menu':
            if self['movielist'].getCurrent()[1] == 'NetzkinoSuche':
                self.session.openWithCallback(self.search, VirtualKeyBoard, title='Netzkino Suche')
            else:
                url = API + 'categories/%s.json?d=www&l=de-DE' % self['movielist'].getCurrent()[1]
                self.load(url)
        elif self.currentList == 'Play':
            self.play(self['movielist'].getCurrent()[1])

    def search(self, search):
        if search:
            url = API + 'search?q=%s&d=www&l=de-DE&v=v1.2.0' % cleanurl(search)
            self.load(url)

    def up(self):
        if self['movielist']:
            self['movielist'].up()
            self.infos()

    def down(self):
        if self['movielist']:
            self['movielist'].down()
            self.infos()

    def left(self):
        if self['movielist']:
            self['movielist'].pageUp()
            self.infos()

    def right(self):
        if self['movielist']:
            self['movielist'].pageDown()
            self.infos()

    def p_up(self):
        self['handlung'].pageUp()

    def p_down(self):
        self['handlung'].pageDown()

    def play(self, url):
        url = 'https://pmd.netzkino-seite.netzkino.de/%s.mp4' % url
        sref = eServiceReference(4097, 0, url)
        sref.setName(self['movielist'].getCurrent()[0])
        self.session.open(MoviePlayer2, sref)

    def exit(self):
        if not self.currentList == 'Menu':
            self.HauptMenu()
            self.infos()
        else:
            os.system('rm -rf /tmp/cover')
            self.close()

    def infos(self):
        handlung = self['movielist'].getCurrent()[2]
        self['handlung'].setText(handlung)
        self.show_cover()

    def show_cover(self):
        if self['movielist'].getCurrent() is not None:
            url = self['movielist'].getCurrent()[3]
            if url.startswith('http'):
                callInThread(self.getimage, url)
            elif url.startswith('/usr/'):
                self.get_cover(url)
            else:
                self['cover'].hide()

    def getimage(self, url):
        try:
            data = geturl(url)
            pathName = pathjoin('/tmp/cover', 'bild')
            with open(pathName, 'wb') as f:
                f.write(data)
            self.get_cover(pathName)
        except OSError as e:
            print('[PixmapDownloader] Error: %s' % str(e))

    def get_cover(self, img):
        self.picload = ePicLoad()
        self['cover'].instance.setPixmap(gPixmapPtr())
        size = self['cover'].instance.size()
        self.picload.setPara((size.width(), size.height(), 1, 1, False, 1, '#FF000000'))
        if self.picload.startDecode(img, 0, 0, False) == 0:
            ptr = self.picload.getData()
            if ptr is not None:
                self['cover'].instance.setPixmap(ptr)
                self['cover'].show()


class MoviePlayer2(MoviePlayer):
    def __init__(self, session, service):
        MoviePlayer.__init__(self, session, service)
        self.skinName = 'MoviePlayer'

    def leavePlayer(self):
        self.close()

    def leavePlayerOnExit(self):
        self.close()

    def doEofInternal(self, playing):
        if not self.execing:
            return
        if not playing:
            return
        self.close()
