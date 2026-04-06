# -*- coding: UTF-8 -*-
# Zap Statistic by AliAbdul
from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, eServiceReference, gFont
from Plugins.Plugin import PluginDescriptor

from Screens.ChoiceBox import ChoiceBox
from Screens.ParentalControlSetup import ProtectedScreen
from Screens.Screen import Screen
from ServiceReference import ServiceReference
from time import gmtime, localtime, strftime, time
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from xml.etree.cElementTree import parse
import gettext


PluginLanguageDomain = "ZapStatistic"
PluginLanguagePath = "Extensions/ZapStatistic/locale/"


def localeInit():
    gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
    translated = gettext.dgettext(PluginLanguageDomain, txt)
    if translated:
        return translated
    print("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt))
    return gettext.gettext(txt)


localeInit()
language.addCallback(localeInit)


def decode_charset(value, charset="UTF-8"):
    if isinstance(value, bytes):
        try:
            return value.decode(charset, "strict")
        except Exception:
            return value.decode(charset, "ignore")
    return value


def deformXml(xml):
    xml = xml.replace("&", "&amp;")
    xml = xml.replace("'", "&apos;")
    xml = xml.replace("<", "&lt;")
    xml = xml.replace(">", "&gt;")
    xml = xml.replace('"', "&quot;")
    return xml


def reformXml(xml):
    xml = xml.replace("&amp;", "&")
    xml = xml.replace("&apos;", "'")
    xml = xml.replace("&lt;", "<")
    xml = xml.replace("&gt;", ">")
    xml = xml.replace("&quot;", '"')
    return xml


class ZapEntry:
    def __init__(self, ref, begin=None, end=None):
        self.ref = ref
        self.name = ServiceReference(eServiceReference(ref)).getServiceName()
        self.begin = begin if begin is not None else time()
        self.end = end

    def stop(self):
        self.end = time()


class DurationZapEntry:
    def __init__(self, zapentry):
        self.ref = zapentry.ref
        self.name = zapentry.name
        duration = zapentry.end - zapentry.begin
        self.duration = strftime("%H:%M:%S", gmtime(duration))
        t = localtime(zapentry.begin)
        self.begin = "%02d.%02d. %02d:%02d:%02d" % (t[2], t[1], t[3], t[4], t[5])


class CombinedZapEntry:
    def __init__(self, zapentry):
        self.ref = zapentry.ref
        self.name = zapentry.name
        self.duration = zapentry.end - zapentry.begin

    def addDuration(self, zapentry):
        self.duration = self.duration + zapentry.end - zapentry.begin

    def getDurationText(self):
        return strftime("%H:%M:%S", gmtime(self.duration))


class ZapStatistic:
    def __init__(self):
        self.xmlFile = "/etc/zapstastistic.xml"
        self.zapEntries = []
        self.currentEntry = None

    def loadZapEntries(self):
        if fileExists(self.xmlFile):
            try:
                menu = parse(self.xmlFile).getroot()
                for item in menu.findall("entry"):
                    ref = item.get("ref") or None
                    if ref:
                        ref = reformXml(decode_charset(ref, "UTF-8"))
                    begin = item.get("begin") or None
                    end = item.get("end") or None
                    if ref and begin and end:
                        self.zapEntries.append(ZapEntry(ref, float(begin), float(end)))
            except Exception:
                print("[ZapStatistic] Error while reading xml file")

    def saveZapEntries(self):
        xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<zapstastistic>\n'
        for entry in self.zapEntries:
            if not entry.end:
                entry.end = time()
            xml += '\t<entry ref="%s" begin="%s" end ="%s" />\n' % (
                deformXml(decode_charset(entry.ref, "UTF-8")),
                str(entry.begin),
                str(entry.end),
            )
        xml += '</zapstastistic>'
        try:
            with open(self.xmlFile, "w", encoding="UTF-8") as handle:
                handle.write(xml)
        except Exception:
            print("[ZapStatistic] Error while writing xml file")

    def handlePlayServiceCommand(self, ref):
        self.handleStopServiceCommand()
        if ref:
            self.currentEntry = ZapEntry(ref.toString())

    def handleStopServiceCommand(self):
        if self.currentEntry:
            self.currentEntry.stop()
            self.zapEntries.append(self.currentEntry)
            self.currentEntry = None


zapstatistic = ZapStatistic()

PlayService = None
StopService = None


def playService(ref, **kwargs):
    if PlayService:
        zapstatistic.handlePlayServiceCommand(ref)
        PlayService(ref, **kwargs)


def stopService():
    if StopService:
        zapstatistic.handleStopServiceCommand()
        StopService()


class ZapStatisticBrowserList(MenuList):
    def __init__(self, entries, enableWrapAround=False):
        MenuList.__init__(self, entries, enableWrapAround, eListboxPythonMultiContent)
        self.l.setItemHeight(25)
        self.l.setFont(0, gFont("Regular", 20))


def ZapStatisticBrowserListEntry(entry):
    res = [entry]
    t_begin = localtime(entry.begin)
    t_end = localtime(entry.end)
    res.append(MultiContentEntryText(pos=(0, 0), size=(240, 25), font=0, text="%02d.%02d. %02d:%02d:%02d - %02d:%02d:%02d" % (t_begin[2], t_begin[1], t_begin[3], t_begin[4], t_begin[5], t_end[3], t_end[4], t_end[5])))
    res.append(MultiContentEntryText(pos=(250, 0), size=(310, 25), font=0, text=entry.name))
    return res


def ZapStatisticBrowserDurationListEntry(entry):
    res = [entry]
    res.append(MultiContentEntryText(pos=(0, 0), size=(240, 25), font=0, text="%s (%s)" % (entry.duration, entry.begin)))
    res.append(MultiContentEntryText(pos=(250, 0), size=(310, 25), font=0, text=entry.name))
    return res


def ZapStatisticBrowserCombinedListEntry(entry):
    res = [entry]
    res.append(MultiContentEntryText(pos=(0, 0), size=(150, 25), font=0, text="%s" % (entry.getDurationText())))
    res.append(MultiContentEntryText(pos=(160, 0), size=(400, 25), font=0, text=entry.name))
    return res


class ZapStatisticDurationScreen(Screen):
    SORT_NAME_ASCENDING = 0
    SORT_NAME_DESCENDING = 1
    SORT_DURATION_ASCENDING = 2
    SORT_DURATION_DESCENDING = 3
    skin = """
        <screen position="center,center" size="560,450" title="%s" >
            <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
            <widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="list" position="0,40" size="560,400" scrollbarMode="showOnDemand" />
        </screen>""" % _("Zap Statistic")

    def __init__(self, session):
        Screen.__init__(self, session)

        self.sortType = self.SORT_NAME_ASCENDING

        self["key_red"] = Label(_("Sort (name+)"))
        self["key_green"] = Label(_("Sort (name-)"))
        self["key_yellow"] = Label(_("Sort (duration+)"))
        self["key_blue"] = Label(_("Sort (duration-)"))
        self["list"] = ZapStatisticBrowserList([])

        self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
            {
                "ok": self.play,
                "cancel": self.close,
                "red": self.sortByNameAscending,
                "green": self.sortByNameDescending,
                "yellow": self.sortByDurationAscending,
                "blue": self.sortByDurationDescending
            }, prio=-1)

        self.onLayoutFinish.append(self.buildList)

    def sortList(self, entries):
        if self.sortType == self.SORT_NAME_ASCENDING:
            return entries.sort(key=self.buildSortNameKey, reverse=False)
        elif self.sortType == self.SORT_NAME_DESCENDING:
            return entries.sort(key=self.buildSortNameKey, reverse=True)
        elif self.sortType == self.SORT_DURATION_ASCENDING:
            return entries.sort(key=self.buildSortDurationKey, reverse=False)
        elif self.sortType == self.SORT_DURATION_DESCENDING:
            return entries.sort(key=self.buildSortDurationKey, reverse=True)
        return entries

    def buildSortNameKey(self, entry):
        try:
            name = entry.name
        except Exception:
            name = ""
        return name.lower() if name else ""

    def buildSortDurationKey(self, entry):
        try:
            duration = str(entry.duration)
        except Exception:
            duration = ""
        return duration.lower() if duration else ""

    def buildList(self):
        entries = []
        duration_entries = []
        for item in zapstatistic.zapEntries:
            duration_entries.append(DurationZapEntry(item))
        self.sortList(duration_entries)
        for item in duration_entries:
            entries.append(ZapStatisticBrowserDurationListEntry(item))
        self["list"].setList(entries)

    def play(self):
        cur = self["list"].getCurrent()
        if cur:
            entry = cur[0]
            self.session.nav.playService(eServiceReference(entry.ref))

    def sortByNameAscending(self):
        self.sortType = self.SORT_NAME_ASCENDING
        self.buildList()

    def sortByNameDescending(self):
        self.sortType = self.SORT_NAME_DESCENDING
        self.buildList()

    def sortByDurationAscending(self):
        self.sortType = self.SORT_DURATION_ASCENDING
        self.buildList()

    def sortByDurationDescending(self):
        self.sortType = self.SORT_DURATION_DESCENDING
        self.buildList()


