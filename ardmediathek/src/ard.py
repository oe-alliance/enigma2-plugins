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
import re
PLUGINPATH = '/usr/lib/enigma2/python/Plugins/Extensions/ArdMediathek/'
setdefaulttimeout(2)
FHD = getDesktop(0).size().height() > 720
if FHD:
    skin = PLUGINPATH + 'skin_FHD.xml'
else:
    skin = PLUGINPATH + 'skin_HD.xml'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Accept-Language': 'de,en-US;q=0.7,en;q=0.3', 'Accept-Encoding': 'gzip, deflate'}
API_URL = 'https://api.ardmediathek.de/page-gateway/'
URL_START = API_URL + 'pages/ard/editorial/mainstreamer-webpwa-nichtaendern?embedded=true'
URL_ENTDECKEN = API_URL + 'pages/ard/editorial/entdecken?embedded=true'
URL_LIVE = API_URL + 'widgets/ard/editorials/4hEeBDgtx6kWs6W6sa44yY?pageNumber=0&pageSize=24&embedded=true'
URL_HOME = API_URL + 'pages/%s/home?embedded=true'
URL_AZ = API_URL + 'pages/%s/editorial/experiment-a-z?embedded=true'


def geturl(url):
    try:
        response = get(url, headers=HEADERS)
        return response.content
    except Exception as e:
        print(str(e))
        return ''


def quality(t):
    q = {'0': 'Niedrige Qualität', '1': 'Mittlere Qualität', '2': 'hohe Qualität', '3': 'Sehr hohe Qualität', '4': 'Full HD'}
    if t in q:
        return q[t]
    else:
        return t


def cleanurl(t):
    return t.replace('ä', '%C3%A4').replace('ö', '%C3%B6').replace('ü', '%C3%BC').replace('ß', '%C3%9F').replace('\\', '/').replace(' ', '%20').strip()


def dateTime2(dt):
    try:
        import time
        s = ''
        delta = time.localtime().tm_isdst
        if dt.get('broadcastedOn'):
            b = time.mktime(time.strptime(dt.get('broadcastedOn'), "%Y-%m-%dT%H:%M:%SZ"))
            b = b + (delta + 1) * 3600
            b = time.localtime(b)
            s += 'Gesendet am %s ' % '{0:02d}.{1:02d}.{2:04d} {3:02d}:{4:02d}'.format(b.tm_mday, b.tm_mon, b.tm_year, b.tm_hour, b.tm_min) + '\n'
        if dt.get('availableTo'):
            a = time.mktime(time.strptime(dt.get('availableTo'), "%Y-%m-%dT%H:%M:%SZ"))
            a = a + (delta + 1) * 3600
            a = time.localtime(a)
            s += 'Verfügbar bis %s' % '{0:02d}.{1:02d}.{2:04d} {3:02d}:{4:02d}'.format(a.tm_mday, a.tm_mon, a.tm_year, a.tm_hour, a.tm_min)
        return ensure_str(s)
    except Exception:
        return ''


