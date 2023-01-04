# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta
from json import loads
import os
import requests
from six import ensure_str
from six.moves.urllib.parse import quote_plus
from twisted.internet.reactor import callInThread
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigDirectory
from Components.FileList import FileList
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from enigma import eTimer, eServiceReference, ePicLoad, gPixmapPtr, getDesktop
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBarGenerics import setResumePoint
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Downloader import DownloadWithProgress
config.plugins.ardzdf = ConfigSubsection()
config.plugins.ardzdf.savetopath = ConfigDirectory(default='/media/hdd/movie/')
PLUGINPATH = '/usr/lib/enigma2/python/Plugins/Extensions/ZDFMediathek/'
FHD = getDesktop(0).size().height() > 720
if FHD:
    skin = PLUGINPATH + 'skin_FHD.xml'
else:
    skin = PLUGINPATH + 'skin_HD.xml'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Accept-Language': 'de,en-US;q=0.7,en;q=0.3', 'Accept-Encoding': 'gzip, deflate'}
API_URL = 'https://zdf-cdn.live.cellular.de/mediathekV2/'


def geturl(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        return response.content
    except Exception as e:
        print(str(e))
        return ''


class ZDFMediathek(Screen):
    def __init__(self, session):
        with open(skin, "r") as file:
            self.skin = file.read()
        Screen.__init__(self, session)
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'DirectionActions', 'ChannelSelectBaseActions', 'MovieSelectionActions'], {"contextMenu": self.ZDFSetup, "green": self.Download, "red": self.close, "blue": self.Home, 'up': self.up, 'down': self.down, 'left': self.left, 'right': self.right, 'nextBouquet': self.p_up, 'prevBouquet': self.p_down, 'ok': self.ok, 'cancel': self.exit}, -1)
        self['movielist'] = List()
        self['cover'] = Pixmap()
        self['handlung'] = ScrollLabel()
        self['DownloadLabel'] = ScrollLabel()
        self['progress'] = ProgressBar()
        self['progress'].hide()
        self.downloader = None
        self.HISTORY = [('MENU', '', '', '')]
        if not os.path.exists('/tmp/cover/'):
            os.mkdir('/tmp/cover/')
        self.onLayoutFinish.append(self.HauptMenu)

    def ZDFSetup(self):
        self.session.open(ZDFConfigScreen)

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
            self.session.open(MessageBox, 'Achtung! Livestreams werden in der aktuellen Version noch nicht unterstützt.', MessageBox.TYPE_INFO)
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

    def Download(self):
        if self.downloader:
            self.session.openWithCallback(self.DownloadStop, MessageBox, 'möchten Sie den Download abbrechen?', default=True, type=MessageBox.TYPE_YESNO)
        else:
            url = self['movielist'].getCurrent()[2]
            data = ensure_str(geturl(url))
            if 'fskCheck":true' in data:
                self.session.open(MessageBox, 'Das Video ist nicht für Kinder und Jugendliche geeignet und kann erst nach 22 Uhr abgespielt werden.', MessageBox.TYPE_INFO)
                return
            liste = []
            filename = "".join(i for i in self['movielist'].getCurrent()[1] if i not in r"\/:*?<>|")
            if data:
                data = loads(data)
            if data.get('document'):
                data = data.get('document')
                if data.get('formitaeten'):
                    data = data.get('formitaeten')
                    for js in data:
                        url = js.get('url')
                        if '.m3u8' in url:
                            continue
                        url = js.get('url').replace('1628k_p13v15', '3360k_p36v15').replace('808k_p11v15', '2360k_p35v15').replace('508k_p9v15', '808k_p11v15')
                        q = filename
                        if js.get('language'):
                            q += '(' + str(js.get('language').upper()) + ')'
                        if js.get('class', '') == 'ad':
                            q += '(AD)'
                        if js.get('quality'):
                            q += '(' + str(js.get('quality').upper()) + ')'
                        liste.append((q + '.mp4', url))
            if len(liste) > 1:
                self.session.openWithCallback(self.Download2, ChoiceBox, title='Download starten?', list=liste)

    def Download2(self, url):
        if url:
            filename = str(config.plugins.ardzdf.savetopath.value) + str(url[0])
            url = url[1]
            if os.path.exists(filename):
                self.session.open(MessageBox, 'Datei schon vorhanden', MessageBox.TYPE_INFO)
            else:
                self['progress'].show()
                self['DownloadLabel'].show()
                self.downloader = DownloadWithProgress(url, filename)
                self.downloader.addProgress(self.http_progress)
                self.downloader.addEnd(self.http_finished)
                self.downloader.addError(self.http_failed)
                self.downloader.start()

    def DownloadStop(self, answer):
        if answer:
            self.downloader.stop()
            self.downloader = None
            self['progress'].hide()
            self['DownloadLabel'].hide()
            self.infos()

    def http_finished(self, s=''):
        self['progress'].hide()
        self['DownloadLabel'].hide()
        self.downloader = None
        self.session.open(MessageBox, 'Download erfolgreich ' + s, MessageBox.TYPE_INFO, timeout=5)

    def http_failed(self, error):
        self['progress'].hide()
        self['DownloadLabel'].hide()
        self.downloader.stop()
        self.session.open(MessageBox, 'Download-Fehler ' + str(error), MessageBox.TYPE_INFO)

    def http_progress(self, recvbytes, totalbytes):
        try:
            self['DownloadLabel'].setText(str(recvbytes // 1024 // 1024) + 'MB/' + str(totalbytes // 1024 // 1024) + 'MB')
            self['progress'].setValue(int(100 * recvbytes // totalbytes))
        except Exception:
            pass

    def Home(self):
        self.HISTORY = [('MENU', '', '', '')]
        self.HauptMenu()

    def exit(self):
        if len(self.HISTORY) > 1:
            Index = self.HISTORY[-1][2]
            self.HISTORY.pop()
            Type = self.HISTORY[-1][0]
            url = self.HISTORY[-1][1]
            if Type == 'LISTE':
                self.load(url, Index)
            elif Type == 'TEASER':
                self.teaser(url, self.HISTORY[-1][3], Index)
            elif Type == 'STAGE':
                self.Stage(url, Index)
            elif Type == 'BROADCAST':
                self.Broadcast(Index)
            elif Type == 'MENU':
                self.HauptMenu(Index)
            else:
                self.session.open(MessageBox, Type, MessageBox.TYPE_INFO)
            self.infos()
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
            url = API_URL + 'search?q=%s' % quote_plus(search)
            self.HISTORY.append(('LISTE', url, self['movielist'].getIndex(), ''))
            self.load(url, index='0')

    def Broadcast(self, index='0'):
        liste = []
        now = datetime.now()
        for i in range(0, 7):
            datum = (now + timedelta(- i)).strftime('%d-%m-%Y')
            url = API_URL + 'broadcast-missed/%s' % (now + timedelta(- i)).strftime('%Y-%m-%d')
            liste.append(('LISTE', ensure_str(datum), url, '', PLUGINPATH + '/img/' + 'programm.png', '', '', index))
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
                    for tc in data:
                        tc = self.teaserContent(tc)
                        if tc:
                            liste.append((tc))
            else:
                self.session.open(MessageBox, 'Kein Eintrag vorhanden', MessageBox.TYPE_INFO)
                return
            tindex = -1
            for js in data:
                tindex += 1
                if not js.get('name', '') and len(js.get('teaser', '')) > 0:
                    te = js.get('teaser')
                    if te:
                        for tc in te:
                            tc = self.teaserContent(tc)
                            if tc:
                                liste.append((tc))
                if not js.get('name', '') or len(js.get('teaser', '')) == 0:
                    continue
                title = js.get('name')
                img = self.ImageRead(js.get('teaser')[0])
                if js.get('liveStream'):
                    liste.append(('LIVE', ensure_str(title), url, '', (img), '', '', tindex))
                else:
                    liste.append(('TEASER', ensure_str(title), (url), '', (img), '', '', tindex))
            if liste:
                if html.get('nextPageUrl'):
                    liste.append(('LISTE', 'Next Page', html.get('nextPageUrl'), '', PLUGINPATH + '/img/' + 'nextpage.png', '', '', ''))
                self['movielist'].setList(liste)
                self['movielist'].setIndex(int(index))
        else:
            self.session.open(MessageBox, 'Kein Eintrag vorhanden', MessageBox.TYPE_INFO)

    def teaserContent(self, js):
        if js.get('type') == 'externalUrl' or js.get('currentVideoType') == 'novideo':
            return None
        if js.get('seasonNumber'):
            title = js.get('headline') + ' - ' + 'S{:02d}E{:02d}'.format(int(js.get('seasonNumber', '0')), int(js.get('episodeNumber', '0')))
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
            Type = 'PLAY'
        else:
            Type = 'LISTE'
        return Type, ensure_str(title), url, ensure_str(plot), img, duration, '', ''

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

        for tc in teaser:
            tc = self.teaserContent(tc)
            if tc:
                liste.append((tc))
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
                        url = js.get('url').replace('1628k_p13v15', '3360k_p36v15').replace('808k_p11v15', '2360k_p35v15').replace('508k_p9v15', '808k_p11v15')
                        q += '(MP4)'
                    if js.get('language'):
                        q += ' ' + js.get('language').upper()
                    if js.get('class', '') == 'ad':
                        q += ' (AD)'
                    liste.append((ensure_str(q), url))
        if len(liste) > 1:
            self.session.openWithCallback(self.Play2, ChoiceBox, title='Wiedergabe starten?', list=sorted(liste, reverse=True, key=str))
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
            path = os.path.join('/tmp/cover', 'bild')
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
        setResumePoint(self.session)
        self.close()

    def doEofInternal(self, playing):
        if not self.execing:
            return
        if not playing:
            return
        self.close()


class ZDFConfigScreen(ConfigListScreen, Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.title = ('Einstellungen')
        self.session = session
        self.skinName = ['Setup']
        self['key_red'] = StaticText('Speichern')
        self['key_green'] = StaticText('OK')
        self['description'] = Label('')
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions'], {'cancel': self.cancel, 'red': self.cancel, 'ok': self.ok, 'green': self.ok}, -2)
        ConfigListScreen.__init__(self, [], session=session)
        self.ConfigList()

    def ConfigList(self):
        if 'config' not in self:
            return
        self.list = []
        self.list.append(getConfigListEntry('Download-Verzeichnis:', config.plugins.ardzdf.savetopath))
        self['config'].list = self.list

    def cancel(self):
        self.keySave()
        self.close()

    def ok(self):
        if self['config'].getCurrent()[1] == config.plugins.ardzdf.savetopath:
            downloaddir = config.plugins.ardzdf.savetopath.value
            self.session.openWithCallback(self.downloadPath, DirBrowser, downloaddir)

    def downloadPath(self, res):
        self['config'].setCurrentIndex(0)
        if res:
            config.plugins.ardzdf.savetopath.value = res


class DirBrowser(Screen):
    def __init__(self, session, downloaddir):
        Screen.__init__(self, session)
        self.skinName = ['FileBrowser']
        self['key_green'] = StaticText('Benutzen')
        self['key_red'] = StaticText('Abbrechen')

        if not os.path.exists(downloaddir):
            downloaddir = '/tmp/'
        self['filelist'] = FileList(downloaddir, showFiles=False)
        self['FilelistActions'] = ActionMap(['SetupActions', 'ColorActions'], {'cancel': self.cancel, 'red': self.cancel, 'ok': self.ok, 'green': self.use}, -2)

    def ok(self):
        if self['filelist'].canDescent():
            self['filelist'].descent()

    def use(self):
        fullpath = self["filelist"].getSelection()[0]
        if fullpath is not None and fullpath.endswith("/"):
            self.close(fullpath)

    def cancel(self):
        self.close(False)
