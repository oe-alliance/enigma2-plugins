# -*- coding: UTF-8 -*-
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from datetime import datetime, timedelta
from enigma import eServiceReference, ePicLoad, gPixmapPtr, getDesktop
from json import loads
from Screens.InfoBar import MoviePlayer
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from six import ensure_str
from socket import setdefaulttimeout
from twisted.internet.reactor import callInThread
from os.path import exists, join as pathjoin
from requests import get
import os
PLUGINPATH = '/usr/lib/enigma2/python/Plugins/Extensions/ZDFMediathek/'
setdefaulttimeout(2)
FHD = getDesktop(0).size().height() > 720
if FHD:
    skin = PLUGINPATH + 'skin_FHD.xml'
else:
    skin = PLUGINPATH + 'skin_HD.xml'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Accept-Language': 'de,en-US;q=0.7,en;q=0.3', 'Accept-Encoding': 'gzip, deflate'}
API_URL = 'https://zdf-cdn.live.cellular.de/mediathekV2/'


def geturl(url):
    try:
        response = get(url, headers=HEADERS)
        return response.content
    except Exception as e:
        print(str(e))
        return ''


def cleanurl(t):
    return t.replace('ä', '%C3%A4').replace('ö', '%C3%B6').replace('ü', '%C3%BC').replace('ß', '%C3%9F').replace('\\', '/').replace(' ', '%20').strip()