class ZapStatisticCombinedScreen(Screen):
    SORT_NAME_ASCENDING = 0
    SORT_NAME_DESCENDING = 1
    SORT_DURATION_ASCENDING = 2
    SORT_DURATION_DESCENDING = 3
    skin = """
        <screen position="center,center" size="560,450" title="%s" >
            <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
            <widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="list" position="0,40" size="560,400" scrollbarMode="showOnDemand" />
        </screen>""" % _("Zap Statistic")

    def __init__(self, session):
        Screen.__init__(self, session)

        self.combined_entries = []
        self.sortType = self.SORT_DURATION_DESCENDING

        self["key_red"] = Label(_("Sort (name+)"))
        self["key_green"] = Label(_("Sort (name-)"))
        self["key_yellow"] = Label(_("Sort (duration+)"))
        self["key_blue"] = Label(_("Sort (duration-)"))
        self["list"] = ZapStatisticBrowserList([])

        self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
            {
                "ok": self.play,
                "cancel": self.close,
                "red": self.sortByNameAscending,
                "green": self.sortByNameDescending,
                "yellow": self.sortByDurationAscending,
                "blue": self.sortByDurationDescending
            }, prio=-1)

        self.onLayoutFinish.append(self.buildList)

    def sortList(self, entries):
        if self.sortType == self.SORT_NAME_ASCENDING:
            return entries.sort(key=self.buildSortNameKey, reverse=False)
        elif self.sortType == self.SORT_NAME_DESCENDING:
            return entries.sort(key=self.buildSortNameKey, reverse=True)
        elif self.sortType == self.SORT_DURATION_ASCENDING:
            return entries.sort(key=self.buildSortDurationKey, reverse=False)
        elif self.sortType == self.SORT_DURATION_DESCENDING:
            return entries.sort(key=self.buildSortDurationKey, reverse=True)
        return entries

    def buildSortNameKey(self, entry):
        try:
            name = entry.name
        except Exception:
            name = ""
        return name.lower() if name else ""

    def buildSortDurationKey(self, entry):
        try:
            duration = entry.getDurationText()
        except Exception:
            duration = ""
        return duration.lower() if duration else ""

    def buildList(self):
        entries = []
        if len(self.combined_entries) == 0:
            for zap_entry in zapstatistic.zapEntries:
                added = False
                for combined_entry in self.combined_entries:
                    if zap_entry.ref == combined_entry.ref:
                        combined_entry.addDuration(zap_entry)
                        added = True
                        break
                if not added:
                    self.combined_entries.append(CombinedZapEntry(zap_entry))
        self.sortList(self.combined_entries)
        for item in self.combined_entries:
            entries.append(ZapStatisticBrowserCombinedListEntry(item))
        self["list"].setList(entries)

    def play(self):
        cur = self["list"].getCurrent()
        if cur:
            entry = cur[0]
            self.session.nav.playService(eServiceReference(entry.ref))

    def sortByNameAscending(self):
        self.sortType = self.SORT_NAME_ASCENDING
        self.buildList()

    def sortByNameDescending(self):
        self.sortType = self.SORT_NAME_DESCENDING
        self.buildList()

    def sortByDurationAscending(self):
        self.sortType = self.SORT_DURATION_ASCENDING
        self.buildList()

    def sortByDurationDescending(self):
        self.sortType = self.SORT_DURATION_DESCENDING
        self.buildList()


