# -*- coding: UTF-8 -*-
from os.path import join, exists
from os import mkdir, system, unlink
from datetime import datetime, timedelta
from json import loads
import xml.etree.ElementTree as Et
import time
import re
import requests
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigDirectory, ConfigSelection
from Components.FileList import FileList
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from enigma import eServiceReference, ePicLoad, gPixmapPtr, getDesktop, addFont
from Screens.InfoBarGenerics import setResumePoint
from Screens.InfoBar import MoviePlayer
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from six import ensure_str
from twisted.internet.reactor import callInThread
from Tools.Downloader import downloadWithProgress
PLUGINPATH = '/usr/lib/enigma2/python/Plugins/Extensions/ArdMediathek/'
config.plugins.ARD = ConfigSubsection()
config.plugins.ARD.savetopath = ConfigDirectory(default='/media/hdd/movie/')
RegionList = [("bw", ("Baden-Württemberg (SWR)")), ("by", ("Bayern (BR)")), ("be", ("Berlin (rbb)")), ("bb", ("Brandenburg (rbb)")), ("hb", ("Bremen (radiobremen)")), ("hh", ("Hamburg (NDR)")), ("he", ("Hessen (hr)")), ("mv", ("Mecklenburg-Vorpommern (NDR)")), ("ni", ("Niedersachsen (NDR)")), ("nw", ("Nordrhein-Westfalen (WDR)")), ("rp", ("Rheinland-Pfalz (SWR)")), ("sl", ("Saarland (SR)")), ("sn", ("Sachsen (mdr)")), ("st", ("Sachsen-Anhalt (mdr)")), ("sh", ("Schleswig-Holstein (NDR)")), ("th", ("Thüringen (mdr"))]
config.plugins.ARD.Region = ConfigSelection(default="nw", choices=RegionList)
FHD = getDesktop(0).size().height() > 720
SKINFILE = join(PLUGINPATH, 'skin_FHD.xml') if FHD else join(PLUGINPATH, 'skin_HD.xml')
FONT = '/usr/share/fonts/LiberationSans-Regular.ttf'
if not exists(FONT):
    FONT = '/usr/share/fonts/nmsbd.ttf'
addFont(FONT, 'SRegular', 100, False)
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0'}
API_URL = 'https://api.ardmediathek.de/page-gateway/'
URL_HOME = API_URL + 'pages/%s/home?embedded=true'
URL_AZ = API_URL + 'pages/%s/editorial/experiment-a-z?embedded=true'
ColorList = [("default,#1a104485,#3D104485", ("Trans-BrightBlue")), ("default,#050a1232,#1502050e", ("Trans-DarkBlue")),
    ("default,#05000000,#15000000", ("Trans-Black")), ("default,#1a746962,#1502050e", ("Trans-BrownBlue")),
    ("MiniTV,#104485,#0c366a", ("BrightBlue MiniTV")), ("MiniTV,#0a1232,#02050e", ("DarkBlue MiniTV")),
    ("MiniTV,#000000,#080808", ("Black MiniTV")), ("MiniTV,#746962,#02050e", ("BrownBlue MiniTV"))]
config.plugins.ARD.SkinColor = ConfigSelection(default="default,#050a1232,#1502050e", choices=ColorList)


def readskin():
    cf = config.plugins.ARD.SkinColor.value.split(',')
    skin = ''
    try:
        with open(SKINFILE, 'r') as f:
            root = Et.parse(f).getroot()
        for element in root:
            if element.tag == "screen" and element.attrib['name'] == cf[0]:
                skin = ensure_str(Et.tostring(element))
    except (IOError, Et.ParseError):
        return ''
    return skin.strip().replace('#050a1232', cf[1]).replace('#1502050e', cf[2]).replace('{picpath}', PLUGINPATH + 'img/')


def geturl(url):
    try:
        response = requests.get(url, headers=UA, timeout=10)
        return response.content
    except Exception:
        return ''


def quality(t):
    q = {'0': 'Niedrige Qualität', '1': 'Mittlere Qualität', '2': 'hohe Qualität', '3': 'Sehr hohe Qualität', '4': 'Full HD'}
    if t in q:
        return q[t]
    return t


def cleanurl(t):
    return t.replace('ä', '%C3%A4').replace('ö', '%C3%B6').replace('ü', '%C3%BC').replace('ß', '%C3%9F').replace('\\', '/').replace(' ', '%20').strip()


