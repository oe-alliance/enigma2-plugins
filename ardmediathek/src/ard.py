# -*- coding: UTF-8 -*-
import re
import time
import xml.etree.ElementTree as Et
from datetime import datetime, timedelta
from json import loads
from os import mkdir, path, unlink
import requests
import skin
from Components.ActionMap import ActionMap
from Components.config import ConfigDirectory, ConfigSelection, ConfigSubsection, ConfigYesNo, config, configfile, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from enigma import addFont, eConsoleAppContainer, ePicLoad, eServiceReference, getDesktop, gPixmapPtr
from Screens import InfoBarGenerics
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from six import ensure_str
from six.moves.urllib.parse import quote_plus
from Tools.Downloader import downloadWithProgress
from twisted.internet.reactor import callInThread

config.plugins.ARD = ConfigSubsection()
config.plugins.ARD.savetopath = ConfigDirectory(default="/media/hdd/movie/")
config.plugins.ARD.SaveResumePoint = ConfigYesNo(default=False)
config.plugins.ARD.UT_DL = ConfigYesNo(default=False)
config.plugins.ARD.COVER_DL = ConfigSelection(default="nein", choices=[("nein", "Nein"), (".jpg", "jpg"), (".bdp.jpg", "bdp.jpg")])
config.plugins.ARD.DESC = ConfigYesNo(default=False)
PLUGINPATH = "/usr/lib/enigma2/python/Plugins/Extensions/ArdMediathek/"
RegionList = [("bw", ("Baden-Württemberg (SWR)")), ("by", ("Bayern (BR)")), ("be", ("Berlin (rbb)")), ("bb", ("Brandenburg (rbb)")), ("hb", ("Bremen (radiobremen)")), ("hh", ("Hamburg (NDR)")), ("he", ("Hessen (hr)")), ("mv", ("Mecklenburg-Vorpommern (NDR)")), ("ni", ("Niedersachsen (NDR)")), ("nw", ("Nordrhein-Westfalen (WDR)")), ("rp", ("Rheinland-Pfalz (SWR)")), ("sl", ("Saarland (SR)")), ("sn", ("Sachsen (mdr)")), ("st", ("Sachsen-Anhalt (mdr)")), ("sh", ("Schleswig-Holstein (NDR)")), ("th", ("Thüringen (mdr)"))]
config.plugins.ARD.Region = ConfigSelection(default="nw", choices=RegionList)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"
TMPIC = "/tmp/cover/bild.jpg"
SKINFILE = PLUGINPATH + "skin_FHD.xml" if getDesktop(0).size().height() > 720 else PLUGINPATH + "skin_HD.xml"
FONT = "/usr/share/fonts/LiberationSans-Regular.ttf"
if not path.exists(FONT):
    FONT = "/usr/share/fonts/nmsbd.ttf"
addFont(FONT, "SRegular", 100, False)
API_URL = "https://api.ardmediathek.de/page-gateway/"
URL_HOME = API_URL + "pages/%s/home?embedded=true"
URL_AZ = API_URL + "pages/%s/editorial/experiment-a-z?embedded=true"
ColorList = [("glass,#40000000,#5a000000,#37cccccc", "Black Glass"), ("glass,#5a082567,#5a000000,#37cccccc", "SapphireBlue Glass"), ("glass,#5a080828,#5a000000,#37cccccc", "MagentaBlue Glass"), ("glass,#e615d7b6,#5a000000,#37cccccc", "PaleGreen Glass"), ("glass,#5aa0785a,#5a000000,#37cccccc", "Chamoisee Glass"), ("transparent,#050a1232,#1502050e,#05192d7c", "DarkBlue Transparent"), ("transparent,#05000000,#15000000,#606060", "BlackGray Transparent"), ("transparent,#05000000,#15000000,#ffff00", "BlackYellow Transparent"), ("transparent,#1a104485,#3D104485,#1aC0C0C0", "BrightBlue Transparent"), ("transparent,#1a746962,#1502050e,#1a746962", "BrownBlue Transparent"), ("MiniTV,#104485,#0c366a,#C0C0C0", "BrightBlue MiniTV"), ("MiniTV,#0a1232,#02050e,#192d7c", "DarkBlue MiniTV"), ("MiniTV,#000000,#080808,#606060", "BlackGray MiniTV"), ("MiniTV,#000000,#080808,#ffff00", "BlackYellow MiniTV"), ("MiniTV,#746962,#02050e,#746962", "BrownBlue MiniTV")]
config.plugins.ARD.SkinColor = ConfigSelection(default="glass,#5a082567,#5a000000,#37cccccc", choices=ColorList)