class ZDFMediathek(Screen):
    def __init__(self, session):
        self.skin = open(skin, 'r').read()
        Screen.__init__(self, session)
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'DirectionActions', 'ChannelSelectBaseActions'], {"red": self.close, 'up': self.up, 'down': self.down, 'left': self.left, 'right': self.right, 'nextBouquet': self.p_up, 'prevBouquet': self.p_down, 'ok': self.ok, 'cancel': self.exit}, -1)
        self['movielist'] = List()
        self['cover'] = Pixmap()
        self['handlung'] = ScrollLabel()
        self.HISTORY = [('MENU', '', '', '')]
        if not exists('/tmp/cover/'):
            os.mkdir('/tmp/cover/')
        self.onLayoutFinish.append(self.HauptMenu)

    def HauptMenu(self, index='0'):
        menu = [('LISTE', 'ZDF Mediathek - Start', API_URL + 'start-page', '', PLUGINPATH + '/img/' + 'home.png', ''), ('LISTE', 'Rubriken', API_URL + 'categories-overview', '', PLUGINPATH + '/img/' + 'endecken.png', ''), ('LISTE', 'Sendung  A - Z', API_URL + 'brands-alphabetical', '', PLUGINPATH + '/img/' + 'az.png', ''), ('BROADCAST', 'Sendung  Verpasst', '', '', PLUGINPATH + '/img/' + 'programm.png', ''), ('SUCHE', 'Suche', '', '', PLUGINPATH + '/img/' + 'suche.png', '')]
        self['movielist'].setList(menu)
        self['movielist'].setIndex(int(index))
        self.infos()

    def ok(self):
        Type = self['movielist'].getCurrent()[0]
        teaser = ''
        if Type == 'SUCHE':
            self.session.openWithCallback(self.search, VirtualKeyBoard, title='ZDF Mediathek Suche')
        elif Type == 'PLAY':
            self.Play()
        elif Type == 'LIVE':
            teaser = self['movielist'].getCurrent()[7]
            self.Live(teaser)
        else:
            Index = self['movielist'].getIndex()
            url = self['movielist'].getCurrent()[2]
            if Type == 'LISTE':
                self.load(url)
            elif Type == 'TEASER':
                teaser = self['movielist'].getCurrent()[7]
                self.teaser(url, teaser)
            elif Type == 'STAGE':
                self.Stage(url)
            elif Type == 'BROADCAST':
                self.Broadcast()
            else:
                self.session.open(MessageBox, Type, MessageBox.TYPE_INFO)
            self.HISTORY.append((Type, url, Index, teaser))
            self.infos()

    def exit(self):
        if len(self.HISTORY) > 1:
            Index = self.HISTORY[-1][2]
            self.HISTORY.pop()
            Type = self.HISTORY[-1][0]
            url = self.HISTORY[-1][1]
            teaser = self.HISTORY[-1][3]
            if Type == 'LISTE':
                self.load(url, Index)
            elif Type == 'TEASER':
                self.teaser(url, teaser, Index)
            elif Type == 'STAGE':
                self.Stage(url, Index)
            elif Type == 'BROADCAST':
                self.Broadcast(Index)
            elif Type == 'MENU':
                self.HauptMenu(Index)
            else:
                self.session.open(MessageBox, Type, MessageBox.TYPE_INFO)
        else:
            os.system('rm -rf /tmp/cover')
            self.close()

    def ImageRead(self, img):
        if img.get('teaserBild'):
            img = img.get('teaserBild')
            if img.get('384'):
                img = img.get('384')
            elif img.get('380'):
                img = img.get('380')
            if img.get('url'):
                return img.get('url')
        return ''

    def search(self, search):
        if search:
            self.searchtxt = search
            url = 'https://zdf-cdn.live.cellular.de/mediathekV2/search?q=%s' % (cleanurl(self.searchtxt))
            Index = self['movielist'].getIndex()
            self.HISTORY.append(('LISTE', url, Index, ''))
            self.load(url, index='0')

    def Broadcast(self, index='0'):
        liste = []
        now = datetime.now()
        for i in range(0, 7):
            Datum = (now + timedelta(- i)).strftime('%d-%m-%Y')
            url = API_URL + 'broadcast-missed/%s' % (now + timedelta(- i)).strftime('%Y-%m-%d')
            liste.append(('LISTE', ensure_str(Datum), url, '', PLUGINPATH + '/img/' + 'programm.png', '', '', index))
        if liste:
            self['movielist'].setList(liste)
            self['movielist'].setIndex(int(index))

    def Stage(self, url, index='0'):
        liste = []
        data = geturl(url)
        if data:
            data = loads(ensure_str(data))
            if data.get('stage'):
                for stage in data.get('stage'):
                    stage = self.teaserContent(stage)
                    if stage:
                        liste.append((stage))
            if liste:
                self['movielist'].setList(liste)
                self['movielist'].setIndex(int(index))

    def load(self, url, index='0'):
        liste = []
        html = geturl(url)
        if html:
            html = loads(ensure_str(html))
            if html.get('stage'):
                liste.append(('STAGE', 'Stage', url, '', PLUGINPATH + '/img/' + 'stage.png', '', '', ''))
            if html.get('cluster'):
                data = html.get('cluster')
            elif html.get('epgCluster'):
                data = html.get('epgCluster')
            elif html.get('broadcastCluster'):
                data = html.get('broadcastCluster')
            elif html.get('results'):
                data = html.get('results')
                if data:
                    for TC in data:
                        TC = self.teaserContent(TC)
                        if TC:
                            liste.append((TC))
            else:
                self.session.open(MessageBox, 'Kein Eintrag vorhanden', MessageBox.TYPE_INFO)
                return
            TIndex = -1
            for js in data:
                TIndex += 1
                if not js.get('name', '') and len(js.get('teaser', '')) > 0:
                    TE = js.get('teaser')
                    if TE:
                        for TC in TE:
                            TC = self.teaserContent(TC)
                            if TC:
                                liste.append((TC))
                if not js.get('name', '') or len(js.get('teaser', '')) == 0:
                    continue
                title = js.get('name')
                img = self.ImageRead(js.get('teaser')[0])
                if js.get('liveStream'):
                    liste.append(('LIVE', ensure_str(title), url, '', (img), '', '', TIndex))
                else:
                    liste.append(('TEASER', ensure_str(title), (url), '', (img), '', '', TIndex))
            if liste:
                if html.get('nextPageUrl'):
                    liste.append(('LISTE', 'Next Page', html.get('nextPageUrl'), '', PLUGINPATH + '/img/' + 'nextpage.png', '', '', ''))
                self['movielist'].setList(liste)
                self['movielist'].setIndex(int(index))
        else:
            self.session.open(MessageBox, 'Kein Eintrag vorhanden', MessageBox.TYPE_INFO)

    def teaserContent(self, js):
        if js.get('type') == 'externalUrl':
            return
        if js.get('seasonNumber'):
            title = js.get('headline') + ' - ' + "S{:02d}E{:02d} - ".format(int(js.get('seasonNumber', '0')), int(js.get('episodeNumber', '0'))) + js.get('titel')
        else:
            title = js.get('titel', '')
        img = self.ImageRead(js)
        plot = js.get('beschreibung', '')
        if js.get('textLong'):
            plot = js.get('textLong')
        if js.get('timetolive'):
            plot += u'\n\nVerfügbar bis ' + js.get('timetolive')
        if js.get('geoLocation'):
            geo = js.get('geoLocation')
            if geo == 'dach':
                plot += u'\nin Deutschland, Österreich, Schweiz'
            elif geo == 'de':
                plot += '\nin Deutschland'
        if js.get('fsk', '').startswith('fsk'):
            plot += '\n' + js.get('fsk').upper()
        plot += '\n' + js.get('channel', '')
        plot += '\n' + js.get('headline') + ' ' + js.get('label', '')
        duration = js.get('length', '')
        if str(duration).isdigit():
            duration = str(timedelta(seconds=int(duration)))
        url = js.get('url')
        if js.get('type') == 'video':
            return 'PLAY', ensure_str(title), url, ensure_str(plot), img, duration, '', ''
        else:
            return 'LISTE', ensure_str(title), url, ensure_str(plot), img, duration, '', ''

    def teaser(self, url, teaser, index='0'):
        liste = []
        data = loads(geturl(url))
        if data.get('cluster'):
            cluster = data.get('cluster')[teaser]
            teaser = cluster.get('teaser')
        elif data.get('broadcastCluster'):
            cluster = data.get('broadcastCluster')[teaser]
            teaser = cluster.get('teaser')
        else:
            self.session.open(MessageBox, 'Kein Eintrag vorhanden', MessageBox.TYPE_INFO)
            return

        for TC in teaser:
            TC = self.teaserContent(TC)
            if TC:
                liste.append((TC))
        if liste:
            self['movielist'].setList(liste)
            self['movielist'].setIndex(int(index))

    def Play(self):
        url = self['movielist'].getCurrent()[2]
        data = ensure_str(geturl(url))
        if 'fskCheck":true' in data:
            self.session.open(MessageBox, 'Das Video ist nicht für Kinder und Jugendliche geeignet und kann erst nach 22 Uhr abgespielt werden.', MessageBox.TYPE_INFO)
            return
        liste = []
        if data:
            data = loads(data)
        if data.get('document'):
            data = data.get('document')
            if data.get('formitaeten'):
                data = data.get('formitaeten')
                for js in data:
                    url = js.get('url')
                    q = js.get('quality').upper()
                    if '.m3u8' in url:
                        q += '(M3U8)'
                    elif '.mp4' in url:
                        q += '(MP4)'
                    if js.get('language'):
                        q += ' ' + js.get('language').upper()
                    if js.get('class', '') == 'ad':
                        q += ' Audiodeskription'
                    liste.append((ensure_str(q), url))
        if len(liste) > 1:
            self.session.openWithCallback(self.Play2, ChoiceBox, title='Wiedergabe starten?', list=sorted(liste, reverse=True, key=str))
        elif liste:
            self.Play2(liste[0])
        else:
            self.session.open(MessageBox, 'Kein Eintrag vorhanden', MessageBox.TYPE_INFO)

    def Live(self, teaser):
        self.session.open(MessageBox, 'Achtung! Livestreams werden in der aktuellen Version noch nicht unterstützt.', MessageBox.TYPE_INFO)

    def Play2(self, answer):
        answer = answer and answer[1]
        if answer:
            sref = eServiceReference(4097, 0, ensure_str(answer))
            sref.setName(self['movielist'].getCurrent()[1])
            self.session.open(MoviePlayer2, sref)

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

    def infos(self):
        handlung = self['movielist'].getCurrent()[3]
        self['handlung'].setText(str(handlung))
        self.show_cover()

    def show_cover(self):
        if self['movielist'].getCurrent() is not None:
            url = self['movielist'].getCurrent()[4]
            if url.startswith('http'):
                callInThread(self.getimage, url)
            elif url.startswith('/usr/'):
                self.get_cover(url)
            else:
                img = PLUGINPATH + '/img/nocover.png'
                self.get_cover(img)

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
        scale = AVSwitch().getFramebufferScale()
        size = self['cover'].instance.size()
        self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, '#FF000000'))
        if self.picload.startDecode(img, 0, 0, False) == 0:
            ptr = self.picload.getData()
            if ptr is not None:
                self['cover'].instance.setPixmap(ptr)
                self['cover'].show()


class MoviePlayer2(MoviePlayer):
    def __init__(self, session, service):
        MoviePlayer.__init__(self, session, service)
        self.skinName = 'MoviePlayer'

    def up(self):
        pass

    def down(self):
        pass

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
