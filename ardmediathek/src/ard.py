# -*- coding: UTF-8 -*-
from os import mkdir, unlink, path
from datetime import datetime, timedelta
from json import loads
import xml.etree.ElementTree as Et
import time
import re
import requests
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigDirectory, ConfigSelection, ConfigYesNo
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
from six.moves.urllib.parse import quote_plus
from twisted.internet.reactor import callInThread
from Tools.Downloader import downloadWithProgress
config.plugins.ARD = ConfigSubsection()
config.plugins.ARD.savetopath = ConfigDirectory(default="/media/hdd/movie/")
config.plugins.ARD.SaveResumePoint = ConfigYesNo(default=False)
config.plugins.ARD.UT_DL = ConfigYesNo(default=False)
config.plugins.ARD.COVER_DL = ConfigYesNo(default=False)
config.plugins.ARD.DESC = ConfigYesNo(default=False)
config.plugins.ARD.AUTOPLAY = ConfigYesNo(default=False)
PLUGINPATH = "/usr/lib/enigma2/python/Plugins/Extensions/ArdMediathek/"
RegionList = [("bw", ("Baden-Württemberg (SWR)")), ("by", ("Bayern (BR)")), ("be", ("Berlin (rbb)")), ("bb", ("Brandenburg (rbb)")), ("hb", ("Bremen (radiobremen)")), ("hh", ("Hamburg (NDR)")), ("he", ("Hessen (hr)")), ("mv", ("Mecklenburg-Vorpommern (NDR)")), ("ni", ("Niedersachsen (NDR)")), ("nw", ("Nordrhein-Westfalen (WDR)")), ("rp", ("Rheinland-Pfalz (SWR)")), ("sl", ("Saarland (SR)")), ("sn", ("Sachsen (mdr)")), ("st", ("Sachsen-Anhalt (mdr)")), ("sh", ("Schleswig-Holstein (NDR)")), ("th", ("Thüringen (mdr)"))]
config.plugins.ARD.Region = ConfigSelection(default="nw", choices=RegionList)
FHD = getDesktop(0).size().height() > 720
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0"
TMPIC = "/tmp/cover/bild.jpg"
SKINFILE = PLUGINPATH + "skin_FHD.xml" if FHD else PLUGINPATH + "skin_HD.xml"
FONT = "/usr/share/fonts/LiberationSans-Regular.ttf"
if not path.exists(FONT):
    FONT = "/usr/share/fonts/nmsbd.ttf"
addFont(FONT, "SRegular", 100, False)
API_URL = "https://api.ardmediathek.de/page-gateway/"
URL_HOME = API_URL + "pages/%s/home?embedded=true"
URL_AZ = API_URL + "pages/%s/editorial/experiment-a-z?embedded=true"
ColorList = [("default,#1a104485,#3D104485,#1aC0C0C0", "Trans-BrightBlue"), ("default,#050a1232,#1502050e,#05192d7c", "Trans-DarkBlue"), ("default,#05000000,#15000000,#606060", "Trans-BlackGray"), ("default,#05000000,#15000000,#ffff00", "Trans-BlackYellow"), ("default,#1a746962,#1502050e,#1a746962", "Trans-BrownBlue"), ("MiniTV,#104485,#0c366a,#C0C0C0", "BrightBlue MiniTV"), ("MiniTV,#0a1232,#02050e,#192d7c", "DarkBlue MiniTV"), ("MiniTV,#000000,#080808,#606060", "BlackGray MiniTV"), ("MiniTV,#000000,#080808,#ffff00", "BlackYellow MiniTV"), ("MiniTV,#746962,#02050e,#746962", "BrownBlue MiniTV")]
config.plugins.ARD.SkinColor = ConfigSelection(default="default,#050a1232,#1502050e,#05192d7c", choices=ColorList)


def readskin():
    cf = config.plugins.ARD.SkinColor.value.split(",")
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


def geturl(url):
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8", "Accept-Language": "de,en-US;q=0.7,en;q=0.3", "Accept-Encoding": "gzip, deflate"})
        r.raise_for_status()
        return r.content
    except requests.RequestException:
        return ""