def dateTime2(dt):
    try:
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
        skin = readskin()
        self.skin = skin
        Screen.__init__(self, session)
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'DirectionActions', 'ChannelSelectBaseActions', 'MovieSelectionActions'], {"contextMenu": self.ARDSetup, "green": self.Download, "red": self.close, "blue": self.Home, 'up': self.up, 'down': self.down, 'left': self.left, 'right': self.right, 'nextBouquet': self.p_up, 'prevBouquet': self.p_down, 'ok': self.ok, 'cancel': self.exit}, -1)
        self['movielist'] = List()
        self['cover'] = Pixmap()
        self['handlung'] = ScrollLabel()
        self.HISTORY = [('MENU', '')]
        self['DownloadLabel'] = ScrollLabel()
        self['progress'] = ProgressBar()
        self['progress'].hide()
        self.DL_File = None
        if not exists('/tmp/cover/'):
            mkdir('/tmp/cover/')
        self.onLayoutFinish.append(self.HauptMenu)

    def ARDSetup(self):
        self.session.open(ARDConfigScreen)

    def HauptMenu(self, index='0'):
        self.searchtxt = ''
        self.PROGRAMM = 'ard'
        menu = [('MENU', 'ARD Mediathek - Start', URL_HOME % self.PROGRAMM, '', PLUGINPATH + '/img/' + 'home.png', ''),
                ('MENU', 'Entdecken', API_URL + 'pages/ard/editorial/entdecken?embedded=true', '', PLUGINPATH + '/img/' + 'endecken.png', ''),
                ('SenderMenu', 'Sender', 'SenderMenu', '', PLUGINPATH + '/img/' + 'sender.png', ''),
                ('ProgrammMenu', 'Sendung verpasst', 'ProgrammMenu', '', PLUGINPATH + '/img/' + 'programm.png', ''),
                ('MENU', 'Sendungen A-Z', URL_AZ % 'ard', '', PLUGINPATH + '/img/' + 'az.png', ''),
                ('MENU', 'LIVE', API_URL + 'widgets/ard/editorials/4hEeBDgtx6kWs6W6sa44yY?pageNumber=0&pageSize=24&embedded=true', '', PLUGINPATH + '/img/' + 'live.png', ''),
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

    def Home(self):
        self.HISTORY = [('MENU', '')]
        self.HauptMenu()

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
            system('rm -rf /tmp/cover')
            self.close()

    def SenderMenu(self, index='0', mt=''):
        URL = 'https://images.ardmediathek.de/vrwifdtrtsys/'
        menu = [(mt, 'Alpha', 'alpha', '', URL + '4hn8C8lrTimEuYSiee6Y0/ca7f2eaf0f75c01412a54ad002b62d05/livestream_ard-alpha.jpg?w=360', ''),
                (mt, 'Arte', 'arte', '', URL + '6tne4hKLnD9RGHNDolSKu4/c3ca716c02da066a135777b7f5ef5a33/arte_livestream_bild.png?w=360', ''),
                (mt, 'BR', 'br', '', URL + '6G1LV7aj5okmlUx0PoJ3g4/bc05260c402272eb4458f141c43f51f9/BR_Fernsehen.jpg?w=360', ''),
                (mt, 'Das Erste', 'daserste', '', URL + '43ntcnDlAiL2fbBuR4AXlq/51487971e825f5b9968cf3f9c2c81ec5/8.jpg?w=360', ''),
                (mt, 'HR', 'hr', '', URL + 'xMGOYhXKGnS4ZujacpB3n/7f67e1d482aa9c80f56db652369532a6/hr-Logo-Livestream-16-9.jpg?w=360', ''),
                (mt, 'KIKA', 'kika', '', 'https://api.ardmediathek.de/image-service/images/urn:ard:image:34a231a870f22c6d?w=360&ch=865612894cbd4d56', ''),
                (mt, 'MDR', 'mdr', '', URL + '70UZvshUMZ3esCGEMGVgVJ/0bc665b6b1a4874f0d767e8931a65ac8/livestream.jpg?w=360', ''),
                (mt, 'NDR', 'ndr', '', 'https://api.ardmediathek.de/image-service/images/urn:ard:image:8d587d540cd01169?w=360', ''),
                (mt, 'One', 'one', '', URL + '1N26MHa704lWZqiIPMR4nn/65260642a6afef4152b10cb2a37b1f34/ONE_Livestream.jpg?w=360', ''),
                (mt, 'Phoenix', 'phoenix', '', URL + '5cTm9Nwre7F41oMKBdbs9h/1bf04723d680dbf9a4e8e9fb5afc4da9/phoenixlogo_169.jpg?w=360', ''),
                (mt, 'Radio Bremen', 'radiobremen', '', URL + '4RpI2I7QHu2M2OysQwaC8K/d1318b6f73be6bb1303f622e174f7940/radiobremen.jpg?w=360', ''),
                (mt, 'RBB', 'rbb', '', URL + 'ca3lrftfNOollG4Ts3bIF/187d062535a5263e0f4087e5b472f3fd/rbb_Logo_roter_Hintergrund_wei_es_Logo_1920.jpg?w=360', ''),
                (mt, 'SR', 'sr', '', URL + '5JuVdzmKl2u6WQIW8qeGKa/6fe4ba39ffa9a94c475b11f4e8733e74/livestream_sr.png?w=360', ''),
                (mt, 'SWR', 'swr', '', URL + '4apl4dmokQmuWOEltdMXoZ/a36e2c6a58884f5c0488b34b3b180a2d/SWR_Logo_fuer_Livestream_Mediathek.jpg?w=360', ''),
                (mt, 'Tagesschau24', 'tagesschau24', '', URL + '7tfD9nWFpPlGzvyuDGIb7v/e763406fd70a8302ea6b920c719291f4/welt_ts24.jpg?w=360', ''),
                (mt, 'WDR', 'wdr', '', URL + '5r6IfjTgc4h3JrYZkSdbyY/0e11ab1a8bbc67d2d4e91844306532c1/wdr-logo-128_gross.jpg?w=360', '')]
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
            url = API_URL + 'compilations/%s/pastbroadcasts?startDateTime=%s&endDateTime=%s&pageSize=200' % (self.PROGRAMM, start, end)
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
            if js.get('type') in ('external'):
                continue
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
                im = {}
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
            elif js.get('type') == 'region_gridlist':
                liste.append(('WEITER', ensure_str(title) + ' ' + config.plugins.ARD.Region.value, ensure_str(API_URL + 'widgets/ard/region/6YgzSO0C7huVaGgzM5mq19/%s?pageNumber=0&pageSize=100&embedded=true') % config.plugins.ARD.Region.value, ensure_str(plot), cleanurl(img), duration))
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

    def Download(self):
        if self.DL_File:
            self.session.openWithCallback(self.DL_Stop, MessageBox, 'möchten Sie den Download abbrechen?', default=True, type=MessageBox.TYPE_YESNO)
        else:
            url = self['movielist'].getCurrent()[2]
            html = ensure_str(geturl(url))
            if 'blockedByFsk":true' in html:
                self.session.open(MessageBox, 'Das Video ist nicht für Kinder und Jugendliche geeignet und kann erst nach 22 Uhr Download werden.', MessageBox.TYPE_INFO)
                return
            filename = "".join(i for i in self['movielist'].getCurrent()[1] if i not in r"\/:*?<>|")
            liste = []
            links = re.compile(r'_height":(\d+).*?_stream":"([^"]+).*?width":(\d+)', re.DOTALL).findall(html)
            if links:
                for height, url, width in links:
                    if '.m3u8' in url:
                        continue
                    if url.startswith('//'):
                        url = 'https:' + url
                    liste.append((filename + '(' + str(width) + 'x' + str(height) + ')' + '.mp4', url))
            sub = re.compile(r'_subtitleUrl":"([^"]+)', re.DOTALL).findall(html)
            if sub:
                for url in sub:
                    liste.append((filename + '.srt', url))
            if len(liste) > 1:
                self.session.openWithCallback(self.DL_Start, ChoiceBox, title='Download starten?', list=liste)

    def DL_Start(self, url):
        if url:
            self.DL_File = str(config.plugins.ARD.savetopath.value) + str(url[0])
            url = url[1]
            if exists(self.DL_File):
                self.session.open(MessageBox, 'Datei ist schon vorhanden', MessageBox.TYPE_INFO)
            else:
                self['progress'].show()
                self['DownloadLabel'].show()
                self.downloader = downloadWithProgress(url, self.DL_File)
                self.downloader.addProgress(self.DL_progress)
                self.downloader.addEnd(self.DL_finished)
                self.downloader.addError(self.DL_failed)
                self.downloader.start()

    def DL_Stop(self, answer):
        if answer:
            self.downloader.stop()
            if exists(self.DL_File):
                unlink(self.DL_File)
            self.DL_File = None
            self['progress'].hide()
            self['DownloadLabel'].hide()
            self.infos()

    def DL_finished(self, s=''):
        self['progress'].hide()
        self['DownloadLabel'].hide()
        self.DL_File = None
        self.session.open(MessageBox, 'Download erfolgreich %s' % s, MessageBox.TYPE_INFO, timeout=5)

    def DL_failed(self, error):
        self['progress'].hide()
        self['DownloadLabel'].hide()
        self.downloader.stop()
        if exists(self.DL_File):
            unlink(self.DL_File)
        self.DL_File = None
        self.session.open(MessageBox, 'Download-Fehler %s' % error, MessageBox.TYPE_INFO)

    def DL_progress(self, recvbytes, totalbytes):
        try:
            self['DownloadLabel'].setText(str(recvbytes // 1024 // 1024) + 'MB/' + str(totalbytes // 1024 // 1024) + 'MB')
            self['progress'].setValue(int(100 * recvbytes // totalbytes))
        except Exception:
            pass

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
            path = join('/tmp/cover', 'bild')
            with open(path, 'wb') as f:
                f.write(data)
            self.get_cover(path)
        except OSError:
            pass

    def get_cover(self, img):
        picload = ePicLoad()
        self['cover'].instance.setPixmap(gPixmapPtr())
        scale = AVSwitch().getFramebufferScale()
        size = self['cover'].instance.size()
        picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, '#FF000000'))
        if picload.startDecode(img, 0, 0, False) == 0:
            ptr = picload.getData()
            if ptr is not None:
                self['cover'].instance.setPixmap(ptr)
                self['cover'].show()


class MoviePlayer2(MoviePlayer):
    ENABLE_RESUME_SUPPORT = True

    def __init__(self, session, service):
        MoviePlayer.__init__(self, session, service)
        self.skinName = 'MoviePlayer'

    def up(self):
        pass

    def down(self):
        pass

    def leavePlayer(self):
        setResumePoint(self.session)
        self.close()

    def leavePlayerOnExit(self):
        self.leavePlayer()

    def doEofInternal(self, playing):
        if not playing or not self.execing:
            return
        self.close()


class ARDConfigScreen(ConfigListScreen, Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.title = ('Einstellungen')
        self.session = session
        self.skinName = ['Setup']
        self['key_red'] = StaticText('Abbrechen')
        self['key_green'] = StaticText('Speichern')
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions'], {'cancel': self.cancel, 'red': self.cancel, 'ok': self.ok, 'green': self.save}, -2)
        ConfigListScreen.__init__(self, [], session=session)
        self.ConfigList()

    def ConfigList(self):
        if 'config' not in self:
            return
        self['config'].list = [getConfigListEntry('Download-Verzeichnis:', config.plugins.ARD.savetopath), getConfigListEntry('Skin', config.plugins.ARD.SkinColor), getConfigListEntry('Unsere Region', config.plugins.ARD.Region)]

    def save(self):
        self.keySave()
        self.close()

    def cancel(self):
        self.close()

    def ok(self):
        if self['config'].getCurrent()[1] == config.plugins.ARD.savetopath:
            DLdir = config.plugins.ARD.savetopath.value
            self.session.openWithCallback(self.DL_Path, DirBrowser, DLdir)

    def DL_Path(self, res):
        self['config'].setCurrentIndex(0)
        if res:
            config.plugins.ARD.savetopath.value = res


class DirBrowser(Screen):
    def __init__(self, session, DLdir):
        Screen.__init__(self, session)
        self.skinName = ['FileBrowser']
        self['key_red'] = StaticText('Abbrechen')
        self['key_green'] = StaticText('Speichern')
        if not exists(DLdir):
            DLdir = '/'
        self.filelist = FileList(DLdir, showFiles=False)
        self['filelist'] = self.filelist
        self['FilelistActions'] = ActionMap(['SetupActions', 'ColorActions'], {'cancel': self.cancel, 'red': self.cancel, 'ok': self.ok, 'green': self.save}, -2)

    def ok(self):
        if self.filelist.canDescent():
            self.filelist.descent()

    def save(self):
        fullpath = self["filelist"].getSelection()[0]
        if fullpath is not None and fullpath.endswith("/"):
            self.close(fullpath)

    def cancel(self):
        self.close(False)
