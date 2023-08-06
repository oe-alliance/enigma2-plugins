# -*- coding: UTF-8 -*-
from os import mkdir, unlink, path
from datetime import datetime, timedelta
import json
import xml.etree.ElementTree as Et
import re
import threading
import requests
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigDirectory, ConfigSelection, ConfigYesNo, configfile
from Components.FileList import FileList
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from enigma import eServiceReference, ePicLoad, gPixmapPtr, getDesktop, addFont, eConsoleAppContainer
from Screens.ChoiceBox import ChoiceBox
from Screens.Console import Console
from Screens import InfoBarGenerics
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from six import ensure_str
from six.moves.urllib.parse import quote_plus

config.plugins.SRF = ConfigSubsection()
config.plugins.SRF.savetopath = ConfigDirectory(default="/media/hdd/movie/")
config.plugins.SRF.SaveResumePoint = ConfigYesNo(default=False)
config.plugins.SRF.AUTOPLAY = ConfigYesNo(default=False)
PLUGINPATH = "/usr/lib/enigma2/python/Plugins/Extensions/SRFMediathek/"
FHD = getDesktop(0).size().height() > 720
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0"
TMPIC = "/tmp/cover/bild.jpg"
SKINFILE = PLUGINPATH + "skin_FHD.xml" if FHD else PLUGINPATH + "skin_HD.xml"
FONT = "/usr/share/fonts/LiberationSans-Regular.ttf"
if not path.exists(FONT):
    FONT = "/usr/share/fonts/nmsbd.ttf"
addFont(FONT, "SRegular", 100, False)
API_URL = "https://il.srgssr.ch/integrationlayer"
ColorList = [("glass,#40000000,#5a000000,#37cccccc", "Black Glass"), ("glass,#5a082567,#5a000000,#37cccccc", "SapphireBlue Glass"), ("glass,#5a080828,#5a000000,#37cccccc", "MagentaBlue Glass"), ("glass,#e615d7b6,#5a000000,#37cccccc", "PaleGreen Glass"), ("glass,#5aa0785a,#5a000000,#37cccccc", "Chamoisee Glass"), ("transparent,#050a1232,#1502050e,#05192d7c", "DarkBlue Transparent"), ("transparent,#05000000,#15000000,#606060", "BlackGray Transparent"), ("transparent,#05000000,#15000000,#ffff00", "BlackYellow Transparent"), ("transparent,#1a104485,#3D104485,#1aC0C0C0", "BrightBlue Transparent"), ("transparent,#1a746962,#1502050e,#1a746962", "BrownBlue Transparent"), ("MiniTV,#104485,#0c366a,#C0C0C0", "BrightBlue MiniTV"), ("MiniTV,#0a1232,#02050e,#192d7c", "DarkBlue MiniTV"), ("MiniTV,#000000,#080808,#606060", "BlackGray MiniTV"), ("MiniTV,#000000,#080808,#ffff00", "BlackYellow MiniTV"), ("MiniTV,#746962,#02050e,#746962", "BrownBlue MiniTV")]
config.plugins.SRF.SkinColor = ConfigSelection(default="glass,#40000000,#5a000000,#37cccccc", choices=ColorList)


def callInThread(func, *args, **kwargs):
    thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    thread.start()


def readskin():
    cf = config.plugins.SRF.SkinColor.value.split(",")
    skin = ""
    try:
        with open(SKINFILE, "r") as f:
            root = Et.parse(f).getroot()
        for element in root:
            if element.tag == "screen" and element.attrib["name"] == cf[0]:
                skin = ensure_str(Et.tostring(element))
    except (IOError, Et.ParseError):
        return ""
    return skin.strip().replace("{col1}", cf[1]).replace("{col2}", cf[2]).replace("{col3}", cf[3]).replace("{picpath}", PLUGINPATH + "img/")