def dateTime2(dt):
    try:
        s = ""
        delta = time.localtime().tm_isdst
        if dt.get("broadcastedOn"):
            b = time.mktime(time.strptime(dt.get("broadcastedOn"), "%Y-%m-%dT%H:%M:%SZ"))
            b = b + (delta + 1) * 3600
            b = time.localtime(b)
            s += "\nGesendet am %s " % "{0:02d}.{1:02d}.{2:04d} {3:02d}:{4:02d}".format(b.tm_mday, b.tm_mon, b.tm_year, b.tm_hour, b.tm_min)
        if dt.get("availableTo"):
            a = time.mktime(time.strptime(dt.get("availableTo"), "%Y-%m-%dT%H:%M:%SZ"))
            a = a + (delta + 1) * 3600
            a = time.localtime(a)
            s += "\nVerfügbar bis %s" % "{0:02d}.{1:02d}.{2:04d} {3:02d}:{4:02d}".format(a.tm_mday, a.tm_mon, a.tm_year, a.tm_hour, a.tm_min)
        return ensure_str(s)
    except (TypeError, ValueError, AttributeError):
        return ""


def sortList(txt):
    return sorted(txt, key=lambda text: int(re.compile(r"(\d+)x", re.DOTALL).findall(text[0])[0]) if re.compile(r"(\d+)x", re.DOTALL).findall(str(text[0])) else 0, reverse=True)


