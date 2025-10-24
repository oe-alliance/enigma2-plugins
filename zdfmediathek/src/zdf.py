# -*- coding: UTF-8 -*-
from os import mkdir, system, unlink, path
from datetime import datetime, timedelta
from json import loads
import xml.etree.ElementTree as Et
import requests
from Components.ActionMap import ActionMap
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
config.plugins.ZDF = ConfigSubsection()
config.plugins.ZDF.savetopath = ConfigDirectory(default="/media/hdd/movie/")
config.plugins.ZDF.SaveResumePoint = ConfigYesNo(default=False)
config.plugins.ZDF.UT_DL = ConfigYesNo(default=False)
config.plugins.ZDF.COVER_DL = ConfigYesNo(default=False)
PLUGINPATH = "/usr/lib/enigma2/python/Plugins/Extensions/ZDFMediathek/"
FHD = getDesktop(0).size().height() > 720
SKINFILE = PLUGINPATH + "skin_FHD.xml" if FHD else PLUGINPATH + "skin_HD.xml"
FONT = "/usr/share/fonts/LiberationSans-Regular.ttf"
if not path.exists(FONT):
    FONT = "/usr/share/fonts/nmsbd.ttf"
addFont(FONT, "SRegular", 100, False)
API_URL = "https://zdf-prod-futura.zdf.de/mediathekV2/"
ColorList = [("default,#1a104485,#3D104485,#1aC0C0C0", "Trans-BrightBlue"), ("default,#050a1232,#1502050e,#05192d7c", "Trans-DarkBlue"), ("default,#05000000,#15000000,#606060", "Trans-BlackGray"), ("default,#05000000,#15000000,#ffff00", "Trans-BlackYellow"), ("default,#1a746962,#1502050e,#1a746962", "Trans-BrownBlue"), ("MiniTV,#104485,#0c366a,#C0C0C0", "BrightBlue MiniTV"), ("MiniTV,#0a1232,#02050e,#192d7c", "DarkBlue MiniTV"), ("MiniTV,#000000,#080808,#606060", "BlackGray MiniTV"), ("MiniTV,#000000,#080808,#ffff00", "BlackYellow MiniTV"), ("MiniTV,#746962,#02050e,#746962", "BrownBlue MiniTV")]
config.plugins.ZDF.SkinColor = ConfigSelection(default="default,#050a1232,#1502050e,#05192d7c", choices=ColorList)


def readskin():
    cf = config.plugins.ZDF.SkinColor.value.split(",")
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
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0"})
        return response.content
    except Exception:
        return ""


def ImageUrl(img):
    img = img.get("teaserBild", {})
    return img.get("384").get("url", "") if img.get("384") else img.get("380", {}).get("url", "")