class ArdMediathek(Screen):
    def __init__(self, session):
        self.skin = open(skin, 'r').read()
        Screen.__init__(self, session)
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'DirectionActions', 'ChannelSelectBaseActions'], {"red": self.close, 'up': self.up, 'down': self.down, 'left': self.left, 'right': self.right, 'nextBouquet': self.p_up, 'prevBouquet': self.p_down, 'ok': self.ok, 'cancel': self.exit}, -1)
        self['movielist'] = List()
        self['cover'] = Pixmap()
        self['handlung'] = ScrollLabel()
        self.HISTORY = [('MENU', '')]
        if not exists('/tmp/cover/'):
            os.mkdir('/tmp/cover/')
        self.onLayoutFinish.append(self.HauptMenu)

    def HauptMenu(self, index='0'):
        self.searchtxt = ''
        self.PROGRAMM = 'ard'
        menu = [('MENU', 'ARD Mediathek - Start', URL_START, '', PLUGINPATH + '/img/' + 'home.png', ''),
                ('MENU', 'Entdecken', URL_ENTDECKEN, '', PLUGINPATH + '/img/' + 'endecken.png', ''),
                ('SenderMenu', 'Sender', 'SenderMenu', '', PLUGINPATH + '/img/' + 'sender.png', ''),
                ('ProgrammMenu', 'Sendung verpasst', 'ProgrammMenu', '', PLUGINPATH + '/img/' + 'programm.png', ''),
                ('MENU', 'Sendungen A-Z', URL_AZ % 'ard', '', PLUGINPATH + '/img/' + 'az.png', ''),
                ('MENU', 'LIVE', URL_LIVE, '', PLUGINPATH + '/img/' + 'live.png', ''),
                ('Suche', 'Suche', '', '', PLUGINPATH + '/img/' + 'suche.png', '')]
        self['movielist'].setList(menu)
        self['movielist'].setIndex(int(index))
        self.infos()

    def ok(self):
        if self['movielist'].getCurrent()[0] == 'Suche':
            self.session.openWithCallback(self.search, VirtualKeyBoard, title='ARD Mediathek Suche')
        elif self['movielist'].getCurrent()[0] == 'PLAY':
            self.Play()
        else:
            Index = self['movielist'].getIndex()
            url = self['movielist'].getCurrent()[2]
            if self['movielist'].getCurrent()[0] == 'MENU':
                self.load(url)
            elif self['movielist'].getCurrent()[0] == 'WEITER':
                self.load(url)
            elif self['movielist'].getCurrent()[0] == 'Sender2Menu':
                self.PROGRAMM = self['movielist'].getCurrent()[2]
                self.Menu2Sender()
                url = 'Sender2Menu'
            elif self['movielist'].getCurrent()[0] == 'Programm3':
                self.PROGRAMM = self['movielist'].getCurrent()[2]
                url = 'Programm3'
                self.Programm3()
            elif self['movielist'].getCurrent()[0] == 'SenderMenu':
                self.SenderMenu('0', 'Sender2Menu')

            elif self['movielist'].getCurrent()[0] == 'ProgrammMenu':
                self.SenderMenu('0', 'Programm3')
            else:
                print('OK ELSE')
            self.HISTORY.append((url, Index))

    def exit(self):
        if len(self.HISTORY) > 1:
            Index = self.HISTORY[-1][1]
            self.HISTORY.pop()
            url = self.HISTORY[-1][0]
            if url.startswith('http'):
                self.load(url, Index)
            elif url == 'MENU':
                self.HauptMenu(Index)
            elif url == 'SenderMenu':
                self.SenderMenu(Index, 'Sender2Menu')
            elif url == 'Sender2Menu':
                self.Menu2Sender(Index)
            elif url == 'ProgrammMenu':
                self.SenderMenu(Index, 'ProgrammMenu')
            elif url == 'Programm3':
                self.Programm3(Index)
        else:
            os.system('rm -rf /tmp/cover')
            self.close()

    def SenderMenu(self, index='0', mt=''):
        menu = [(mt, 'Alpha', 'alpha', '', PLUGINPATH + '/img/' + 'alpha.png', ''),
                (mt, 'Arte', 'arte', '', PLUGINPATH + '/img/' + 'arte.png', ''),
                (mt, 'BR', 'br', '', PLUGINPATH + '/img/' + 'br.png', ''),
                (mt, 'Das Erste', 'daserste', '', PLUGINPATH + '/img/' + 'daserste.png', ''),
                (mt, 'HR', 'hr', '', PLUGINPATH + '/img/' + 'hr.png', ''),
                (mt, 'KIKA', 'kika', '', PLUGINPATH + '/img/' + 'kika.png', ''),
                (mt, 'MDR', 'mdr', '', PLUGINPATH + '/img/' + 'mdr.png', ''),
                (mt, 'NDR', 'ndr', '', PLUGINPATH + '/img/' + 'ndr.png', ''),
                (mt, 'One', 'one', '', PLUGINPATH + '/img/' + 'one.png', ''),
                (mt, 'Phoenix', 'phoenix', '', PLUGINPATH + '/img/' + 'phoenix.png', ''),
                (mt, 'Radio Bremen', 'radiobremen', '', PLUGINPATH + '/img/' + 'radiobremen.png', ''),
                (mt, 'RBB', 'rbb', '', PLUGINPATH + '/img/' + 'rbb.png', ''),
                (mt, 'SR', 'sr', '', PLUGINPATH + '/img/' + 'sr.png', ''),
                (mt, 'SWR', 'swr', '', PLUGINPATH + '/img/' + 'swr.png', ''),
                (mt, 'Tagesschau24', 'tagesschau24', '', PLUGINPATH + '/img/' + 'tagesschau24.png', ''),
                (mt, 'WDR', 'wdr', '', PLUGINPATH + '/img/' + 'wdr.png', '')]
        self['movielist'].setList(menu)
        self['movielist'].setIndex(int(index))
        self.infos()

    def Menu2Sender(self, index='0'):
        menu = [('WEITER', '%s  Start' % self.PROGRAMM.upper(), URL_HOME % self.PROGRAMM, '', PLUGINPATH + '/img/' + 'home.png', ''), ('WEITER', 'Sendungen A-Z', URL_AZ % self.PROGRAMM, '', PLUGINPATH + '/img/' + 'az.png', ''), ('Suche', 'Suche', '', '', PLUGINPATH + '/img/' + 'suche.png', '')]
        self['movielist'].setList(menu)
        self['movielist'].setIndex(int(index))
        self.infos()

    def Programm3(self, index='0'):
        now = datetime.now()
        liste = []

        for i in range(0, 7):
            start = (now + timedelta(-i))
            if i == 0:
                title = 'HEUTE'
            elif i == 1:
                title = 'GESTERN'
            else:
                title = start.strftime("%d.%m.%Y")
            start = (start.strftime("%Y-%m-%dT03:30:00.000Z"))
            end = ((now + timedelta(1 - i)).strftime("%Y-%m-%dT03:29:59.000Z"))
            url = 'https://api.ardmediathek.de/page-gateway/compilations/%s/pastbroadcasts?startDateTime=%s&endDateTime=%s&pageSize=200' % (self.PROGRAMM, start, end)
            liste.append(('WEITER', title, ensure_str(url), '', '', ''))
        self['movielist'].setList(liste)
        self['movielist'].setIndex(int(index))
        self.infos()

    def search(self, search):
        if search:
            self.searchtxt = search
            url = API_URL + 'widgets/%s/search/grouping?searchString=%s&pageSize=200' % (self.PROGRAMM, cleanurl(self.searchtxt))
            Index = self['movielist'].getIndex()
            self.HISTORY.append((url, Index))
            self.load(url, index='0')

    def load(self, url, index='0'):
        liste = []
        data = geturl(url)
        if data:
            data = loads(ensure_str(data))
        else:
            self.HISTORY.pop()
            return
        if len(data) == 1:
            data = data[0]
        if data.get('widgets', ''):
            data2 = data.get('widgets')
            if 'grouping' in url and data2[0].get('teasers'):
                data2 = data2[0].get('teasers')
        elif data.get('teasers'):
            data2 = data.get('teasers')
        else:
            if self.searchtxt:
                self.session.open(MessageBox, 'Kein Suchergebnis', MessageBox.TYPE_INFO, 5)
            else:
                self.session.open(MessageBox, 'Kein Eintrag vorhanden', MessageBox.TYPE_INFO)
            self.HISTORY.pop()
            return
        if self.searchtxt and 'grouping?searchString' in url:
            liste.append(('WEITER', 'Videos', API_URL + 'widgets/%s/search/vod?searchString=%s&pageNumber=0&pageSize=200' % (self.PROGRAMM, cleanurl(self.searchtxt)), '', '', ''))

        for js in data2:
            duration = ''
            img = ''
            plot = ''
            if js.get('title'):
                title = js.get('title')
            else:
                title = js.get('longTitle', '')
            if ' | ' in title:
                plot += title.split(' | ')[1] + '\n'
                title = title.split(' | ')[0]
            plot += dateTime2(js)
            plot += js.get('description', '')
            if js.get('show'):
                s = js.get('show')
                if s.get('longSynopsis'):
                    plot += '\n\n' + s.get('longSynopsis') + '\n'
            if js.get('maturityContentRating') and 'FSK' in js.get('maturityContentRating') and 'FSK0' not in js.get('maturityContentRating'):
                plot += js.get('maturityContentRating', '') + '\n'
            if js.get('publicationService'):
                PS = js.get('publicationService', '')
                plot += PS.get('name') + '\n'
            if plot == '':
                plot += data.get('title', '')
            if js.get('duration'):
                duration = js.get('duration', '')
                if str(duration).isdigit():
                    duration = str(timedelta(seconds=int(duration)))
            if js.get('images'):
                im = js.get('images')
            elif js.get('teasers'):
                im = js.get('teasers')[0]
                if im.get('images'):
                    im = im.get('images')
            else:
                im = dict()
            if im.get('aspect16x9'):
                im = im.get('aspect16x9')
            if im.get('src'):
                img = im.get('src').replace('{width}', '360')
            if js.get('links'):
                li = js.get('links')
                if li.get('target'):
                    li = li.get('target')
                elif li.get('self'):
                    li = li.get('self')
                if li.get('href'):
                    url2 = li.get('href')
            if js.get('duration') or js.get('type') in ('live', 'event', 'broadcastMainClip'):
                liste.append(('PLAY', ensure_str(title), ensure_str(url2), ensure_str(plot), cleanurl(img), duration))
            else:
                liste.append(('WEITER', ensure_str(title), ensure_str(url2), ensure_str(plot), cleanurl(img), duration))
        if 'grouping' in url and data.get('widgets'):
            data = data.get('widgets')[0]
        if data.get('pagination'):
            page = data.get('pagination')
            pageNumber = page.get('pageNumber')
            pageSize = page.get('pageSize')
            total = page.get('totalElements')
            if (int(pageNumber) + 1) * int(pageSize) < int(total):
                if '/search/vod' in url:
                    url = API_URL + 'widgets/%s/search/vod?searchString=%s&pageNumber=%s&pageSize=%d' % (self.PROGRAMM, self.searchtxt, pageNumber + 1, pageSize)
                elif 'grouping' in url or 'asset' in url:
                    url = API_URL + 'widgets/%s/asset/%s?pageNumber=%s&pageSize=%s' % (self.PROGRAMM, data.get('id', ''), pageNumber + 1, pageSize)
                else:
                    url = API_URL + 'widgets/%s/editorials/%s?pageNumber=%s&pageSize=%s&embedded=true' % (self.PROGRAMM, data.get('id', ''), pageNumber + 1, pageSize)
                maxpage = total // pageSize + (1 if total - pageSize * (total // pageSize) > 0 else 0)
                liste.append(('WEITER', 'NextPage (' + str((int(pageNumber) + 2)) + ' / ' + str(maxpage) + ')', cleanurl(url), '', PLUGINPATH + '/img/' + 'nextpage.png', ''))
        if liste:
            self['movielist'].setList(liste)
            self['movielist'].setIndex(int(index))
            self.infos()

    def Play(self):
        url = self['movielist'].getCurrent()[2]
        html = ensure_str(geturl(url))
        if 'blockedByFsk":true' in html:
            self.session.open(MessageBox, 'Das Video ist nicht für Kinder und Jugendliche geeignet und kann erst nach 22 Uhr abgespielt werden.', MessageBox.TYPE_INFO)
            return
        liste = []
        links = re.compile('_quality":[?"|]?([^",]+).*?_stream":"([^"]+)', re.DOTALL).findall(html)
        if links:
            for q, url in links[::-1]:
                if url.startswith('//'):
                    url = 'https:' + url
                liste.append((quality(q), url))
        if len(liste) > 1:
            self.session.openWithCallback(self.Play2, ChoiceBox, title='Wiedergabe starten?', list=liste)
        elif liste:
            self.Play2(liste[0])
        else:
            self.session.open(MessageBox, 'Kein Eintrag vorhanden', MessageBox.TYPE_INFO)

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
        self['handlung'].setText(handlung)
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
        self.picload.setPara(size.width(), size.height(), scale[0], scale[1], False, 1, '#FF000000')
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