def geturl(url, headers=None, data=None, timeout=10, verify=True):
    try:
        if not headers:
            headers = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8", "Accept-Language": "de,en-US;q=0.7,en;q=0.3", "Accept-Encoding": "gzip, deflate"}
        if data:
            r = requests.post(url, headers=headers, data=data, timeout=timeout, verify=verify)
        else:
            r = requests.get(url, headers=headers, timeout=timeout, verify=verify)
        return r.content
    except requests.RequestException:
        return ""


def format_datetime(dt):
    try:
        s = ""
        if "validFrom" in dt:
            valid_from = datetime.strptime(dt["validFrom"][:19], "%Y-%m-%dT%H:%M:%S")
            s += "Gesendet am %s\n" % valid_from.strftime("%d.%m.%Y %H:%M")
        if "validTo" in dt:
            valid_to = datetime.strptime(dt["validTo"][:19], "%Y-%m-%dT%H:%M:%S")
            s += "Verfügbar bis %s\n" % valid_to.strftime("%d.%m.%Y %H:%M")
        return s
    except (ValueError, KeyError):
        return ""


def sortList(txt):
    return sorted(txt, key=lambda text: int(re.compile(r"(\d+)x", re.DOTALL).findall(text[0])[0]) if re.compile(r"(\d+)x", re.DOTALL).findall(str(text[0])) else 0, reverse=True)