class ZDFMediathek(Screen):
    def __init__(self, session):
        self.skin = readskin()
        Screen.__init__(self, session)
        self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "ChannelSelectBaseActions", "MenuActions"], {"menu": self.ZDFSetup, "green": self.Download, "red": self.close, "blue": self.Home, "up": self.up, "down": self.down, "left": self.left, "right": self.right, "nextBouquet": self.p_up, "prevBouquet": self.p_down, "ok": self.ok, "cancel": self.exit}, -1)
        self["movielist"] = List()
        self["cover"] = Pixmap()
        self["handlung"] = ScrollLabel()
        self["DownloadLabel"] = ScrollLabel()
        self["progress"] = ProgressBar()
        self["progress"].hide()
        self.DL_File = None
        self.HISTORY = [("MENU", "", "", "")]
        if not path.exists("/tmp/cover/"):
            mkdir("/tmp/cover/")
        self.onLayoutFinish.append(self.HauptMenu)

    def ZDFSetup(self):
        self.session.open(ZDFConfigScreen)

    def HauptMenu(self, index="0"):
        menu = [("LISTE", "ZDF Mediathek - Start", API_URL + "start-page", "", PLUGINPATH + "/img/" + "home.png", ""), ("LISTE", "ZDF Info", API_URL + "document/zdf-info-100", "", PLUGINPATH + "/img/" + "home.png", ""), ("LISTE", "ZDF tivi", API_URL + "document/zdftivi-fuer-kinder-100", "", PLUGINPATH + "/img/" + "home.png", ""), ("LISTE", "Rubriken", API_URL + "categories-overview", "", PLUGINPATH + "/img/" + "endecken.png", ""), ("LISTE", "Sendung  A - Z", API_URL + "document/sendungen-100", "", PLUGINPATH + "/img/" + "az.png", ""), ("BROADCAST", "Sendung  Verpasst", "", "", PLUGINPATH + "/img/" + "programm.png", ""), ("SUCHE", "Suche", "", "", PLUGINPATH + "/img/" + "suche.png", "")]
        self["movielist"].setList(menu)
        self["movielist"].setIndex(int(index))
        self.infos()

    def ok(self):
        Type = self["movielist"].getCurrent()[0]
        teaser = ""
        if Type == "SUCHE":
            self.session.openWithCallback(self.search, VirtualKeyBoard, title="ZDF Mediathek Suche")
        elif Type == "PLAY":
            self.Play()
        elif Type == "LIVE":
            self.session.open(MessageBox, "Achtung! Livestreams werden in der aktuellen Version noch nicht unterstützt.", MessageBox.TYPE_INFO)
        else:
            Index = self["movielist"].getIndex()
            url = self["movielist"].getCurrent()[2]
            if Type == "LISTE":
                self.Cluster(url)
            elif Type == "TEASER":
                teaser = self["movielist"].getCurrent()[7]
                self.teaser(url, teaser)
            elif Type == "STAGE":
                self.Stage(url)
            elif Type == "BROADCAST":
                self.Broadcast()
            else:
                self.session.open(MessageBox, Type, MessageBox.TYPE_INFO)
            self.HISTORY.append((Type, url, Index, teaser))
            self.infos()

    def Download(self):
        if self.DL_File:
            self.session.openWithCallback(self.DL_Stop, MessageBox, "möchten Sie den Download abbrechen?", default=True, type=MessageBox.TYPE_YESNO)
        else:
            url = self["movielist"].getCurrent()[2]
            data = ensure_str(geturl(url))
            if 'fskCheck":true' in data:
                self.session.open(MessageBox, "Das Video ist nicht für Kinder und Jugendliche geeignet und kann erst nach 22 Uhr Download werden.", MessageBox.TYPE_INFO)
                return
            liste = []
            UT = []
            filename = "".join(i for i in self["movielist"].getCurrent()[1] if i not in r'\/":*?<>|')
            if data:
                data = loads(data)
                data = data.get("document", {})
                for js in data.get("captions", []):
                    if js.get("format") == "webvtt":
                        UT.append(js.get("uri"))
                UT = UT[0] if UT else ""
                for js in data.get("formitaeten", []):
                    url = js.get("url")
                    if ".m3u8" in url:
                        continue
                    url = js.get("url").replace("1628k_p13v", "3360k_p36v").replace("808k_p11v", "2360k_p35v").replace("508k_p9v", "808k_p11v")
                    q = filename
                    if js.get("language"):
                        q += " (" + str(js.get("language").upper()) + ")"
                    if js.get("class", "") == "ad":
                        q += "(AD)"
                    if js.get("quality"):
                        q += "(" + str(js.get("quality").upper()) + ")"
                    liste.append((q + ".mp4", url + "##" + UT, q + ".srt"))
            if len(liste) > 1:
                self.session.openWithCallback(self.DL_Start, ChoiceBox, title="Download starten?", list=liste)

    def DL_Start(self, answer):
        if answer:
            UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0"
            url = answer[1].split("##")
            self.DL_File = str(config.plugins.ZDF.savetopath.value) + str(answer[0])
            if path.exists(self.DL_File):
                self.session.open(MessageBox, "Datei ist schon vorhanden", MessageBox.TYPE_INFO)
                self.DL_File = None
            else:
                if config.plugins.ZDF.COVER_DL:
                    downloader = downloadWithProgress(str(self["movielist"].getCurrent()[4]), str(config.plugins.ZDF.savetopath.value) + str(answer[2][:-3] + "jpg"))
                    if hasattr(downloadWithProgress, "setAgent"):
                        downloader.setAgent(UA)
                    downloader.start()
                if config.plugins.ZDF.UT_DL.value and url[1]:
                    downloader = downloadWithProgress(str(url[1]), str(config.plugins.ZDF.savetopath.value) + str(answer[2]))
                    if hasattr(downloadWithProgress, "setAgent"):
                        downloader.setAgent(UA)
                    downloader.start()
                self["progress"].show()
                self["DownloadLabel"].show()
                self.downloader = downloadWithProgress(str(url[0]), self.DL_File)
                if hasattr(downloadWithProgress, "setAgent"):
                    self.downloader.setAgent(UA)
                self.downloader.addProgress(self.DL_progress)
                self.downloader.addEnd(self.DL_finished)
                self.downloader.addError(self.DL_failed)
                self.downloader.start()

    def DL_Stop(self, answer):
        if answer:
            self.downloader.stop()
            if path.exists(self.DL_File):
                unlink(self.DL_File)
            if path.exists(self.DL_File[:-3] + "srt"):
                unlink(self.DL_File[:-3] + "srt")
            if path.exists(self.DL_File[:-3] + "jpg"):
                unlink(self.DL_File[:-3] + "jpg")
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
        if path.exists(self.DL_File):
            unlink(self.DL_File)
        self.DL_File = None
        self.session.open(MessageBox, "Download-Fehler %s" % error, MessageBox.TYPE_INFO)

    def DL_progress(self, recvbytes, totalbytes):
        try:
            self["DownloadLabel"].setText(str(recvbytes // 1024 // 1024) + "MB/" + str(totalbytes // 1024 // 1024) + "MB")
            self["progress"].setValue(int(100 * recvbytes // totalbytes))
        except Exception:
            pass

    def Home(self):
        self.HISTORY = [("MENU", "", "", "")]
        self.HauptMenu()

    def exit(self):
        if len(self.HISTORY) > 1:
            Index = self.HISTORY[-1][2]
            self.HISTORY.pop()
            Type = self.HISTORY[-1][0]
            url = self.HISTORY[-1][1]
            if Type == "LISTE":
                self.Cluster(url, Index)
            elif Type == "TEASER":
                self.teaser(url, self.HISTORY[-1][3], Index)
            elif Type == "STAGE":
                self.Stage(url, Index)
            elif Type == "BROADCAST":
                self.Broadcast(Index)
            elif Type == "MENU":
                self.HauptMenu(Index)
            else:
                self.session.open(MessageBox, Type, MessageBox.TYPE_INFO)
            self.infos()
        else:
            system("rm -rf /tmp/cover")
            self.close()

    def search(self, search):
        if search:
            url = API_URL + "search?q=%s" % quote_plus(search)
            self.HISTORY.append(("LISTE", url, self["movielist"].getIndex(), ""))
            self.Cluster(url, index="0")

    def Broadcast(self, index="0"):
        liste = []
        now = datetime.now()
        for i in range(0, 7):
            datum = (now + timedelta(-i)).strftime("%d-%m-%Y")
            url = API_URL + "broadcast-missed/%s" % (now + timedelta(-i)).strftime("%Y-%m-%d")
            liste.append(("LISTE", ensure_str(datum), url, "", PLUGINPATH + "/img/" + "programm.png", "", "", index))
        if liste:
            self["movielist"].setList(liste)
            self["movielist"].setIndex(int(index))

    def Stage(self, url, index="0"):
        liste = []
        data = geturl(url)
        if data:
            data = loads(ensure_str(data))
            for stage in data.get("stage", []):
                stage = self.teaserContent(stage)
                if stage:
                    liste.append(stage)
            if liste:
                self["movielist"].setList(liste)
                self["movielist"].setIndex(int(index))

    def Cluster(self, url, index="0"):
        liste = []
        html = geturl(url)
        if html:
            html = loads(ensure_str(html))
            if html.get("stage"):
                img = ImageUrl(html.get("stage")[0])
                liste.append(("STAGE", "Stage", url, "", img, "", "", ""))
            if html.get("cluster"):
                data = html.get("cluster")
            elif html.get("epgCluster"):
                data = html.get("epgCluster")
            elif html.get("broadcastCluster"):
                data = html.get("broadcastCluster")
            elif html.get("results"):
                data = html.get("results")
                if data:
                    for tc in data:
                        tc = self.teaserContent(tc)
                        if tc:
                            liste.append(tc)
            else:
                self.session.open(MessageBox, "Kein Eintrag vorhanden", MessageBox.TYPE_INFO)
                return
            tindex = -1
            for js in data:
                tindex += 1
                if not js.get("name", "") and len(js.get("teaser", "")) > 0:
                    for tc in js.get("teaser", []):
                        tc = self.teaserContent(tc)
                        if tc:
                            liste.append(tc)
                if not js.get("name", "") or len(js.get("teaser", "")) == 0:
                    continue
                title = js.get("name")
                img = ImageUrl(js.get("teaser")[0])
                if js.get("liveStream"):
                    liste.append(("LIVE", ensure_str(title), url, "", img, "", "", tindex))
                else:
                    liste.append(("TEASER", ensure_str(title), url, "", img, "", "", tindex))
            if liste:
                if html.get("nextPageUrl"):
                    liste.append(("LISTE", "Next Page", html.get("nextPageUrl"), "", PLUGINPATH + "/img/" + "nextpage.png", "", "", ""))
                self["movielist"].setList(liste)
                self["movielist"].setIndex(int(index))
        else:
            self.session.open(MessageBox, "Kein Eintrag vorhanden", MessageBox.TYPE_INFO)

    def teaserContent(self, js):
        if js.get("type") == "externalUrl" or js.get("currentVideoType") in ["novideo", "live"]:
            return None
        if js.get("seasonNumber"):
            title = "%s - S%sE%s%s" % (js.get("headline"), js.get("seasonNumber", "0"), js.get("episodeNumber", "0"), (" - " + js.get("titel") if "Episode" not in js.get("titel") else ""))
        else:
            title = js.get("titel")
        img = ImageUrl(js)
        plot = js.get("channel", "")
        contAttr = js.get("contentAttributes", {})
        plot += " " + contAttr.get("editorialDate", {}).get("title", "") + contAttr.get("productionYear", {}).get("title", "")
        sta = js.get("streamingOptions", {}).get("attrs", {})
        plot += " UHD" if sta.get("uhd", {}).get("enabled") is True else ""
        plot += " UT" if sta.get("ut", {}).get("enabled") is True else ""
        plot += " AD" if sta.get("ad", {}).get("enabled") is True else ""
        plot += " DGS" if sta.get("dgs", {}).get("enabled") is True else ""
        plot += " " + js.get("fsk", "").upper() if js.get("fsk", "") not in "none" else ""
        if not js.get("beschreibung", "") == js.get("textLong", "") and js.get("beschreibung") and js.get("textLong"):
            plot += "\n\n" + js.get("beschreibung") + "\n\n" + js.get("textLong")
        else:
            plot += "\n\n" + js.get("textLong") if js.get("textLong") else "\n\n" + js.get("beschreibung", "")
        plot += "\n\nGesendet am " + js.get("visibleFrom") if js.get("visibleFrom") else ""
        plot += "\nVerfügbar bis " + js.get("timetolive") + "\n" if js.get("timetolive") else ""
        plot += "in Deutschland" if js.get("geoLocation") == "de" else ""
        plot += "in Deutschland, Österreich, Schweiz" if js.get("geoLocation") == "dach" else ""
        plot += "\n\n" + js.get("brandTitle", "")
        duration = str(timedelta(seconds=int(js.get("length")))) if str(js.get("length")).isdigit() else ""
        url = js.get("url")
        Type = "PLAY" if js.get("type") == "video" else "LISTE"
        return Type, ensure_str(title), url, ensure_str(plot), img, duration, "", ""

    def teaser(self, url, teaser, index="0"):
        liste = []
        data = loads(geturl(url))
        if data.get("cluster"):
            cluster = data.get("cluster")[teaser]
            teaser = cluster.get("teaser")
        elif data.get("broadcastCluster"):
            cluster = data.get("broadcastCluster")[teaser]
            teaser = cluster.get("teaser")
        else:
            self.session.open(MessageBox, "Kein Eintrag vorhanden", MessageBox.TYPE_INFO)
            return

        for tc in teaser:
            tc = self.teaserContent(tc)
            if tc:
                liste.append(tc)
        if liste:
            self["movielist"].setList(liste)
            self["movielist"].setIndex(int(index))

    def Play(self):
        url = self["movielist"].getCurrent()[2]
        data = ensure_str(geturl(url))
        if 'fskCheck":true' in data:
            self.session.open(MessageBox, "Das Video ist nicht für Kinder und Jugendliche geeignet und kann erst nach 22 Uhr abgespielt werden.", MessageBox.TYPE_INFO)
            return
        liste = []
        if data:
            data = loads(data)
        if data.get("document"):
            data = data.get("document")
            if data.get("formitaeten"):
                data = data.get("formitaeten")
                for js in data:
                    url = js.get("url")
                    q = js.get("quality").upper()
                    if ".m3u8" in url:
                        q += "(M3U8)"
                    elif ".mp4" in url:
                        url = js.get("url").replace("1628k_p13v", "3360k_p36v").replace("808k_p11v", "2360k_p35v").replace("508k_p9v", "808k_p11v")
                        q += "(MP4)"
                    if js.get("language"):
                        q += " " + js.get("language").upper()
                    if js.get("class", "") == "ad":
                        q += " (AD)"
                    liste.append((ensure_str(q), url))
        if len(liste) > 1:
            self.session.openWithCallback(self.Play2, ChoiceBox, title="Wiedergabe starten?", list=sorted(liste, reverse=True, key=str))
        elif liste:
            self.Play2(liste[0])
        else:
            self.session.open(MessageBox, "Kein Eintrag vorhanden", MessageBox.TYPE_INFO)

    def Play2(self, answer):
        answer = answer and answer[1]
        if answer:
            sref = eServiceReference(4097, 0, ensure_str(answer))
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
        self["handlung"].setText(str(handlung))
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
            img = "/tmp/cover/bild.jpg"
            with open(img, "wb") as f:
                f.write(data)
            self.get_cover(img)
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
        if config.plugins.ZDF.SaveResumePoint.value:
            setResumePoint(self.session)
        self.close()

    def leavePlayerOnExit(self):
        self.leavePlayer()

    def doEofInternal(self, playing):
        if not playing or not self.execing:
            return
        self.close()


class ZDFConfigScreen(ConfigListScreen, Screen):
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
        self["config"].list = [getConfigListEntry("Skin", config.plugins.ZDF.SkinColor), getConfigListEntry("Download-Verzeichnis:", config.plugins.ZDF.savetopath), getConfigListEntry("Untertitle Downloaden", config.plugins.ZDF.UT_DL), getConfigListEntry("Cover Downloaden", config.plugins.ZDF.COVER_DL), getConfigListEntry("Letzte Abspielposition speichern", config.plugins.ZDF.SaveResumePoint)]

    def save(self):
        self.keySave()
        self.close()

    def cancel(self):
        self.close()

    def ok(self):
        if self["config"].getCurrent()[1] == config.plugins.ZDF.savetopath:
            DLdir = config.plugins.ZDF.savetopath.value
            self.session.openWithCallback(self.DL_Path, DirBrowser, DLdir)

    def DL_Path(self, res):
        self["config"].setCurrentIndex(0)
        if res:
            config.plugins.ZDF.savetopath.value = res


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
