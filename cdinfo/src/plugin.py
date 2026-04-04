from enigma import eConsoleAppContainer
import shlex
import xml.dom.minidom

from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Screens.Screen import Screen
from Components.config import (
    config,
    ConfigSubsection,
    ConfigInteger,
    ConfigYesNo,
    ConfigText,
    getConfigListEntry,
)
from Components.ConfigList import ConfigListScreen

from . import _


DEFAULT_CDDB_SERVER = "gnudb.gnudb.org"
DEFAULT_CDDB_PORT = 8880
DEFAULT_CDDB_TIMEOUT = 20
DEFAULT_DISPLAY_STRING = "$i - $t ($a)"


config.plugins.CDInfo = ConfigSubsection()
config.plugins.CDInfo.useCDTEXT = ConfigYesNo(default=True)
config.plugins.CDInfo.useCDDB = ConfigYesNo(default=True)
config.plugins.CDInfo.displayString = ConfigText(DEFAULT_DISPLAY_STRING, fixed_size=False)
config.plugins.CDInfo.preferCDDB = ConfigYesNo(default=False)
config.plugins.CDInfo.CDDB_server = ConfigText(DEFAULT_CDDB_SERVER, fixed_size=False)
config.plugins.CDInfo.CDDB_port = ConfigInteger(DEFAULT_CDDB_PORT, limits=(1, 65535))
config.plugins.CDInfo.CDDB_timeout = ConfigInteger(DEFAULT_CDDB_TIMEOUT, limits=(-1, 60))
config.plugins.CDInfo.CDDB_cache = ConfigYesNo(default=True)


class CDInfo(ConfigListScreen, Screen):
    skin = """
        <screen position="90,95" size="560,430" title="CDInfo" >
            <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
            <widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
            <widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
            <widget name="info" position="20,50" size="520,40" font="Regular;20" transparent="1" />
            <widget name="config" position="20,120" size="520,200" scrollbarMode="showOnDemand" />
            <widget name="info2" position="20,340" size="520,80" font="Regular;20" transparent="1" />
        </screen>
        """

    def __init__(self, session, args=None):
        self.skin = CDInfo.skin
        Screen.__init__(self, session)

        self["info"] = Label(_("Gather audio cd album information and track listing from CDDB (online database) and / or CD-Text (from medium)."))

        self["info2"] = Label(_("Playlist string variables: $i=track, $t=title, $a=artist\nCDDB query will not delay start of audio CD playback. The request will be sent asynchronously and playlist text will be updated when match was found."))

        self.list = []
        self.list.append(getConfigListEntry(_("Try to extract CDTEXT"), config.plugins.CDInfo.useCDTEXT))
        self.list.append(getConfigListEntry(_("Try to query CDDB"), config.plugins.CDInfo.useCDDB))
        self.list.append(getConfigListEntry(_("Playlist string"), config.plugins.CDInfo.displayString))
        self.list.append(getConfigListEntry(_("CDDB overwrites CDTEXT info"), config.plugins.CDInfo.preferCDDB))
        self.list.append(getConfigListEntry(_("CDDB server hostname"), config.plugins.CDInfo.CDDB_server))
        self.list.append(getConfigListEntry(_("CDDB server port number"), config.plugins.CDInfo.CDDB_port))
        self.list.append(getConfigListEntry(_("CDDB retrieval timeout (s)"), config.plugins.CDInfo.CDDB_timeout))
        self.list.append(getConfigListEntry(_("Store local CDDB cache"), config.plugins.CDInfo.CDDB_cache))

        ConfigListScreen.__init__(self, self.list)
        self["key_red"] = Button(_("cancel"))
        self["key_green"] = Button(_("ok"))
        self["key_blue"] = Button(_("defaults"))

        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"], {
            "green": self.save,
            "red": self.cancel,
            "blue": self.defaults,
            "save": self.save,
            "cancel": self.cancel,
            "ok": self.save,
        }, -2)

    def save(self):
        for entry in self["config"].list:
            entry[1].save()
        self.close(True)

    def cancel(self):
        for entry in self["config"].list:
            entry[1].cancel()
        self.close(False)

    def defaults(self):
        config.plugins.CDInfo.useCDTEXT.setValue(True)
        config.plugins.CDInfo.useCDDB.setValue(True)
        config.plugins.CDInfo.displayString.setValue(DEFAULT_DISPLAY_STRING)
        config.plugins.CDInfo.preferCDDB.setValue(False)
        config.plugins.CDInfo.CDDB_server.setValue(DEFAULT_CDDB_SERVER)
        config.plugins.CDInfo.CDDB_port.setValue(DEFAULT_CDDB_PORT)
        config.plugins.CDInfo.CDDB_timeout.setValue(DEFAULT_CDDB_TIMEOUT)
        config.plugins.CDInfo.CDDB_cache.setValue(True)
        for entry in self["config"].list:
            entry[1].save()
        self.close(True)