class SRFMediathek(Screen):
    def __init__(self, session):
        skin = readskin()
        self.skin = skin
        Screen.__init__(self, session)
        self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "ChannelSelectBaseActions", "MenuActions"], {"menu": self.SRFSetup, "green": self.Download, "red": self.close, "blue": self.HauptMenu, "up": self.up, "down": self.down, "left": self.left, "right": self.right, "nextBouquet": self.p_up, "prevBouquet": self.p_down, "ok": self.ok, "cancel": self.exit}, -1)
        self["movielist"] = List()
        self["cover"] = Pixmap()
        self["handlung"] = ScrollLabel()
        self.HISTORY = [("MENU", "")]
        self["DownloadLabel"] = ScrollLabel()
        self["PluginName"] = ScrollLabel("SRF Mediathek v0.7")
        self["progress"] = ProgressBar()
        self["progress"].hide()
        self.PROGRAMM = "srf"
        self.DL_File = None
        self.totalDuration = 0
        if not path.exists("/tmp/cover/"):
            mkdir("/tmp/cover/")
        self.onLayoutFinish.append(self.HauptMenu)

    def SRFSetup(self):
        self.session.open(SRFConfigScreen)

    def HauptMenu(self, index="0"):
        self.PROGRAMM = "srf"
        self.HISTORY = [("MENU", "")]
        self.searchtxt = ""
        menu = [("MENU", "SRF Mediathek", API_URL + "/2.0/%s/page/landingPage/byProduct/PLAY_VIDEO?isPublished=true&vector=APPPLAY" % self.PROGRAMM, "", PLUGINPATH + "/img/home.png", ""), ("MENU", "Kategorien", API_URL + "/2.0/%s/topicList/tv?vector=APPPLAY" % self.PROGRAMM, "", PLUGINPATH + "/img/endecken.png", ""), ("MENU", "A-Z", API_URL + "/2.0/%s/showList/tv/alphabetical?pageSize=unlimited&vector=APPPLAY" % self.PROGRAMM, "", PLUGINPATH + "/img/az.png", ""), ("VERPASST", "Sendung verpasst", "VERPASST", "", PLUGINPATH + "/img/programm.png", ""), ("MENU", "Am meisten gesuchte", API_URL + "/2.0/%s/showList/tv/mostClickedSearchResults?vector=portalplay" % self.PROGRAMM, "", PLUGINPATH + "/img/mostClick.png", ""), ("SENDER", "Sender", "", "", "", ""), ("Suche", "Suche", "", "", PLUGINPATH + "/img/suche.png", "")]
        self["movielist"].setList(menu)
        self["movielist"].setIndex(int(index))
        self.infos()

    def Sender(self, index="0"):
        menu = [("CHANNEL", "RTS (french)", "rts", "", "", ""), ("CHANNEL", "RSI (italian)", "rsi", "", "", ""), ("CHANNEL", "RTR (rätoromanische)", "rtr", "", "", ""), ("CHANNEL", "SWI (englisch)", "swi", "", "", "")]
        self["movielist"].setList(menu)
        self["movielist"].setIndex(int(index))

    def Channel(self, index="0"):
        if "swi" in self.PROGRAMM:
            menu = [("MENU", "%s Mediathek" % self.PROGRAMM.upper(), "%s/2.0/%s/page/landingPage/byProduct/PLAY_VIDEO?isPublished=true&vector=APPPLAY" % (API_URL, self.PROGRAMM), "", "%s/img/home.png" % PLUGINPATH, ""), ("Suche", "Suche", "", "", "%s/img/suche.png" % PLUGINPATH, "")]
        else:
            menu = [("MENU", "%s Mediathek" % self.PROGRAMM.upper(), "%s/2.0/%s/page/landingPage/byProduct/PLAY_VIDEO?isPublished=true&vector=APPPLAY" % (API_URL, self.PROGRAMM), "", "%s/img/home.png" % PLUGINPATH, ""), ("MENU", "Kategorien", "%s/2.0/%s/topicList/tv?vector=APPPLAY" % (API_URL, self.PROGRAMM), "", "%s/img/endecken.png" % PLUGINPATH, ""), ("MENU", "A-Z", "%s/2.0/%s/showList/tv/alphabetical?pageSize=unlimited&vector=APPPLAY" % (API_URL, self.PROGRAMM), "", "%s/img/az.png" % PLUGINPATH, ""), ("VERPASST", "Sendung verpasst", "VERPASST", "", "%s/img/programm.png" % PLUGINPATH, ""), ("MENU", "Am meisten gesuchte", "%s/2.0/%s/showList/tv/mostClickedSearchResults?vector=portalplay" % (API_URL, self.PROGRAMM), "", "%s/img/mostClick.png" % PLUGINPATH, ""), ("Suche", "Suche", "", "", "%s/img/suche.png" % PLUGINPATH, "")]
        self["movielist"].setList(menu)
        self["movielist"].setIndex(int(index))

    def ok(self):
        Current = self["movielist"].getCurrent()[0]
        if Current == "Suche":
            self.session.openWithCallback(self.search, VirtualKeyBoard, title="SRF Mediathek Suche")
        elif Current == "PLAY":
            self.Play()
        else:
            Index = self["movielist"].getIndex()
            url = self["movielist"].getCurrent()[2]
            if Current in ("MENU", "NEXT"):
                self.Srf(url)
            elif Current == "SENDER":
                url = "SENDER"
                self.Sender()
            elif Current == "CHANNEL":
                url = "CHANNEL"
                self.PROGRAMM = self["movielist"].getCurrent()[2]
                self.Channel()
            elif Current == "VERPASST":
                self.Verpasst()
            else:
                return
            self.HISTORY.append((url, Index))

    def exit(self):
        if len(self.HISTORY) > 1:
            Index = self.HISTORY[-1][1]
            self.HISTORY.pop()
            url = self.HISTORY[-1][0]
            if url.startswith("http"):
                self.Srf(url, Index)
            elif url == "MENU":
                self.HauptMenu(Index)
            elif url == "SENDER":
                self.Sender(Index)
            elif url == "CHANNEL":
                self.Channel(Index)
            elif url == "VERPASST":
                self.Verpasst(Index)
        else:
            if path.exists(TMPIC):
                unlink(TMPIC)
            self.close()

    def Verpasst(self, index="0"):
        now = datetime.now()
        liste = []
        for i in range(0, 7):
            start = now + timedelta(-i)
            if i == 0:
                title = "HEUTE"
            elif i == 1:
                title = "GESTERN"
            else:
                title = start.strftime("%d.%m.%Y")
            url = "%s/2.0/%s/mediaList/video/episodesByDate/%s?pageSize=40&vector=APPPLAY" % (API_URL, self.PROGRAMM, start.strftime("%Y-%m-%d"))
            liste.append(("NEXT", title, ensure_str(url), "", "", ""))
        self["movielist"].setList(liste)
        self["movielist"].setIndex(int(index))
        self.infos()

    def search(self, search):
        if search:
            self.searchtxt = search
            url = "%s/2.0/%s/searchResultMediaList?q=%s&sortBy=default&includeSuggestions=false&includeAggregations=false&pageSize=40&vector=APPPLAY" % (API_URL, self.PROGRAMM, quote_plus(self.searchtxt))
            Index = self["movielist"].getIndex()
            self.HISTORY.append((url, Index))
            self.Srf(url, index="0")

    def Srf(self, link, index="0"):
        liste = []
        data = geturl(link)
        if data:
            data = json.loads(ensure_str(data))
        else:
            self.session.open(MessageBox, "Fehler beim Lesen der Daten", MessageBox.TYPE_INFO)
            self.HISTORY.pop()
            return
        if data.get("topicList"):
            data2 = data.get("topicList")
        elif data.get("showList"):
            data2 = data.get("showList")
        elif data.get("sectionList"):
            data2 = data.get("sectionList")
        elif data.get("mediaList"):
            data2 = data.get("mediaList")
        elif data.get("searchResultMediaList"):
            data2 = data.get("searchResultMediaList")
        else:
            self.session.open(MessageBox, "Kein Eintrag vorhanden", MessageBox.TYPE_INFO)
            self.HISTORY.pop()
            return

        for js in data2:
            url = ""
            title = js.get("title", "")
            if js.get("urn"):
                url = js.get("urn", "")
                if "video" in url or "audio" in url:
                    url = "%s/2.1/mediaComposition/byUrn/%s?onlyChapters=false&vector=APPPLAY" % (API_URL, url)
                elif "show" in url:
                    url = "%s/2.0/mediaList/latest/byShowUrn/urn:srf:%s?pageSize=40&vector=APPPLAY" % (API_URL, url)
                elif "topic" in url:
                    url = "%s/2.0/%s/page/byTopicUrn/%s?isPublished=true&vector=APPPLAY" % (API_URL, self.PROGRAMM, url)
            elif js.get("id"):
                if js.get("sectionType") == "MediaSection":
                    url = "%s/2.0/%s/section/mediaSection/%s?isPublished=true&vector=APPPLAY" % (API_URL, self.PROGRAMM, js.get("id"))
                if js.get("sectionType") == "ShowSection":
                    url = "%s/2.0/%s/section/showSection/%s?isPublished=true&vector=APPPLAY" % (API_URL, self.PROGRAMM, js.get("id"))
                if js.get("representation"):
                    js = js.get("representation", "")
                if "HeroStage" in js.get("name", ""):
                    title = "Stage"
                elif js.get("properties"):
                    js = js.get("properties", "")
                if js.get("title"):
                    title = js.get("title")
            if url.startswith("http") and not title:
                if "61792899-94d5-4012-b52f-b23a692f9fe2" in url:
                    title = "Film-Tipps(2)"
                elif "5403e51d-e682-495f-9f3f-de3cfb4503a9" in url:
                    title = "Dokumentationen(2)"
                elif "65f7bb52-cb22-44c2-85a2-940557d25670" in url:
                    title = "Gameshows(2)"
                else:
                    title = ".."
            duration = js.get("duration", "")
            if str(duration).isdigit():
                duration = str(timedelta(seconds=int(duration // 1000)))
            img = js.get("imageUrl") + "/scale/width/320" if js.get("imageUrl") else ""
            desc = format_datetime(js)
            desc += "\n" + js.get("lead", "") if desc else js.get("lead", "")
            desc += "\n" + js.get("description", "") if desc else js.get("description", "")
            if not url.startswith("http"):
                continue
            if "video" in url or "audio" in url:
                liste.append(("PLAY", ensure_str(title), ensure_str(url), ensure_str(desc), ensure_str(img), duration))
            else:
                liste.append(("NEXT", ensure_str(title), ensure_str(url), ensure_str(desc), ensure_str(img), duration))
        if data.get("next"):
            liste.append(("NEXT", "NextPage", data.get("next"), "", "%s/img/nextpage.png" % PLUGINPATH, ""))
        if liste:
            self["movielist"].setList(liste)
            self["movielist"].setIndex(int(index))
            self.infos()

    def ffmpegsetup(self, answer):
        if answer:
            self.session.open(Console, cmdlist=["opkg update && opkg install ffmpeg"])

    def Download(self):
        if not path.exists("/usr/bin/ffmpeg"):
            self.session.openWithCallback(self.ffmpegsetup, MessageBox, "Zum Download benötigen Sie ffmpeg installieren?")
            return
        if self.DL_File:
            self.session.openWithCallback(self.DL_Stop, MessageBox, "möchten Sie den Download abbrechen?", default=True, type=MessageBox.TYPE_YESNO)
            return

        url = self["movielist"].getCurrent()[2]
        data = ensure_str(geturl(url))
        if not data:
            return
        if "drmList" in data or "don't have permission" in data:
            self.session.open(MessageBox, "Download nicht möglich DRM Geschützt", MessageBox.TYPE_INFO)
            return
        liste = []
        if data:
            data = json.loads(ensure_str(data))
            if len(data.get("chapterList", "")) == 1:
                data = data.get("chapterList")[0]
                for data in data.get("resourceList", {}):
                    if data.get("url"):
                        url = data.get("url")
                        if url.split("?")[0] in str(liste):
                            continue
                        if "master.m3u8" in url:
                            url = url.split("?")[0]
                            if ".m3u8" in str(liste):
                                continue
                            html2 = ensure_str(geturl(url))
                            m3u = re.compile(r"#EXT-X-STREAM.*?RESOLUTION=(\d+x+\d+).*?\n(.*?)\n", re.DOTALL).findall(html2)
                            for q, link in m3u:
                                liste.append(("HLS | %s" % q, url.split("master")[0] + link.strip()))
                            if ".m3u8" in str(liste):
                                continue
                        elif ".mp4" in url:
                            liste.append(("MP4 | %s" % data.get("quality", ""), url))
                        elif ".mp3" in url:
                            liste.append(("MP3", url))
                        else:
                            pass
            liste = sortList(liste)
            if len(liste) > 1:
                self.session.openWithCallback(self.DL_Start, ChoiceBox, title="Download starten?", list=liste)
            elif liste:
                self.DL_Start(liste[0])

    def DL_Stop(self, answer):
        if answer:
            self.console.sendCtrlC()
            if path.exists(self.DL_File):
                unlink(self.DL_File)
            self.DL_File = None
            self.totalDuration = 0
            self["progress"].hide()

    def DL_Start(self, answer):
        if answer:
            url = answer[1].replace("&webvttbaseurl=subtitles.eai-general.aws.srf.ch", "")
            filename = "".join(i for i in ensure_str(self["movielist"].getCurrent()[1]) if i not in r'\/":*?<>|')
            self.DL_File = str(config.plugins.SRF.savetopath.value) + "/" + str(filename) + ".mp4"
            if path.exists(self.DL_File):
                n = self.DL_File
                root, ext = path.splitext(self.DL_File)
                i = 0
                while path.exists(n):
                    i += 1
                    n = "%s_(%i)%s" % (root, i, ext)
                self.DL_File = n
            if ".m3u8" in url or ".mp4" in url or ".mp3" in url:
                self.console = eConsoleAppContainer()
                self.console.dataAvail.append(self.avail)
                self.console.appClosed.append(self.finished)
                cmd = 'ffmpeg -y -i %s -headers "User-Agent: %s" -acodec copy -vcodec copy "%s"' % (url, UA, self.DL_File)
                self.console.execute(cmd)
                self["progress"].show()
                self["progress"].setValue(0)
                self["DownloadLabel"].setText("")
                self["DownloadLabel"].show()
            else:
                self.session.open(MessageBox, "Das Herunterladen der Datei wird nicht unterstützt.", MessageBox.TYPE_INFO)
                self.DL_File = None

    def avail(self, txt):
        try:
            if txt:
                txt = ensure_str(txt)
                if "Duration" in txt:
                    duration = txt.split("Duration: ")[1].split(",")[0].split(":")
                    if len(duration) == 3 and duration[0] and duration[1] and duration[2]:
                        self.totalDuration = float(duration[0]) * 3600 + float(duration[1]) * 60 + float(duration[2])
                    else:
                        self.totalDuration = 7200.00
                if "time=" in txt and self.totalDuration > 0:
                    duration = txt.split("time=")[1].split(" ")[0].split(":")
                    if len(duration) == 3 and duration[0].isdigit() and duration[1].isdigit():
                        duration = float(duration[0]) * 3600 + float(duration[1]) * 60 + float(duration[2])
                        if duration and self.totalDuration:
                            progress = (duration / self.totalDuration) * 100
                            self["progress"].setValue(int(progress))
                            self["DownloadLabel"].setText(str(round(progress, 2)) + " %")
        except (KeyError, ValueError, IndexError):
            pass

    def finished(self, string):
        if self.DL_File:
            if string == 0:
                self.session.open(MessageBox, "Download erfolgreich", MessageBox.TYPE_INFO)
            else:
                self.session.open(MessageBox, "Download error", MessageBox.TYPE_INFO)
            self.console.sendCtrlC()
        self["progress"].hide()
        self["DownloadLabel"].hide()

    def Play(self):
        url = self["movielist"].getCurrent()[2]
        data = ensure_str(geturl(url))
        if not data:
            return
        if "drmList" in data or "don't have permission" in data:
            self.session.open(MessageBox, "DRM Geschützt kann nicht abgespielt werden", MessageBox.TYPE_INFO)
            return
        liste = []
        if data:
            data = json.loads(ensure_str(data))
            if len(data.get("chapterList", "")) == 1:
                data = data.get("chapterList")[0]
                for data in data.get("resourceList", {}):
                    if data.get("url"):
                        url = data.get("url")
                        if url.split("?")[0] in str(liste):
                            continue
                        if "master.m3u8" in url:
                            url = url.split("?")[0]
                            if ".m3u8" in str(liste):
                                continue
                            html2 = ensure_str(geturl(url))
                            m3u = re.compile(r"#EXT-X-STREAM.*?RESOLUTION=(\d+x+\d+).*?\n(.*?)\n", re.DOTALL).findall(html2)
                            for q, link in m3u:
                                liste.append(("HLS | %s" % (q), url.split("master")[0] + link.strip()))
                            if ".m3u8" in str(liste):
                                continue
                        elif ".mp4" in url:
                            liste.append(("MP4 | %s" % data.get("quality", ""), url))
                        elif ".mp3" in url:
                            liste.append(("MP3", url))
            liste = sortList(liste)
            if config.plugins.SRF.AUTOPLAY.value and liste:
                self.Player(liste[0])
            elif len(liste) > 1:
                self.session.openWithCallback(self.Player, ChoiceBox, title="Wiedergabe starten?", list=liste)
            elif liste:
                self.Player(liste[0])

    def Player(self, url):
        url = url and url[1]
        if url:
            sref = eServiceReference(4097, 0, ensure_str(url))
            sref.setName(self["movielist"].getCurrent()[1])
            self.session.open(MoviePlayer2, sref)

    def up(self):
        if self["movielist"]:
            self["movielist"].up()
            self.infos()

    def down(self):
        if self["movielist"]:
            self["movielist"].down()
            self.infos()

    def left(self):
        if self["movielist"]:
            self["movielist"].pageUp()
            self.infos()

    def right(self):
        if self["movielist"]:
            self["movielist"].pageDown()
            self.infos()

    def p_up(self):
        self["handlung"].pageUp()

    def p_down(self):
        self["handlung"].pageDown()

    def infos(self):
        handlung = self["movielist"].getCurrent()[3]
        self["handlung"].setText(handlung)
        self.show_cover()

    def show_cover(self):
        if self["movielist"].getCurrent() is not None:
            url = self["movielist"].getCurrent()[4]
            if url.startswith("http"):
                callInThread(self.getimage, url, self["movielist"].getIndex())
            elif url.startswith("/usr/"):
                self.get_cover(url)
            else:
                img = "%s/img/nocover.png" % PLUGINPATH
                self.get_cover(img)

    def getimage(self, url, index=0):
        try:
            data = geturl(url, verify=False)
            with open(TMPIC, "wb") as f:
                f.write(data)
            if index == int(self["movielist"].getIndex()):
                self.get_cover(TMPIC)
        except OSError:
            pass

    def get_cover(self, img):
        picload = ePicLoad()
        self["cover"].instance.setPixmap(gPixmapPtr())
        size = self["cover"].instance.size()
        picload.setPara((size.width(), size.height(), 1, 1, False, 1, "#FF000000"))
        if picload.startDecode(img, 0, 0, False) == 0:
            ptr = picload.getData()
            if ptr is not None:
                self["cover"].instance.setPixmap(ptr)
                self["cover"].show()


class MoviePlayer2(MoviePlayer):
    ENABLE_RESUME_SUPPORT = True

    def __init__(self, session, service):
        MoviePlayer.__init__(self, session, service)
        self.skinName = "MoviePlayer"

    def up(self):
        pass

    def down(self):
        pass

    def leavePlayer(self):
        if config.plugins.SRF.SaveResumePoint.value and hasattr(InfoBarGenerics, "setResumePoint"):
            InfoBarGenerics.setResumePoint(self.session)
        self.close()

    def leavePlayerOnExit(self):
        self.leavePlayer()

    def doEofInternal(self, playing):
        if not playing or not self.execing:
            return
        self.close()


class SRFConfigScreen(ConfigListScreen, Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.title = "Einstellungen"
        self.session = session
        self.skinName = ["Setup"]
        self["key_red"] = StaticText("Abbrechen")
        self["key_green"] = StaticText("Speichern")
        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"], {"cancel": self.cancel, "red": self.cancel, "ok": self.ok, "green": self.save}, -2)
        ConfigListScreen.__init__(self, [], session=session)
        self.ConfigList()

    def ConfigList(self):
        self.list = [getConfigListEntry("Skin (Neustart des Plugins erforderlich)", config.plugins.SRF.SkinColor), getConfigListEntry("Download-Verzeichnis:", config.plugins.SRF.savetopath)]
        if hasattr(InfoBarGenerics, "setResumePoint"):
            self.list.append(getConfigListEntry("Letzte Abspielposition speichern", config.plugins.SRF.SaveResumePoint))
        self.list.append(getConfigListEntry("AutoPlay Beste Qualität", config.plugins.SRF.AUTOPLAY))
        self["config"].list = self.list

    def save(self):
        self.keySave()
        configfile.save()
        self.close()

    def cancel(self):
        self.close()

    def ok(self):
        if self["config"].getCurrent()[1] == config.plugins.SRF.savetopath:
            dldir = config.plugins.SRF.savetopath.value
            self.session.openWithCallback(self.DL_Path, DirBrowser, dldir)

    def DL_Path(self, res):
        self["config"].setCurrentIndex(0)
        if res:
            config.plugins.SRF.savetopath.value = res


class DirBrowser(Screen):
    def __init__(self, session, dldir):
        Screen.__init__(self, session)
        self.skinName = ["FileBrowser"]
        self["key_red"] = StaticText("Abbrechen")
        self["key_green"] = StaticText("Speichern")
        if not path.exists(dldir):
            dldir = "/"
        self.filelist = FileList(dldir, showFiles=False)
        self["filelist"] = self.filelist
        self["FilelistActions"] = ActionMap(["SetupActions", "ColorActions"], {"cancel": self.cancel, "red": self.cancel, "ok": self.ok, "green": self.save}, -2)

    def ok(self):
        if self.filelist.canDescent():
            self.filelist.descent()

    def save(self):
        fullpath = self["filelist"].getSelection()[0]
        if fullpath is not None and fullpath.endswith("/"):
            self.close(fullpath)

    def cancel(self):
        self.close(False)