class ZapStatisticScreen(Screen, ProtectedScreen):
    SORT_NAME_ASCENDING = 0
    SORT_NAME_DESCENDING = 1
    SORT_DATE_ASCENDING = 2
    SORT_DATE_DESCENDING = 3
    skin = """
        <screen position="center,center" size="560,450" title="%s" >
            <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
            <widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="list" position="0,40" size="560,400" scrollbarMode="showOnDemand" />
        </screen>""" % _("Zap Statistic")

    def __init__(self, session):
        Screen.__init__(self, session)
        ProtectedScreen.__init__(self)

        self.session = session
        self.sortType = self.SORT_DATE_ASCENDING

        self["key_red"] = Label(_("Delete"))
        self["key_green"] = Label(" ")
        self["key_yellow"] = Label(" ")
        self["key_blue"] = Label(_("Durations"))
        self["list"] = ZapStatisticBrowserList([])

        self["actions"] = ActionMap(["ColorActions", "OkCancelActions", "InfobarMenuActions"],
            {
                "ok": self.play,
                "cancel": self.close,
                "red": self.delete,
                "green": self.sortByName,
                "yellow": self.sortByDate,
                "blue": self.duration,
                "mainMenu": self.menu
            }, prio=-1)

        self.onLayoutFinish.append(self.buildList)

    def updateLabels(self):
        self["key_green"].setText(_("Sort (name+)"))
        self["key_yellow"].setText(_("Sort (date+)"))
        if self.sortType == self.SORT_NAME_ASCENDING:
            self["key_green"].setText(_("Sort (name-)"))
        if self.sortType == self.SORT_DATE_ASCENDING:
            self["key_yellow"].setText(_("Sort (date-)"))

    def sortList(self, entries):
        if self.sortType == self.SORT_NAME_ASCENDING:
            return entries.sort(key=self.buildSortNameKey, reverse=False)
        elif self.sortType == self.SORT_NAME_DESCENDING:
            return entries.sort(key=self.buildSortNameKey, reverse=True)
        elif self.sortType == self.SORT_DATE_ASCENDING:
            return entries.sort(key=self.buildSortDateKey, reverse=False)
        elif self.sortType == self.SORT_DATE_DESCENDING:
            return entries.sort(key=self.buildSortDateKey, reverse=True)
        return entries

    def buildSortNameKey(self, entry):
        try:
            name = entry.name
        except Exception:
            name = ""
        return name.lower() if name else ""

    def buildSortDateKey(self, entry):
        try:
            begin = str(entry.begin)
        except Exception:
            begin = ""
        return begin.lower() if begin else ""

    def buildList(self):
        entries = []
        zap_entries = zapstatistic.zapEntries
        self.sortList(zap_entries)
        for item in zap_entries:
            entries.append(ZapStatisticBrowserListEntry(item))
        self["list"].setList(entries)
        self.updateLabels()

    def isProtected(self):
        return config.ParentalControl.setuppinactive.value

    def pinEntered(self, result):
        if result is None or not result:
            self.close()

    def play(self):
        cur = self["list"].getCurrent()
        if cur:
            entry = cur[0]
            self.session.nav.playService(eServiceReference(entry.ref))

    def delete(self):
        cur = self["list"].getCurrent()
        if cur:
            entry = cur[0]
            idx = 0
            for item in zapstatistic.zapEntries:
                if item == entry:
                    del zapstatistic.zapEntries[idx]
                    break
                idx += 1
            self.buildList()

    def deleteAll(self):
        if len(zapstatistic.zapEntries):
            del zapstatistic.zapEntries
            zapstatistic.zapEntries = []
            self.buildList()

    def sortByName(self):
        if self["key_green"].getText() == _("Sort (name-)"):
            self.sortType = self.SORT_NAME_DESCENDING
        else:
            self.sortType = self.SORT_NAME_ASCENDING
        self.buildList()

    def sortByNameAscending(self):
        self.sortType = self.SORT_NAME_ASCENDING
        self.buildList()

    def sortByNameDescending(self):
        self.sortType = self.SORT_NAME_DESCENDING
        self.buildList()

    def sortByDate(self):
        if self["key_yellow"].getText() == _("Sort (date-)"):
            self.sortType = self.SORT_DATE_DESCENDING
        else:
            self.sortType = self.SORT_DATE_ASCENDING
        self.buildList()

    def sortByDateAscending(self):
        self.sortType = self.SORT_DATE_ASCENDING
        self.buildList()

    def sortByDateDescending(self):
        self.sortType = self.SORT_DATE_DESCENDING
        self.buildList()

    def duration(self):
        self.session.open(ZapStatisticDurationScreen)

    def combined(self):
        self.session.open(ZapStatisticCombinedScreen)

    def menu(self):
        menu_entries = []
        menu_entries.append((_('Play entry'), self.play))
        menu_entries.append((_('Delete entry'), self.delete))
        menu_entries.append((_('Delete all entries'), self.deleteAll))
        menu_entries.append((_('Sort by name (ascending)'), self.sortByNameAscending))
        menu_entries.append((_('Sort by name (descending)'), self.sortByNameDescending))
        menu_entries.append((_('Sort by date (ascending)'), self.sortByDateAscending))
        menu_entries.append((_('Sort by date (descending)'), self.sortByDateDescending))
        menu_entries.append((_('Show duration window'), self.duration))
        menu_entries.append((_('Show combined duration window'), self.combined))
        menu_entries.append((_('Close plugin'), self.close))
        self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("Please choose a function..."), list=menu_entries)

    def menuCallback(self, callback=None):
        if callback is not None:
            callback[1]()


def main(session, **kwargs):
    session.open(ZapStatisticScreen)


def sessionstart(reason, **kwargs):
    if reason == 0:
        zapstatistic.loadZapEntries()
        session = kwargs.get("session")
        if session is None:
            return
        global PlayService
        global StopService
        PlayService = session.nav.playService
        StopService = session.nav.stopService
        session.nav.playService = playService
        session.nav.stopService = stopService


def autostart(reason, **kwargs):
    if reason == 1:
        zapstatistic.saveZapEntries()


def Plugins(**kwargs):
    return [
        PluginDescriptor(name=_("Zap Statistic"), description=_("Shows the watched services with some statistic"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
        PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart),
        PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart),
    ]