class Query(object):
    def __init__(self, mediaplayer):
        self.playlist = mediaplayer.playlist
        self.mp = mediaplayer
        self.cddb_container = eConsoleAppContainer()
        self.cddb_output = ""
        self.cdtext_container = eConsoleAppContainer()
        self.cdtext_output = ""
        self.tracklisting = {}
        self.albuminfo = {}

    def getText(self, nodelist):
        parts = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                parts.append(node.data)
        return "".join(parts).strip()

    def xml_parse_output(self, data):
        if isinstance(data, bytes):
            data = data.decode("utf-8", "replace")
        elif not isinstance(data, str):
            data = str(data)

        data = data.replace("&", "&amp;")
        try:
            cdinfodom = xml.dom.minidom.parseString(data.encode("ascii", "xmlcharrefreplace"))
        except Exception as err:
            print("[xml_parse_output] error, could not parse: %s" % err)
            return False

        self.albuminfo = {}
        self.tracklisting = {}

        xmldata = cdinfodom.childNodes[0]
        queries = xmldata.childNodes
        self.xml_parse_query(queries)
        print("[xml_parse_output] albuminfo: %s" % self.albuminfo)
        print("[xml_parse_output] tracklisting: %s" % self.tracklisting)
        return True

    def xml_parse_query(self, queries_xml):
        for queries in queries_xml:
            if queries.nodeType == xml.dom.minidom.Element.nodeType and queries.tagName == "query":
                print("[xml_parse_query] cdinfo source is %s, hit %s of %s" % (
                    queries.getAttribute("source"),
                    queries.getAttribute("match"),
                    queries.getAttribute("num_matches"),
                ))
                for query in queries.childNodes:
                    if query.nodeType == xml.dom.minidom.Element.nodeType:
                        if query.tagName == "albuminfo":
                            self.xml_parse_albuminfo(query.childNodes)
                        elif query.tagName == "tracklisting":
                            self.xml_parse_tracklisting(query.childNodes)

    def xml_parse_albuminfo(self, albuminfo_xml):
        for albuminfo in albuminfo_xml:
            if albuminfo.nodeType != xml.dom.minidom.Element.nodeType:
                continue

            tag_name = albuminfo.tagName.lower()
            text = self.getText(albuminfo.childNodes)

            if tag_name in ("performer", "artist"):
                self.albuminfo["artist"] = text
            elif tag_name == "title":
                self.albuminfo["title"] = text
            elif tag_name == "year":
                self.albuminfo["year"] = text
            elif tag_name == "genre":
                self.albuminfo["genre"] = text
            elif tag_name == "category" and "genre" not in self.albuminfo:
                self.albuminfo["genre"] = text

    def xml_parse_tracklisting(self, tracklisting_xml):
        for tracklist in tracklisting_xml:
            if tracklist.nodeType != xml.dom.minidom.Element.nodeType or tracklist.tagName != "track":
                continue

            try:
                index = int(tracklist.getAttribute("number"))
            except (TypeError, ValueError):
                continue

            trackinfo = {}
            for track in tracklist.childNodes:
                if track.nodeType != xml.dom.minidom.Element.nodeType:
                    continue

                tag_name = track.tagName.lower()
                text = self.getText(track.childNodes)
                if tag_name in ("performer", "artist"):
                    trackinfo["artist"] = text
                elif tag_name == "title":
                    trackinfo["title"] = text

            self.tracklisting[index] = trackinfo

    def updateAlbuminfo(self, replace=False):
        for tag, value in self.albuminfo.items():
            if tag not in self.mp.AudioCD_albuminfo or replace:
                self.mp.AudioCD_albuminfo[tag] = value

    def updatePlaylist(self, replace=False):
        service_refs = self.playlist.getServiceRefList()
        for idx in range(len(self.playlist)):
            if idx >= len(service_refs):
                break

            ref = service_refs[idx]
            track = idx + 1
            if track not in self.tracklisting:
                continue

            if replace or not ref.getName():
                trackinfo = self.tracklisting[track]
                display_string = config.plugins.CDInfo.displayString.value.replace("$i", str(track))
                display_string = display_string.replace("$t", trackinfo.get("title", ""))
                display_string = display_string.replace("$a", trackinfo.get("artist", ""))
                ref.setName(display_string)
                self.playlist.updateFile(idx, ref)

        self.playlist.updateList()

    def scan(self):
        if config.plugins.CDInfo.useCDTEXT.value:
            self.cdtext_scan()
        if config.plugins.CDInfo.useCDDB.value:
            self.cddb_scan()

    def _execute(self, container, cmd):
        print("[execute] %s" % cmd)
        return container.execute("/bin/sh", "/bin/sh", "-c", cmd)

    def cdtext_scan(self):
        cmd = "cdtextinfo -xalT"
        self.cdtext_container.appClosed.append(self.cdtext_finished)
        self.cdtext_container.dataAvail.append(self.cdtext_avail)
        self._execute(self.cdtext_container, cmd)

    def cddb_scan(self):
        cmd = (
            "cdtextinfo -xalD --cddb-port=%d --cddb-server=%s --cddb-timeout=%s"
            % (
                config.plugins.CDInfo.CDDB_port.value,
                shlex.quote(config.plugins.CDInfo.CDDB_server.value),
                config.plugins.CDInfo.CDDB_timeout.value,
            )
        )
        if not config.plugins.CDInfo.CDDB_cache.value:
            cmd += " --no-cddb-cache"

        self.cddb_container.appClosed.append(self.cddb_finished)
        self.cddb_container.dataAvail.append(self.cddb_avail)
        self._execute(self.cddb_container, cmd)

    def cddb_avail(self, data):
        if isinstance(data, bytes):
            data = data.decode("utf-8", "replace")
        self.cddb_output += data

    def cdtext_avail(self, data):
        if isinstance(data, bytes):
            data = data.decode("utf-8", "replace")
        self.cdtext_output += data

    def cddb_finished(self, retval):
        if self.cddb_finished in self.cddb_container.appClosed:
            self.cddb_container.appClosed.remove(self.cddb_finished)
        if self.cddb_avail in self.cddb_container.dataAvail:
            self.cddb_container.dataAvail.remove(self.cddb_avail)

        if not self.xml_parse_output(self.cddb_output):
            self.cddb_output = ""
            return

        self.updatePlaylist(replace=config.plugins.CDInfo.preferCDDB.value)
        self.updateAlbuminfo(replace=config.plugins.CDInfo.preferCDDB.value)
        self.mp.readTitleInformation()
        self.cddb_output = ""

    def cdtext_finished(self, retval):
        if self.cdtext_finished in self.cdtext_container.appClosed:
            self.cdtext_container.appClosed.remove(self.cdtext_finished)
        if self.cdtext_avail in self.cdtext_container.dataAvail:
            self.cdtext_container.dataAvail.remove(self.cdtext_avail)

        if not self.xml_parse_output(self.cdtext_output):
            self.cdtext_output = ""
            return

        replace = not config.plugins.CDInfo.preferCDDB.value
        self.updatePlaylist(replace=replace)
        self.updateAlbuminfo(replace=replace)
        self.mp.readTitleInformation()
        self.cdtext_output = ""


def main(session, **kwargs):
    session.open(CDInfo)


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="CDInfo",
            description=_("AudioCD info from CDDB & CD-Text"),
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main,
            icon="plugin.png",
        )
    ]