class ArdMediathek(Screen):
    def __init__(self, session):
        skin = readskin()
        self.skin = skin
        Screen.__init__(self, session)
        self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "ChannelSelectBaseActions", "MovieSelectionActions"], {"contextMenu": self.ARDSetup, "green": self.Download, "red": self.close, "blue": self.Home, "up": self.up, "down": self.down, "left": self.left, "right": self.right, "nextBouquet": self.p_up, "prevBouquet": self.p_down, "ok": self.ok, "cancel": self.exit}, -1)
        self["movielist"] = List()
        self["cover"] = Pixmap()
        self["handlung"] = ScrollLabel()
        self.HISTORY = [("MENU", "")]
        self["DownloadLabel"] = ScrollLabel()
        self["PluginName"] = ScrollLabel("ARD Mediathek v1.5")
        self["progress"] = ProgressBar()
        self["progress"].hide()
        self.PROGRAMM = "ard"
        self.DL_File = None
        if not path.exists("/tmp/cover/"):
            mkdir("/tmp/cover/")
        self.onLayoutFinish.append(self.HauptMenu)

    def ARDSetup(self):
        self.session.open(ARDConfigScreen)

    def HauptMenu(self, index="0"):
        self.searchtxt = ""
        self.PROGRAMM = "ard"
        menu = [("MENU", "ARD Mediathek - Start", URL_HOME % self.PROGRAMM, "", PLUGINPATH + "/img/" + "home.png", ""), ("MENU", "Entdecken", API_URL + "pages/ard/editorial/entdecken?embedded=true", "", PLUGINPATH + "/img/" + "endecken.png", ""), ("SenderMenu", "Sender", "SenderMenu", "", PLUGINPATH + "/img/" + "sender.png", ""), ("ProgrammMenu", "Sendung verpasst", "ProgrammMenu", "", PLUGINPATH + "/img/" + "programm.png", ""), ("MENU", "Sendungen A-Z", URL_AZ % "ard", "", PLUGINPATH + "/img/" + "az.png", ""), ("MENU", "LIVE", API_URL + "widgets/ard/editorials/4hEeBDgtx6kWs6W6sa44yY?pageNumber=0&pageSize=24&embedded=true", "", PLUGINPATH + "/img/" + "live.png", ""), ("Suche", "Suche", "", "", PLUGINPATH + "/img/" + "suche.png", "")]
        self["movielist"].setList(menu)
        self["movielist"].setIndex(int(index))
        self.infos()

    def ok(self):
        if self["movielist"].getCurrent()[0] == "Suche":
            self.session.openWithCallback(self.search, VirtualKeyBoard, title="ARD Mediathek Suche")
        elif self["movielist"].getCurrent()[0] == "PLAY":
            self.Play()
        else:
            Index = self["movielist"].getIndex()
            url = self["movielist"].getCurrent()[2]
            if self["movielist"].getCurrent()[0] == "MENU":
                self.Widgets(url)
            elif self["movielist"].getCurrent()[0] == "WEITER":
                self.Widgets(url)
            elif self["movielist"].getCurrent()[0] == "Sender2Menu":
                self.PROGRAMM = self["movielist"].getCurrent()[2]
                self.Menu2Sender()
                url = "Sender2Menu"
            elif self["movielist"].getCurrent()[0] == "Programm3":
                self.PROGRAMM = self["movielist"].getCurrent()[2]
                url = "Programm3"
                self.Programm3()
            elif self["movielist"].getCurrent()[0] == "SenderMenu":
                self.SenderMenu("0", "Sender2Menu")

            elif self["movielist"].getCurrent()[0] == "ProgrammMenu":
                self.SenderMenu("0", "Programm3")
            else:
                return
            self.HISTORY.append((url, Index))

    def Home(self):
        self.HISTORY = [("MENU", "")]
        self.HauptMenu()

    def exit(self):
        if len(self.HISTORY) > 1:
            Index = self.HISTORY[-1][1]
            self.HISTORY.pop()
            url = self.HISTORY[-1][0]
            if url.startswith("http"):
                self.Widgets(url, Index)
            elif url == "MENU":
                self.HauptMenu(Index)
            elif url == "SenderMenu":
                self.SenderMenu(Index, "Sender2Menu")
            elif url == "Sender2Menu":
                self.Menu2Sender(Index)
            elif url == "ProgrammMenu":
                self.SenderMenu(Index, "ProgrammMenu")
            elif url == "Programm3":
                self.Programm3(Index)
        else:
            if path.exists(TMPIC):
                unlink(TMPIC)
            self.close()

    def SenderMenu(self, index="0", mt=""):
        URL = "https://images.ardmediathek.de/vrwifdtrtsys/"
        menu = [(mt, "Alpha", "alpha", "", URL + "4hn8C8lrTimEuYSiee6Y0/ca7f2eaf0f75c01412a54ad002b62d05/livestream_ard-alpha.jpg?w=360", ""), (mt, "Arte", "arte", "", URL + "6tne4hKLnD9RGHNDolSKu4/c3ca716c02da066a135777b7f5ef5a33/arte_livestream_bild.png?w=360", ""), (mt, "BR", "br", "", URL + "6G1LV7aj5okmlUx0PoJ3g4/bc05260c402272eb4458f141c43f51f9/BR_Fernsehen.jpg?w=360", ""), (mt, "Das Erste", "daserste", "", URL + "43ntcnDlAiL2fbBuR4AXlq/51487971e825f5b9968cf3f9c2c81ec5/8.jpg?w=360", ""), (mt, "HR", "hr", "", URL + "xMGOYhXKGnS4ZujacpB3n/7f67e1d482aa9c80f56db652369532a6/hr-Logo-Livestream-16-9.jpg?w=360", ""), (mt, "KIKA", "kika", "", "https://api.ardmediathek.de/image-service/images/urn:ard:image:34a231a870f22c6d?w=360&ch=865612894cbd4d56", ""), (mt, "MDR", "mdr", "", URL + "70UZvshUMZ3esCGEMGVgVJ/0bc665b6b1a4874f0d767e8931a65ac8/livestream.jpg?w=360", ""), (mt, "NDR", "ndr", "", "https://api.ardmediathek.de/image-service/images/urn:ard:image:8d587d540cd01169?w=360", ""), (mt, "One", "one", "", URL + "1N26MHa704lWZqiIPMR4nn/65260642a6afef4152b10cb2a37b1f34/ONE_Livestream.jpg?w=360", ""), (mt, "Phoenix", "phoenix", "", URL + "5cTm9Nwre7F41oMKBdbs9h/1bf04723d680dbf9a4e8e9fb5afc4da9/phoenixlogo_169.jpg?w=360", ""), (mt, "Radio Bremen", "radiobremen", "", URL + "4RpI2I7QHu2M2OysQwaC8K/d1318b6f73be6bb1303f622e174f7940/radiobremen.jpg?w=360", ""), (mt, "RBB", "rbb", "", URL + "ca3lrftfNOollG4Ts3bIF/187d062535a5263e0f4087e5b472f3fd/rbb_Logo_roter_Hintergrund_wei_es_Logo_1920.jpg?w=360", ""), (mt, "SR", "sr", "", URL + "5JuVdzmKl2u6WQIW8qeGKa/6fe4ba39ffa9a94c475b11f4e8733e74/livestream_sr.png?w=360", ""), (mt, "SWR", "swr", "", URL + "4apl4dmokQmuWOEltdMXoZ/a36e2c6a58884f5c0488b34b3b180a2d/SWR_Logo_fuer_Livestream_Mediathek.jpg?w=360", ""), (mt, "Tagesschau24", "tagesschau24", "", URL + "7tfD9nWFpPlGzvyuDGIb7v/e763406fd70a8302ea6b920c719291f4/welt_ts24.jpg?w=360", ""), (mt, "WDR", "wdr", "", URL + "5r6IfjTgc4h3JrYZkSdbyY/0e11ab1a8bbc67d2d4e91844306532c1/wdr-logo-128_gross.jpg?w=360", "")]
        self["movielist"].setList(menu)
        self["movielist"].setIndex(int(index))
        self.infos()

    def Menu2Sender(self, index="0"):
        menu = [("WEITER", "%s  Start" % self.PROGRAMM.upper(), URL_HOME % self.PROGRAMM, "", PLUGINPATH + "/img/" + "home.png", ""), ("WEITER", "Sendungen A-Z", URL_AZ % self.PROGRAMM, "", PLUGINPATH + "/img/" + "az.png", ""), ("Suche", "Suche", "", "", PLUGINPATH + "/img/" + "suche.png", "")]
        self["movielist"].setList(menu)
        self["movielist"].setIndex(int(index))
        self.infos()

    def Programm3(self, index="0"):
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
            start = start.strftime("%Y-%m-%dT03:30:00.000Z")
            end = (now + timedelta(1 - i)).strftime("%Y-%m-%dT03:29:59.000Z")
            url = API_URL + "compilations/%s/pastbroadcasts?startDateTime=%s&endDateTime=%s&pageSize=200" % (self.PROGRAMM, start, end)
            liste.append(("WEITER", title, ensure_str(url), "", "", ""))
        self["movielist"].setList(liste)
        self["movielist"].setIndex(int(index))
        self.infos()

    def search(self, search):
        if search:
            self.searchtxt = search
            url = API_URL + "widgets/%s/search/grouping?searchString=%s&pageSize=200" % (self.PROGRAMM, quote_plus(self.searchtxt))
            Index = self["movielist"].getIndex()
            self.HISTORY.append((url, Index))
            self.Widgets(url, index="0")

    def Widgets(self, url, index="0"):
        liste = []
        data = geturl(url)
        if data:
            data = loads(ensure_str(data))
        else:
            self.HISTORY.pop()
            return
        if len(data) == 1:
            data = data[0]
        if data.get("widgets", ""):
            data2 = data.get("widgets")
            if "grouping" in url and data2[0].get("teasers"):
                data2 = data2[0].get("teasers")
        elif data.get("teasers"):
            data2 = data.get("teasers")
        else:
            if self.searchtxt and "grouping?searchString" in url:
                url = API_URL + "widgets/%s/search/vod?searchString=%s&pageNumber=0&pageSize=200" % (self.PROGRAMM, quote_plus(self.searchtxt))
                self.HISTORY.append((url, index))
                self.Widgets(url, index="0")
            elif self.searchtxt:
                self.session.open(MessageBox, "Kein Suchergebnis", MessageBox.TYPE_INFO, 5)
            else:
                self.session.open(MessageBox, "Kein Eintrag vorhanden", MessageBox.TYPE_INFO)
            self.HISTORY.pop()
            return
        if self.searchtxt and "grouping?searchString" in url:
            liste.append(("WEITER", "Videos", API_URL + "widgets/%s/search/vod?searchString=%s&pageNumber=0&pageSize=200" % (self.PROGRAMM, quote_plus(self.searchtxt)), "", "", ""))

        for js in data2:
            if js.get("type") in ("external"):
                continue
            plot = ""
            if js.get("title"):
                title = js.get("title")
            else:
                title = js.get("longTitle", "")
            if " | " in title:
                plot += title.split(" | ")[1] + "\n"
                title = title.split(" | ")[0]
            plot += js.get("publicationService").get("name") + " " if js.get("publicationService", {}).get("name") else ""
            if js.get("show"):
                s = js.get("show")
                for bf in s.get("binaryFeatures", {}):
                    plot += bf + " "
            plot += js.get("maturityContentRating") if "FSK" in js.get("maturityContentRating", "") else ""
            plot += dateTime2(js)
            plot += js.get("description", "")
            if js.get("show"):
                s = js.get("show")
                if s.get("longSynopsis"):
                    plot += "\n\n" + s.get("longSynopsis") + "\n"
            if plot == "":
                plot += data.get("title", "")
            duration = js.get("duration", "")
            if str(duration).isdigit():
                duration = str(timedelta(seconds=int(duration)))
            if js.get("images"):
                im = js.get("images")
            elif js.get("teasers"):
                im = js.get("teasers")[0]
                if im.get("images"):
                    im = im.get("images")
            else:
                im = {}
            if im.get("aspect16x9"):
                im = im.get("aspect16x9")
            img = im.get("src", "").replace("{width}", "360")
            if js.get("links"):
                li = js.get("links")
                if li.get("target"):
                    li = li.get("target")
                elif li.get("self"):
                    li = li.get("self")
                if li.get("href"):
                    url2 = li.get("href")
            if js.get("duration") or js.get("type") in ("live", "event", "broadcastMainClip"):
                liste.append(("PLAY", ensure_str(title), ensure_str(url2), ensure_str(plot), ensure_str(img), duration))
            elif js.get("type") == "region_gridlist":
                liste.append(("WEITER", ensure_str(title) + " " + config.plugins.ARD.Region.value, ensure_str(API_URL + "widgets/ard/region/6YgzSO0C7huVaGgzM5mq19/%s?pageNumber=0&pageSize=100&embedded=true") % config.plugins.ARD.Region.value, ensure_str(plot), img, duration))
            else:
                liste.append(("WEITER", ensure_str(title), ensure_str(url2), ensure_str(plot), ensure_str(img), duration))
        if "grouping" in url and data.get("widgets"):
            data = data.get("widgets")[0]
        if data.get("pagination"):
            page = data.get("pagination")
            pageNumber = page.get("pageNumber")
            pageSize = page.get("pageSize")
            total = page.get("totalElements")
            if (int(pageNumber) + 1) * int(pageSize) < int(total):
                if "/search/vod" in url:
                    url = API_URL + "widgets/%s/search/vod?searchString=%s&pageNumber=%s&pageSize=%d" % (self.PROGRAMM, self.searchtxt, pageNumber + 1, pageSize)
                elif "grouping" in url or "asset" in url:
                    url = API_URL + "widgets/%s/asset/%s?pageNumber=%s&pageSize=%s" % (self.PROGRAMM, data.get("id", ""), pageNumber + 1, pageSize)
                else:
                    url = API_URL + "widgets/%s/editorials/%s?pageNumber=%s&pageSize=%s&embedded=true" % (self.PROGRAMM, data.get("id", ""), pageNumber + 1, pageSize)
                maxpage = total // pageSize + (1 if total - pageSize * (total // pageSize) > 0 else 0)
                liste.append(("WEITER", "NextPage (" + str((int(pageNumber) + 2)) + " / " + str(maxpage) + ")", ensure_str(url), "", PLUGINPATH + "/img/" + "nextpage.png", ""))
        if liste:
            self["movielist"].setList(liste)
            self["movielist"].setIndex(int(index))
            self.infos()

    def Download(self):
        if self.DL_File:
            self.session.openWithCallback(self.DL_Stop, MessageBox, "möchten Sie den Download abbrechen?", default=True, type=MessageBox.TYPE_YESNO)
        else:
            url = self["movielist"].getCurrent()[2]
            html = ensure_str(geturl(url))
            if 'blockedByFsk":true' in html:
                self.session.open(MessageBox, "Das Video ist nicht für Kinder und Jugendliche geeignet und kann erst nach 22 Uhr Download werden.", MessageBox.TYPE_INFO)
                return
            if html and "widgets" in html:
                js = loads(html)
                js = js.get("widgets")[0] if js.get("widgets") else {}
                coreAssetType = js.get("show").get("coreAssetType", "") == "SEASON_SERIES" if js.get("show") else False
                title = ("%s - %s") % (js.get("show", {}).get("title", ""), js.get("title", "")) if coreAssetType else js.get("title", "")
                if "agesschau" in title and js.get("broadcastedOn"):
                    title = "%s(%s)" % (title, js.get("broadcastedOn")[:10])
                filename = "".join(i for i in ensure_str(title) if i not in r'\/":*?<>|')
            UT = re.compile(r'(http[^"]+.vtt)', re.DOTALL).findall(html)
            UT = UT[0] if UT else ""
            liste = []
            mp4 = re.compile(r'_height":(\d+).*?_stream":"([^"]+).*?width":(\d+)', re.DOTALL).findall(html)
            if mp4:
                for h, url, w in mp4:
                    url = "https:" + url if url.startswith("//") else url
                    liste.append(("%s (%sx%s).mp4" % (filename, w, h), url + "##" + UT))
            liste = sortList(liste)
            if len(liste) > 1:
                self.session.openWithCallback(self.DL_Start, ChoiceBox, title="Download starten?", list=liste)

    def DL_Start(self, answer):
        if answer:
            url = answer[1].split("##")
            self.DL_File = str(config.plugins.ARD.savetopath.value) + str(answer[0])
            if path.exists(self.DL_File):
                n = self.DL_File
                root, ext = path.splitext(self.DL_File)
                i = 0
                while path.exists(n):
                    i += 1
                    n = "%s_(%i)%s" % (root, i, ext)
                self.DL_File = n
            if config.plugins.ARD.COVER_DL.value:
                downloader = downloadWithProgress(str(self["movielist"].getCurrent()[4].replace("w=360", "w=1080")), self.DL_File[:-3] + "jpg")
                if hasattr(downloadWithProgress, "setAgent"):
                    downloader.setAgent(UA)
                downloader.start()
            if config.plugins.ARD.UT_DL.value and url[1]:
                txt = ensure_str(geturl(url[1]))
                if txt:
                    cleantext = re.sub(re.compile("<.*?>| align:middle"), "", txt)
                    with open(self.DL_File[:-3] + "srt", "w") as f:
                        f.write(cleantext)
            if config.plugins.ARD.DESC.value:
                data = ensure_str(geturl(self["movielist"].getCurrent()[2]))
                if data and "widgets" in data:
                    js = loads(data)
                    js = js.get("widgets")[0] if js.get("widgets") else {}
                    desc = js.get("synopsis", "")
                    if desc:
                        with open(self.DL_File[:-3] + "txt", "w") as f:
                            f.write(desc)
            self["progress"].show()
            self["DownloadLabel"].show()
            self.downloader = downloadWithProgress(str(url[0]), self.DL_File)
            if hasattr(downloadWithProgress, "setAgent"):
                self.downloader.setAgent(UA)
            self.downloader.addProgress(self.DL_progress)
            self.downloader.addEnd(self.DL_finished)
            self.downloader.addError(self.DL_failed)
            self.downloader.start()

    def fileClean(self):
        if path.exists(self.DL_File):
            unlink(self.DL_File)
        if path.exists(self.DL_File[:-3] + "srt"):
            unlink(self.DL_File[:-3] + "srt")
        if path.exists(self.DL_File[:-3] + "jpg"):
            unlink(self.DL_File[:-3] + "jpg")
        if path.exists(self.DL_File[:-3] + "txt"):
            unlink(self.DL_File[:-3] + "txt")

    def DL_Stop(self, answer):
        if answer:
            self.downloader.stop()
            self.fileClean()
            self.DL_File = None
            self["progress"].hide()
            self["DownloadLabel"].hide()

    def DL_finished(self, s=""):
        self["progress"].hide()
        self["DownloadLabel"].hide()
        self.DL_File = None
        self.session.open(MessageBox, "Download erfolgreich %s" % s, MessageBox.TYPE_INFO, timeout=5)

    def DL_failed(self, error):
        self["progress"].hide()
        self["DownloadLabel"].hide()
        self.downloader.stop()
        self.fileClean()
        self.DL_File = None
        self.session.open(MessageBox, "Download-Fehler %s" % error, MessageBox.TYPE_INFO)

    def DL_progress(self, recvbytes, totalbytes):
        if recvbytes and totalbytes:
            self["DownloadLabel"].setText(str(recvbytes // 1024 // 1024) + "MB/" + str(totalbytes // 1024 // 1024) + "MB")
            self["progress"].setValue(int(100 * recvbytes // totalbytes))

    def Play(self):
        url = self["movielist"].getCurrent()[2]
        html = ensure_str(geturl(url))
        if 'blockedByFsk":true' in html:
            self.session.open(MessageBox, "Das Video ist nicht für Kinder und Jugendliche geeignet und kann erst nach 22 Uhr abgespielt werden.", MessageBox.TYPE_INFO)
            return
        liste = []
        mp4 = re.compile(r'_height":(\d+).*?_stream":"([^"]+).*?width":(\d+)', re.DOTALL).findall(html)
        m3u8 = re.compile('_quality":"([^"]+)","_stream":"([http|//][^"]+m3u8)', re.DOTALL).findall(html)
        if mp4:
            for h, url, w in mp4:
                url = "https:" + url if url.startswith("//") else url
                bit = " | %s" % re.compile(r"(\d+kbit)", re.DOTALL).findall(url)[0] if re.compile(r"(\d+kbit)", re.DOTALL).findall(url) and "m3u8" not in url else ""
                liste.append(("MP4 | %sx%s%s" % (w, h, bit), url))
        if m3u8:
            for res, url in m3u8:
                url = "https:" + url if url.startswith("//") else url
                liste.append(("m3u8 | %s" % res, url))
        liste = sortList(liste)
        if config.plugins.ARD.AUTOPLAY.value and liste:
            self.Play2(liste[0])
        elif len(liste) > 1:
            self.session.openWithCallback(self.Play2, ChoiceBox, title="Wiedergabe starten?", list=liste)
        elif liste:
            self.Play2(liste[0])
        else:
            self.session.open(MessageBox, "Kein Eintrag vorhanden", MessageBox.TYPE_INFO)

    def Play2(self, url):
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
                callInThread(self.getimage, url)
            elif url.startswith("/usr/"):
                self.get_cover(url)
            else:
                img = PLUGINPATH + "/img/nocover.png"
                self.get_cover(img)

    def getimage(self, url):
        try:
            data = geturl(url)
            with open(TMPIC, "wb") as f:
                f.write(data)
            self.get_cover(TMPIC)
        except OSError:
            pass

    def get_cover(self, img):
        picload = ePicLoad()
        self["cover"].instance.setPixmap(gPixmapPtr())
        scale = AVSwitch().getFramebufferScale()
        size = self["cover"].instance.size()
        picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, "#FF000000"))
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
        if config.plugins.ARD.SaveResumePoint.value:
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
        self.title = "Einstellungen"
        self.session = session
        self.skinName = ["Setup"]
        self["key_red"] = StaticText("Abbrechen")
        self["key_green"] = StaticText("Speichern")
        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"], {"cancel": self.cancel, "red": self.cancel, "ok": self.ok, "green": self.save}, -2)
        ConfigListScreen.__init__(self, [], session=session)
        self.ConfigList()

    def ConfigList(self):
        self["config"].list = [getConfigListEntry("Skin", config.plugins.ARD.SkinColor), getConfigListEntry("Download-Verzeichnis:", config.plugins.ARD.savetopath), getConfigListEntry("Untertitle Downloaden", config.plugins.ARD.UT_DL), getConfigListEntry("Cover Downloaden", config.plugins.ARD.COVER_DL), getConfigListEntry("Handlung Downloaden", config.plugins.ARD.DESC), getConfigListEntry("Letzte Abspielposition speichern", config.plugins.ARD.SaveResumePoint), getConfigListEntry("Unsere Region", config.plugins.ARD.Region), getConfigListEntry("AutoPlay", config.plugins.ARD.AUTOPLAY)]

    def save(self):
        self.keySave()
        self.close()

    def cancel(self):
        self.close()

    def ok(self):
        if self["config"].getCurrent()[1] == config.plugins.ARD.savetopath:
            DLdir = config.plugins.ARD.savetopath.value
            self.session.openWithCallback(self.DL_Path, DirBrowser, DLdir)

    def DL_Path(self, res):
        self["config"].setCurrentIndex(0)
        if res:
            config.plugins.ARD.savetopath.value = res


class DirBrowser(Screen):
    def __init__(self, session, DLdir):
        Screen.__init__(self, session)
        self.skinName = ["FileBrowser"]
        self["key_red"] = StaticText("Abbrechen")
        self["key_green"] = StaticText("Speichern")
        if not path.exists(DLdir):
            DLdir = "/"
        self.filelist = FileList(DLdir, showFiles=False)
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