def readskin():
    cf = config.plugins.ARD.SkinColor.value.split(",")
    s = ""
    try:
        with open(SKINFILE, "r") as f:
            root = Et.parse(f).getroot()
        for element in root:
            if element.tag == "screen" and element.attrib["name"] == cf[0]:
                s = ensure_str(Et.tostring(element))
        if hasattr(skin.AttributeParser, "scrollbarForegroundColor"):
            s = s.replace("scrollbarSliderForegroundColor", "scrollbarForegroundColor")
    except (IOError, Et.ParseError):
        return ""
    return s.strip().replace("{col1}", cf[1]).replace("{col2}", cf[2]).replace("{col3}", cf[3]).replace("{picpath}", PLUGINPATH + "img/")


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
    except (TypeError, ValueError, AttributeError, OverflowError):
        return ""


def sortList(txt):
    return sorted(txt, key=lambda text: int(re.compile(r"(\d+)x", re.DOTALL).findall(text[0])[0]) if re.compile(r"(\d+)x", re.DOTALL).findall(str(text[0])) else 0, reverse=True)


class ArdMediathek(Screen):
    def __init__(self, session):
        s = readskin()
        self.skin = s
        Screen.__init__(self, session)
        self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "ChannelSelectBaseActions", "MenuActions"], {"menu": self.ARDSetup, "green": self.Download, "red": self.close, "blue": self.Home, "up": self.up, "down": self.down, "left": self.left, "right": self.right, "nextBouquet": self.p_up, "prevBouquet": self.p_down, "ok": self.ok, "cancel": self.exit}, -1)
        self["movielist"] = List()
        self["cover"] = Pixmap()
        self["handlung"] = ScrollLabel()
        self.HISTORY = [("MENU", "")]
        self["DownloadLabel"] = ScrollLabel()
        self["PluginName"] = ScrollLabel("ARD Mediathek v1.8")
        self["progress"] = ProgressBar()
        self["progress"].hide()
        self.PROGRAMM = "ard"
        self.DL_File = None
        if not path.exists("/tmp/cover/"):
            mkdir("/tmp/cover/")
        self.onLayoutFinish.append(self.HauptMenu)

    def reload_skin(self):
        self.session.open(ArdMediathek)
        self.close()

    def ARDSetup(self):
        self.session.openWithCallback(self.reload_skin, ARDConfigScreen)

    def HauptMenu(self, index="0"):
        self.searchtxt = ""
        self.PROGRAMM = "ard"
        menu = [("MENU", "ARD Mediathek - Start", URL_HOME % self.PROGRAMM, "", PLUGINPATH + "/img/" + "home.png", ""), ("MENU", "Entdecken", API_URL + "pages/ard/editorial/entdecken?embedded=true", "", PLUGINPATH + "/img/" + "endecken.png", ""), ("SenderMenu", "Sender", "SenderMenu", "", PLUGINPATH + "/img/" + "sender.png", ""), ("ProgrammMenu", "Sendung verpasst", "ProgrammMenu", "", PLUGINPATH + "/img/" + "programm.png", ""), ("MENU", "Sendungen A-Z", URL_AZ % "ard", "", PLUGINPATH + "/img/" + "az.png", ""), ("MENU", "LIVE", API_URL + "widgets/ard/editorials/4hEeBDgtx6kWs6W6sa44yY?pageNumber=0&pageSize=24&embedded=true", "", PLUGINPATH + "/img/" + "live.png", ""), ("Suche", "Suche", "", "", PLUGINPATH + "/img/" + "suche.png", "")]
        self["movielist"].setList(menu)
        self["movielist"].setIndex(int(index))
        self.infos()

    def ok(self):
        item = self["movielist"].getCurrent()
        item_type = item[0]
        url = item[2]
        if item_type == "Suche":
            self.session.openWithCallback(self.search, VirtualKeyBoard, title="ARD Mediathek Suche")
        elif item_type == "PLAY":
            self.cdn(download=False)
        elif item_type == "LIVE":
            if path.exists("/usr/bin/exteplayer3"):
                self.cdn(download=False, live=True)
            else:
                self.session.open(MessageBox, "Bitte installieren Sie exteplayer3, um den Livestream abspielen zu können.", MessageBox.TYPE_INFO)
        else:
            index = self["movielist"].getIndex()
            if item_type in ["MENU", "WEITER"]:
                self.Widgets(url)
            elif item_type == "Sender2Menu":
                self.PROGRAMM = url
                self.Menu2Sender()
                url = "Sender2Menu"
            elif item_type == "Programm3":
                self.PROGRAMM = url
                url = "Programm3"
                self.Programm3()
            elif item_type == "SenderMenu":
                self.SenderMenu("0", "Sender2Menu")
            elif item_type == "ProgrammMenu":
                self.SenderMenu("0", "Programm3")
            else:
                return
            self.HISTORY.append((url, index))

    def Home(self):
        self.HISTORY = [("MENU", "")]
        self.HauptMenu()

    def exit(self):
        if len(self.HISTORY) > 1:
            index = self.HISTORY[-1][1]
            self.HISTORY.pop()
            url = self.HISTORY[-1][0]
            if url.startswith("http"):
                self.Widgets(url, index)
            elif url == "MENU":
                self.HauptMenu(index)
            elif url == "SenderMenu":
                self.SenderMenu(index, "Sender2Menu")
            elif url == "Sender2Menu":
                self.Menu2Sender(index)
            elif url == "ProgrammMenu":
                self.SenderMenu(index, "Programm3")
            elif url == "Programm3":
                self.Programm3(index)
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
        for i in range(7):
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
            self.HISTORY.append((url, self["movielist"].getIndex()))
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
            if js.get("type", "") in ("external", "top_navigation") or "LOGGED" in js.get("userVisibility", ""):
                continue
            plot = ""
            title = js.get("title") if js.get("title") else js.get("longTitle", "")
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
            if js.get("duration") or js.get("type") in ("event", "broadcastMainClip"):
                liste.append(("PLAY", ensure_str(title), ensure_str(url2), ensure_str(plot), ensure_str(img), duration))
            elif js.get("type") in ("live"):
                liste.append(("LIVE", ensure_str(title), ensure_str(url2), ensure_str(plot), ensure_str(img), duration))
            elif js.get("type") == "region_gridlist":
                liste.append(("WEITER", ensure_str(title) + " " + config.plugins.ARD.Region.value.upper(), ensure_str(url2.replace("{regionId}", config.plugins.ARD.Region.value)), ensure_str(plot), img, duration))
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
                liste.append(("WEITER", "NextPage (" + str(int(pageNumber) + 2) + " / " + str(maxpage) + ")", ensure_str(url), "", PLUGINPATH + "/img/" + "nextpage.png", ""))
        if liste:
            self["movielist"].setList(liste)
            self["movielist"].setIndex(int(index))
            self.infos()

    def Download(self):
        self.cdn(download=True)

    def Live(self):
        self.cdn(live=True)

    def cdn(self, download=False, live=False):
        if self.DL_File and download is True:
            self.session.openWithCallback(self.DL_Stop, MessageBox, "Möchten Sie den Download abbrechen?", default=True, type=MessageBox.TYPE_YESNO)
        else:
            liste = []
            UT = ""
            url = self["movielist"].getCurrent()[2]
            data = ensure_str(geturl(url + "&mcV6=true"))
            if data and "widgets" in data:
                js = loads(data)
                js = js.get("widgets")[0] if js.get("widgets") else {}
                coreAssetType = js.get("show").get("coreAssetType", "") == "SEASON_SERIES" if js.get("show") else False
                title = ("%s - %s") % (js.get("show", {}).get("title", ""), js.get("title", "")) if coreAssetType else js.get("title", "")
                if "agesschau" in title and js.get("broadcastedOn"):
                    title = "%s(%s)" % (title, js.get("broadcastedOn")[:10])
                filename = "".join(i for i in ensure_str(title) if i not in r'\/":*?<>|')
                if 'blockedByFsk":true' in data:
                    data = ensure_str(geturl("%smediacollectionv6/%s?isTv=false" % (API_URL, js.get("id", ""))))
                    if data:
                        data = loads(data)
                else:
                    js = js.get("mediaCollection") if js.get("mediaCollection") else {}
                    data = js.get("embedded") if js.get("embedded") else {}
            data = data or {}
            UT = next((media.get("url", "") for sub in data.get("subtitles", []) for media in sub.get("sources", []) if media.get("kind", "") == "webvtt"), "")

            for stream in data.get("streams", []):
                kind_name = "(%s)" % stream.get("kindName") if stream.get("kindName") and stream.get("kindName") != "Normal" else ""
                for media in stream.get("media", []):
                    url = str(media.get("url", ""))
                    if not url:
                        continue
                    res = "%sx%s%s" % (media.get("maxHResolutionPx", "0"), media.get("maxVResolutionPx", "0"), kind_name)
                    audios = media.get("audios", [{}])[0]
                    language_code = audios.get("languageCode", "")
                    if "desc" in str(audios.get("kind", "")):
                        res += "(AD)"
                    if language_code and "deu" not in language_code:
                        res += "(%s)" % language_code.upper()
                    if download is True:
                        if ".m3u8" in url:
                            continue
                        liste.append(("%s_%s.mp4" % (filename, res), url + "##" + UT))
                    elif "m3u8" in url:
                        if live:
                            liste.append(("M3U8 | %s" % (res), url))
                    else:
                        liste.append(("MP4 | %s" % (res), url))
            liste = sortList(liste)
            if download is True and len(liste) > 1:
                self.session.openWithCallback(self.DL_Start, ChoiceBox, title="Download starten?", list=liste)
            elif liste and live:
                self.session.open(LivePlayer, liste[0][1])
            elif len(liste) > 1:
                self.session.openWithCallback(self.Player, ChoiceBox, title="Wiedergabe starten?", list=liste)
            else:
                self.session.open(MessageBox, "Kein Eintrag vorhanden", MessageBox.TYPE_INFO)

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
            if not config.plugins.ARD.COVER_DL.value == "nein":
                downloader = downloadWithProgress(str(self["movielist"].getCurrent()[4].replace("w=360", "w=1080")), self.DL_File[:-4] + str(config.plugins.ARD.COVER_DL.value))
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
        filename = self.DL_File.rsplit(".", 1)[0]
        for ext in (".srt", ".jpg", ".bdp.jpg", ".txt"):
            fileext = filename + ext
            if path.exists(fileext):
                unlink(fileext)
        self.DL_File = None

    def DL_Stop(self, answer):
        if answer:
            self.downloader.stop()
            self.fileClean()
            self["progress"].hide()
            self["DownloadLabel"].hide()

    def DL_finished(self, s=""):
        if self:
            self.DL_File = None
            self["progress"].hide()
            self["DownloadLabel"].hide()
            self.session.open(MessageBox, "Download erfolgreich %s" % s, MessageBox.TYPE_INFO, timeout=5)

    def DL_failed(self, error):
        self["progress"].hide()
        self["DownloadLabel"].hide()
        self.downloader.stop()
        self.fileClean()
        self.session.open(MessageBox, "Download-Fehler %s" % error, MessageBox.TYPE_INFO)

    def DL_progress(self, recvbytes, totalbytes):
        try:
            self["DownloadLabel"].setText(str(recvbytes // 1024 // 1024) + "MB/" + str(totalbytes // 1024 // 1024) + "MB")
            self["progress"].setValue(int(100 * recvbytes // totalbytes))
        except KeyError:
            pass

    def Player(self, url):
        url = url and url[1]
        if url:
            sref = eServiceReference(4097, 0, ensure_str(url))
            sref.setName(self["movielist"].getCurrent()[1])
            self.session.open(Player, sref)

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
                img = PLUGINPATH + "/img/nocover.png"
                self.get_cover(img)

    def getimage(self, url, index=0):
        try:
            data = geturl(url)
            with open(TMPIC, "wb") as f:
                f.write(data)
            if self["movielist"].getCurrent() is not None:
                if index == int(self["movielist"].getIndex()):
                    self.get_cover(TMPIC)
        except (IOError, KeyError):
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


class LivePlayer(Screen):
    def __init__(self, session, url):
        self.url = url
        self.skin = """<screen name="Player" position="0,0" size="0, 0" flags="wfNoBorder"> </screen>"""
        Screen.__init__(self, session)
        self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.exit}, -1)
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.console = eConsoleAppContainer()
        self.console.dataAvail.append(self.avail)
        self.onLayoutFinish.append(self.layoutFinished)

    def avail(self, txt):
        if txt:
            pass

    def ok(self):
        pass

    def exit(self):
        self.session.nav.playService(self.oldService)
        self.console.sendCtrlC()
        self.close()

    def layoutFinished(self):
        self.session.nav.stopService()
        parameter = "-l"
        if "###" in self.url:
            video, audio = self.url.split("###")
            cmd = "exteplayer3 %s -x %s %s" % (video, audio, parameter)
        else:
            cmd = "exteplayer3 %s %s" % (self.url, parameter)
        self.console.execute(cmd)


class Player(MoviePlayer):
    ENABLE_RESUME_SUPPORT = True

    def __init__(self, session, service):
        MoviePlayer.__init__(self, session, service)
        self.skinName = "MoviePlayer"

    def up(self):
        pass

    def down(self):
        pass

    def leavePlayer(self):
        if config.plugins.ARD.SaveResumePoint.value and hasattr(InfoBarGenerics, "setResumePoint"):
            InfoBarGenerics.setResumePoint(self.session)
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
        self.list = [getConfigListEntry("Skin", config.plugins.ARD.SkinColor), getConfigListEntry("Download-Verzeichnis:", config.plugins.ARD.savetopath), getConfigListEntry("Untertitle Downloaden", config.plugins.ARD.UT_DL), getConfigListEntry("Cover Downloaden", config.plugins.ARD.COVER_DL), getConfigListEntry("Handlung Downloaden", config.plugins.ARD.DESC), getConfigListEntry("Unsere Region", config.plugins.ARD.Region)]
        if hasattr(InfoBarGenerics, "setResumePoint"):
            self.list.append(getConfigListEntry("Letzte Abspielposition speichern", config.plugins.ARD.SaveResumePoint))
        self["config"].list = self.list

    def save(self):
        self.keySave()
        configfile.save()
        self.close()

    def cancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()

    def ok(self):
        if self["config"].getCurrent()[1] == config.plugins.ARD.savetopath:
            self.session.openWithCallback(self.DL_Path, DirBrowser, config.plugins.ARD.savetopath.value)

    def DL_Path(self, res):
        self["config"].setCurrentIndex(0)
        if res:
            config.plugins.ARD.savetopath.value = res


class DirBrowser(Screen):
    def __init__(self, session, ddir):
        Screen.__init__(self, session)
        self.skinName = ["FileBrowser"]
        self["key_red"] = StaticText("Abbrechen")
        self["key_green"] = StaticText("Speichern")
        if not path.exists(ddir):
            ddir = "/"
        self.filelist = FileList(ddir, showFiles=False)
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
