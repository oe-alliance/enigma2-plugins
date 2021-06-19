from __future__ import print_function
import urllib
from twisted.web.client import getPage
from xml.dom.minidom import parseString

from enigma import eTimer, getDesktop, eSize, eRCInput
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.InputBox import InputBox
from Screens.HelpMenu import HelpableScreen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Input import Input
from Components.config import config, ConfigSubList, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText, getConfigListEntry
from Components.ConfigList import ConfigListScreen

from Plugins.Extensions.GoogleMaps.globalmaptiles import GlobalMercator
from Plugins.Extensions.GoogleMaps.KMLlib import RootFolder, KmlFolder, KmlPlace
from Plugins.Extensions.GoogleMaps.WebPixmap import WebPixmap

config.plugins.GoogleMaps = ConfigSubsection()
config.plugins.GoogleMaps.stop_service_on_start = ConfigYesNo(default=False)
config.plugins.GoogleMaps.add_mainmenu_entry = ConfigYesNo(default=False)
config.plugins.GoogleMaps.save_last_position = ConfigYesNo(default=True)
config.plugins.GoogleMaps.load_map_overlay = ConfigYesNo(default=True)
config.plugins.GoogleMaps.cache_enabled = ConfigYesNo(default=False)
config.plugins.GoogleMaps.position = ConfigSubsection()
config.plugins.GoogleMaps.position.x = ConfigInteger(33)
config.plugins.GoogleMaps.position.y = ConfigInteger(21)
config.plugins.GoogleMaps.position.z = ConfigInteger(6)
config.plugins.GoogleMaps.last_searchkey = ConfigText(default="New York")
config.plugins.GoogleMaps.show_preview_on_searchresults = ConfigYesNo(default=True)
config.plugins.GoogleMaps.default_zoomlevel_for_searchresults = ConfigInteger(18, (1, 99)) #zoomlevel previewpic

global plugin_path, not_found_pic, not_found_pic_overlay
plugin_path = ""
not_found_pic = "404.png"
not_found_pic_overlay = "404_transparent.png"


def applySkinVars(skin, dict):
    for key in dict.keys():
        try:
            skin = skin.replace('{' + key + '}', dict[key])
        except Exception, e:
            print(e, "@key=", key)
    return skin


def getURL(x, y, z):
    url = "http://khm0.google.de/kh/v=53&x=%i&y=%i&z=%i" % (x, y, z)
    return url


def getMapURL(x, y, z):
    url = "http://mt3.google.com/vt/v=w2t.97&hl=de&x=%i&y=%i&z=%i&s=G" % (x, y, z)
    return url


def getMaptilesFromLonLat(lon, lat, zoomlevel):
    # calc map tiles
    mercator = GlobalMercator()
    mx, my = mercator.LatLonToMeters(lat, lon)
    tminx, tminy = mercator.MetersToTile(mx, my, zoomlevel)
    gx, gy = mercator.GoogleTile(tminx, tminy, zoomlevel)
    return gx, gy


class GoogleMapsConfigScreen(ConfigListScreen, Screen):
    skin = """
        <screen position="100,100" size="550,400" title="Google Maps Setup" >
        <widget name="config" position="0,0" size="550,360" scrollbarMode="showOnDemand" />
        <widget name="key_red" position="10,360" size="100,40" backgroundColor="red" valign="center" halign="center" zPosition="1"  foregroundColor="white" font="Regular;18"/>
        <widget name="key_green" position="120,360" size="100,40" backgroundColor="green" valign="center" halign="center" zPosition="1"  foregroundColor="white" font="Regular;18"/>
        <widget name="label" position="240,360" size="200,40"  valign="center" halign="center" zPosition="1"  foregroundColor="white" font="Regular;18"/>
        </screen>"""

    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self.list = []
        self.list.append(getConfigListEntry(_("add Entry to Main Menu"), config.plugins.GoogleMaps.add_mainmenu_entry))
        self.list.append(getConfigListEntry(_("stop TV Service on Start"), config.plugins.GoogleMaps.stop_service_on_start))
        self.list.append(getConfigListEntry(_("save last Map Position"), config.plugins.GoogleMaps.save_last_position))
        self.list.append(getConfigListEntry(_("load Map Overlay"), config.plugins.GoogleMaps.load_map_overlay))
        self.list.append(getConfigListEntry(_("enable caching of Images in /tmp/"), config.plugins.GoogleMaps.cache_enabled))
        self.list.append(getConfigListEntry(_("show Preview Image for Searchresults"), config.plugins.GoogleMaps.show_preview_on_searchresults))
        self.list.append(getConfigListEntry(_("default Zoomlevel for Preview Images"), config.plugins.GoogleMaps.default_zoomlevel_for_searchresults))
        self.setTitle(_("Google Maps Setup"))
        ConfigListScreen.__init__(self, self.list)
        self["key_red"] = Label(_("cancel"))
        self["key_green"] = Label(_("ok"))
        self["label"] = Label("Author: 3c5x9")
        self["setupActions"] = ActionMap(["SetupActions"],
        {
            "green": self.save,
            "red": self.cancel,
            "save": self.save,
            "cancel": self.cancel,
            "ok": self.save,
        }, -2)

    def save(self):
        print("saving")
        for x in self["config"].list:
            x[1].save()
        self.close(True)

    def cancel(self):
        print("cancel")
        for x in self["config"].list:
            x[1].cancel()
        self.close(False)


class GoogleMapsMainScreen(Screen, HelpableScreen):
    raw_skin = """
            <screen position="{screen.position}" size="{screen.size}" title="GoogleMaps" flags="wfNoBorder">
    <!-- widget  name="pic1b" position="{pixmap1.pos}" size="{pixmap.size}" zPosition="0" alphatest="blend"//-->
    <widget  name="pic1" position="{pixmap1.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic1o" position="{pixmap1.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic2" position="{pixmap2.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic2o" position="{pixmap2.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic3" position="{pixmap3.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic3o" position="{pixmap3.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic4" position="{pixmap4.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic4o" position="{pixmap4.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic5" position="{pixmap5.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic5o" position="{pixmap5.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic6" position="{pixmap6.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic6o" position="{pixmap6.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic7" position="{pixmap7.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic7o" position="{pixmap7.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic8" position="{pixmap8.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic8o" position="{pixmap8.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic9" position="{pixmap9.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic9o" position="{pixmap9.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>

    <!-- widget name="infopanel" position="{infopanel.pos}" size="{infopanel.size}" zPosition="0"  backgroundColor="blue" //-->
    <widget name="posx" position="{posx.pos}" size="{posx.size}" font="{font}" zPosition="1" />
    <widget name="posy" position="{posy.pos}" size="{posy.size}" font="{font}" zPosition="1" />
    <widget name="posz" position="{posz.pos}" size="{posz.size}" font="{font}" zPosition="1" />
    <widget name="placeslist" position="{placeslist.pos}" size="{placeslist.size}" zPosition="1"/>
    <widget name="buttonmenu" position="{buttonmenu.pos}" size="{buttonmenu.size}" font="{font}" halign="center" valign="center"  zPosition="1"/>
    <widget name="buttonsearch" position="{buttonsearch.pos}" size="{buttonsearch.size}" font="{font}" halign="center" valign="center"  zPosition="1"  backgroundColor="red"/>
    <widget name="buttonhelp" position="{buttonhelp.pos}" size="{buttonhelp.size}" font="{font}" halign="center" valign="center"  zPosition="1"/>

            </screen>
            """

    def __init__(self, session):
        self.session = session
        size_w = int(getDesktop(0).size().width() * 0.9)
        size_h = int(getDesktop(0).size().height() * 0.9)
        pos_w = int((getDesktop(0).size().width() - size_w) / 2)
        pos_h = int((getDesktop(0).size().height() - size_h) / 2)
        p_h = int(size_h / 3)

        infopanel_width = int(size_w - (p_h * 3))
        infopanel_height = size_h
        label_height = 30
        font = "Regular;21"
        self.dict = {

                'font': font,

                'screen.size': "%i,%i" % (size_w, size_h),
                'screen.position': "%i,%i" % (pos_w, pos_h),
                'pixmap.size': '%i,%i' % (p_h, p_h),

                'pixmap1.pos': '0,0',
                'pixmap2.pos': '%i,0' % (p_h),
                'pixmap3.pos': '%i,0' % (int(p_h * 2)),

                'pixmap4.pos': '0,%i' % (p_h),
                'pixmap5.pos': '%i,%i' % (p_h, p_h),
                'pixmap6.pos': '%i,%i' % (int(p_h * 2), p_h),

                'pixmap7.pos': '0,%i' % (int(p_h * 2)),
                'pixmap8.pos': '%i,%i' % (p_h, int(p_h * 2)),
                'pixmap9.pos': '%i,%i' % (int(p_h * 2), int(p_h * 2)),

                'infopanel.pos': '%i,0' % (int(p_h * 3)),
                'infopanel.size': '%i,%i' % (infopanel_width, infopanel_height),

                'posx.pos': '%i,0' % (int(p_h * 3)),
                'posx.size': '%i,%i' % (infopanel_width, label_height),

                'posy.pos': '%i,%i' % (int(p_h * 3), label_height),
                'posy.size': '%i,%i' % (infopanel_width, label_height),

                'posz.pos': '%i,%i' % (int(p_h * 3), int(label_height * 2)),
                'posz.size': '%i,%i' % (infopanel_width, label_height),

                'placeslist.pos': '%i,%i' % (int(p_h * 3), int(label_height * 3)),
                'placeslist.size': '%i,%i' % (infopanel_width, int(infopanel_height - (label_height * 4))),

                'buttonmenu.pos': '%i,%i' % (int(p_h * 3), int(infopanel_height - (label_height * 4) + (label_height * 3))),
                'buttonmenu.size': '%i,%i' % (int(infopanel_width / 3), label_height),

                'buttonsearch.pos': '%i,%i' % (int(p_h * 3 + (infopanel_width / 3)), int(infopanel_height - (label_height * 4) + (label_height * 3))),
                'buttonsearch.size': '%i,%i' % (int(infopanel_width / 3), label_height),

                'buttonhelp.pos': '%i,%i' % (int(p_h * 3 + ((infopanel_width / 3) * 2)), int(infopanel_height - (label_height * 4) + (label_height * 3))),
                'buttonhelp.size': '%i,%i' % (int(infopanel_width / 3), label_height),

                }

        self.skin = applySkinVars(GoogleMapsMainScreen.raw_skin, self.dict)
        Screen.__init__(self, session)
        HelpableScreen.__init__(self)

        #self["infopanel"] = Label()
        self["posx"] = Label("")
        self["posy"] = Label("")
        self["posz"] = Label("")
        self["placeslist"] = MenuList([])
        self["buttonmenu"] = Label(_("Menu"))
        self["buttonsearch"] = Label(_("Search"))
        self["buttonhelp"] = Label(_("Help"))

        #self["pic1b"] = WebPixmap(default=plugin_path+not_found_pic)
        self["pic1"] = WebPixmap(default=plugin_path + not_found_pic)
        self["pic2"] = WebPixmap(default=plugin_path + not_found_pic)
        self["pic3"] = WebPixmap(default=plugin_path + not_found_pic)
        self["pic4"] = WebPixmap(default=plugin_path + not_found_pic)
        self["pic5"] = WebPixmap(default=plugin_path + not_found_pic)
        self["pic6"] = WebPixmap(default=plugin_path + not_found_pic)
        self["pic7"] = WebPixmap(default=plugin_path + not_found_pic)
        self["pic8"] = WebPixmap(default=plugin_path + not_found_pic)
        self["pic9"] = WebPixmap(default=plugin_path + not_found_pic)

        self["pic1o"] = WebPixmap(default=plugin_path + not_found_pic_overlay)
        self["pic2o"] = WebPixmap(default=plugin_path + not_found_pic_overlay)
        self["pic3o"] = WebPixmap(default=plugin_path + not_found_pic_overlay)
        self["pic4o"] = WebPixmap(default=plugin_path + not_found_pic_overlay)
        self["pic5o"] = WebPixmap(default=plugin_path + not_found_pic_overlay)
        self["pic6o"] = WebPixmap(default=plugin_path + not_found_pic_overlay)
        self["pic7o"] = WebPixmap(default=plugin_path + not_found_pic_overlay)
        self["pic8o"] = WebPixmap(default=plugin_path + not_found_pic_overlay)
        self["pic9o"] = WebPixmap(default=plugin_path + not_found_pic_overlay)

        self["actionmap"] = ActionMap(["OkCancelActions", "NumberActions", "DirectionActions", "MenuActions", "ColorActions", "InfobarChannelSelection"],
            {
             "cancel": self.close,
             "ok": self.keyOk,
             "1": self.key1,
             "2": self.key2,
             "3": self.key3,
             "4": self.key4,
             "5": self.key5,
             "6": self.key6,
             "7": self.key7,
             "8": self.key8,
             "9": self.key9,
             "0": self.key0,
             "red": self.openSearchScreen,
             "menu": self.keymenu,
             "historyNext": self.toggleMapOverlay,

             }, -1)

        self.helpList.append((self["actionmap"], "OkCancelActions", [("cancel", _("quit Google Maps"))]))
        self.helpList.append((self["actionmap"], "DirectionActions", [("up", _("navigate thru Placemarks"))]))
        self.helpList.append((self["actionmap"], "DirectionActions", [("down", _("navigate thru Placemarks"))]))
        self.helpList.append((self["actionmap"], "DirectionActions", [("left", _("navigate thru Placemarks"))]))
        self.helpList.append((self["actionmap"], "DirectionActions", [("right", _("navigate thru Placemarks"))]))
        self.helpList.append((self["actionmap"], "OkCancelActions", [("ok", _("show selected Placemark"))]))
        self.helpList.append((self["actionmap"], "NumberActions", [("1", 'move north-west')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("2", 'move north')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("3", 'move north-east')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("4", 'move west')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("6", 'move east')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("7", 'move south-west')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("8", 'move south')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("9", 'move south-east')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("5", 'zoom in')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("0", 'zoom out')]))
        self.helpList.append((self["actionmap"], "ColorActions", [("red", 'open Search Screen')]))
        self.helpList.append((self["actionmap"], "InfobarChannelSelection", [("historyNext", 'show/unshow Map Overlay')]))

        self.onLayoutFinish.append(self.onLayoutFinished)

    def getRandomNumber(self):
        """ returning a real random number """
        return 4 # fairly choosen by using a dice

    def openSearchScreen(self):
        self.session.openWithCallback(self.searchCB, GoogleMapsGeoSearchScreen)

    def searchCB(self, result, adress, x, y, zoomlevel):
        if result:
            self.setNewXYZ(x, y, zoomlevel)

    def buildMenuRoot(self):
        list = []
        root = RootFolder()
        for i in root.getFiles(plugin_path):
            l = lambda name, filepath: self.openFolderRoot(name, filepath)
            list.append((i[0], i[1], l))
        self["placeslist"].setList(list)

    def openFolderRoot(self, name, filepath):
        print("openFolderRoot", name, filepath)
        root = RootFolder()
        folderx = root.getFolderFromFile(filepath)
        list = []
        l = lambda name, filepath: self.buildMenuRoot()
        list.append(("..", filepath, l))
        for folderx in folderx.getFolders():
            l = lambda name, folder: self.openFolder(name, folder)
            list.append(("+ " + folderx.name, folderx, l))

        for placex in folderx.getPlacemarks():
            l = lambda name, place: self.showPlace(name, place)
            list.append(("" + placex.name, placex, l))

        self["placeslist"].setList(list)

    def openFolder(self, name, foldery):
        print("open Folder", name, foldery)
        list = []
        if foldery.parent is None:
            l = lambda name, folder: self.buildMenuRoot()
            list.append(("..", None, l))
        else:
            l = lambda name, folder: self.openFolder(name, folder)
            list.append(("..", foldery.parent, l))

        for folderx in foldery.getFolders():
            l = lambda name, folder: self.openFolder(name, folder)
            list.append(("+ " + folderx.name, folderx, l))

        for placex in foldery.getPlacemarks():
            l = lambda name, place: self.showPlace(name, place)
            list.append(("" + placex.name, placex, l))

        self["placeslist"].setList(list)

    def showPlace(self, name, place):
        #print "show Place",name,place
        x, y, z = place.getTile(self.z)
        self.setNewXYZ(x, y, z)

    def onLayoutFinished(self):
        self.buildMenuRoot()
        self.setNewXYZ(config.plugins.GoogleMaps.position.x.value,
                       config.plugins.GoogleMaps.position.y.value,
                       config.plugins.GoogleMaps.position.z.value)

    #################
    def toggleMapOverlay(self):
        if config.plugins.GoogleMaps.load_map_overlay.value is True:
            config.plugins.GoogleMaps.load_map_overlay.value = False
        else:
            config.plugins.GoogleMaps.load_map_overlay.value = True
        self.setNewXYZ(config.plugins.GoogleMaps.position.x.value,
                       config.plugins.GoogleMaps.position.y.value,
                       config.plugins.GoogleMaps.position.z.value)

    def keymenu(self):
        self.session.openWithCallback(self.menuCB, GoogleMapsConfigScreen)

    def menuCB(self, dummy):
        self.setNewXYZ(config.plugins.GoogleMaps.position.x.value,
                       config.plugins.GoogleMaps.position.y.value,
                       config.plugins.GoogleMaps.position.z.value)

    def keyOk(self):
        listentry = self["placeslist"].getCurrent()
        if listentry is not None:
            if listentry[1] is not None:
                listentry[2](listentry[0], listentry[1])

    def key1(self):
        # northwest
        self.setNewXYZ(self.x - 1, self.y - 1, self.z)

    def key3(self):
        # northeast
        self.setNewXYZ(self.x + 1, self.y - 1, self.z)

    def key7(self):
        # southwest
        self.setNewXYZ(self.x - 1, self.y + 1, self.z)

    def key9(self):
        # southeast
        self.setNewXYZ(self.x + 1, self.y + 1, self.z)

    #################
    def key2(self):
        # north
        self.setNewXYZ(self.x, self.y - 1, self.z)

    def key8(self):
        # south
        self.setNewXYZ(self.x, self.y + 1, self.z)

    def key4(self):
        # west
        self.setNewXYZ(self.x - 1, self.y, self.z)

    def key6(self):
        # east
        self.setNewXYZ(self.x + 1, self.y, self.z)

    #################
    def key5(self):
        #zoom in
        self.setNewXYZ(self.x * 2, self.y * 2 + 1, self.z + 1)

    def key0(self):
        #zoom out
        self.setNewXYZ(self.x / 2, self.y / 2, self.z - 1)

    #################
    def setNewXYZ(self, x, y, z):
        print(x, y, z)
        if z < 0 or z >= 30:
            return
        self.x = x
        self.y = y
        self.z = z
        if config.plugins.GoogleMaps.save_last_position.value:
            config.plugins.GoogleMaps.position.x.value = x
            config.plugins.GoogleMaps.position.y.value = y
            config.plugins.GoogleMaps.position.z.value = z

        self["posx"].setText(_('Pos.') + " X: " + str(x))
        self["posy"].setText(_('Pos.') + " Y: " + str(y))
        self["posz"].setText(_('Zoom') + " : " + str(z))

        self["pic1"].load(getURL(x - 1, y - 1, z))
        self["pic2"].load(getURL(x, y - 1, z))
        self["pic3"].load(getURL(x + 1, y - 1, z))
        self["pic4"].load(getURL(x - 1, y, z))
        self["pic5"].load(getURL(x, y, z))
        self["pic6"].load(getURL(x + 1, y, z))
        self["pic7"].load(getURL(x - 1, y + 1, z))
        self["pic8"].load(getURL(x, y + 1, z))
        self["pic9"].load(getURL(x + 1, y + 1, z))

        if config.plugins.GoogleMaps.load_map_overlay.value:
            self["pic1o"].show()
            self["pic2o"].show()
            self["pic3o"].show()
            self["pic4o"].show()
            self["pic5o"].show()
            self["pic6o"].show()
            self["pic7o"].show()
            self["pic8o"].show()
            self["pic9o"].show()
            self["pic1o"].load(getMapURL(x - 1, y - 1, z))
            self["pic2o"].load(getMapURL(x, y - 1, z))
            self["pic3o"].load(getMapURL(x + 1, y - 1, z))
            self["pic4o"].load(getMapURL(x - 1, y, z))
            self["pic5o"].load(getMapURL(x, y, z))
            self["pic6o"].load(getMapURL(x + 1, y, z))
            self["pic7o"].load(getMapURL(x - 1, y + 1, z))
            self["pic8o"].load(getMapURL(x, y + 1, z))
            self["pic9o"].load(getMapURL(x + 1, y + 1, z))
        else:
            self["pic1o"].hide()
            self["pic2o"].hide()
            self["pic3o"].hide()
            self["pic4o"].hide()
            self["pic5o"].hide()
            self["pic6o"].hide()
            self["pic7o"].hide()
            self["pic8o"].hide()
            self["pic9o"].hide()


##################################

class GoogleMapsGeoSearchScreen(InputBox):
    raw_skin = """
            <screen position="{screen.position}" size="{screen.size}" title="GoogleMaps Search" flags="wfNoBorder">
                <widget name="text" position="{text.position}" size="{text.size}" font="Regular;23"/>
                <widget name="input" position="{input.position}" size="{input.size}" font="Regular;23"/>
                <widget name="list" position="{list.position}" size="{list.size}" />
                <widget name="infotext" position="{infotext.position}" size="{infotext.size}"   font="Regular;20"/>

                <widget name="preview" position="{preview.position}" size="{preview.size}"  zPosition="1" alphatest="blend"/>
                <widget name="previewo" position="{preview.position}" size="{preview.size}"  zPosition="2" alphatest="blend"/>
            </screen>
            """

    def __init__(self, session):
        self.session = session
        screen_size_w = int(getDesktop(0).size().width() * 0.9)
        screen_size_h = int(getDesktop(0).size().height() * 0.9)
        screen_pos_w = int((getDesktop(0).size().width() - screen_size_w) / 2)
        screen_pos_h = int((getDesktop(0).size().height() - screen_size_h) / 2)

        label_height = 30
        offset = 5

        list_h = int(screen_size_h - (label_height * 3) - (offset * 5))
        list_w = int((screen_size_w / 2) - offset)
        list_pos_x = offset
        list_pos_y = int((offset * 3) + (label_height * 2))

        font = "Regular;21"
        skindict = {

                'font': font,

                'screen.size': "%i,%i" % (screen_size_w, screen_size_h),
                'screen.position': "%i,%i" % (screen_pos_w, screen_pos_h),

                'text.position': "%i,%i" % (offset, offset),
                'text.size': "%i,%i" % (list_w - offset, label_height),

                'input.position': "%i,%i" % (offset, (offset * 2) + label_height),
                'input.size': "%i,%i" % (list_w - offset, label_height),

                'list.position': "%i,%i" % (list_pos_x, list_pos_y),
                'list.size': "%i,%i" % (list_w - offset, list_h),

                "infotext.position": "%i,%i" % (offset, list_pos_y + list_h + offset),
                "infotext.size": "%i,%i" % (int(screen_size_w - (offset * 2)), label_height),

                'preview.position': "%i,%i" % (offset + list_w, offset),
                'preview.size': "%i,%i" % (list_w - offset, screen_size_h - (offset * 3) - label_height),

                }

        self.skin = applySkinVars(GoogleMapsGeoSearchScreen.raw_skin, skindict)

        self["list"] = MenuList([])
        self["list"].onSelectionChanged.append(self.onListSelectionChanged)
        self["preview"] = WebPixmap(default=plugin_path + not_found_pic)
        self["previewo"] = WebPixmap(default=plugin_path + not_found_pic_overlay)
        self["infotext"] = Label("")

        InputBox.__init__(self, session, title="Please enter a City or Locationname:", windowTitle=_("GoogleMaps Search"), text=config.plugins.GoogleMaps.last_searchkey.value)
        self.onLayoutFinish.append(self.onLayoutFinished)

        self.do_preview_timer = eTimer()
        self.do_search_timer = eTimer()

    def onLayoutFinished(self):
        self.doSearch(self["input"].getText())

    def onListSelectionChanged(self):
        listitem = self["list"].getCurrent()
        self.do_preview_timer.stop()
        if listitem:
            #print "list changed",listitem
            adress, lon, lat = listitem[1]
            for i in self.do_preview_timer.timeout.get():
                self.do_preview_timer.timeout.get().remove(i)
            self.do_preview_timer.timeout.get().append(lambda: self.loadPreview(lon, lat))
            self.do_preview_timer.start(1500)
        else:
            pass #print "nothing selected"

    def loadPreview(self, lon, lat):
        self.do_preview_timer.stop()
        if config.plugins.GoogleMaps.show_preview_on_searchresults.value:
            zoomlevel = config.plugins.GoogleMaps.default_zoomlevel_for_searchresults.value
            gx, gy = getMaptilesFromLonLat(lon, lat, zoomlevel)
            self["preview"].load(getURL(gx, gy, zoomlevel))
            self["previewo"].load(getMapURL(gx, gy, zoomlevel))

    def keyNumberGlobal(self, number):
        self["input"].number(number)
        self.do_search_timer.stop()
        for i in self.do_search_timer.timeout.get():
            self.do_search_timer.timeout.get().remove(i)
        self.do_search_timer.timeout.get().append(lambda: self.doSearch(self["input"].getText()))
        self.do_search_timer.start(1000)

        #self.doSearch(self["input"].getText())

    def go(self):
        # overwritten from InputBox
        listitem = self["list"].getCurrent()
        if listitem:
            adress, lon, lat = listitem[1]
            zoomlevel = config.plugins.GoogleMaps.default_zoomlevel_for_searchresults.value
            gx, gy = getMaptilesFromLonLat(lon, lat, zoomlevel)
            self.close(True, adress, gx, gy, zoomlevel)

    def cancel(self):
        # overwritten from InputBox
        rcinput = eRCInput.getInstance()
        rcinput.setKeyboardMode(rcinput.kmNone)
        self.do_preview_timer.stop()
        self.do_search_timer.stop()
        self.close(False, False, False, False, False)

    def doSearch(self, searchkey):
        self.do_search_timer.stop()
        config.plugins.GoogleMaps.last_searchkey.value = searchkey
        self["infotext"].setText("searching with '%s' ..." % (searchkey))
        s = urllib.quote(searchkey)
        url = "http://maps.google.com/maps/geo?q=%s&output=xml&key=abcdefg&oe=utf8" % s
        cb = lambda result: self.onLoadFinished(searchkey, result)
        getPage(url).addCallback(cb).addErrback(self.onLoadFailed)

    def onLoadFinished(self, searchkey, result):
        xmldoc = parseString(result)
        list = []
        for i in xmldoc.getElementsByTagName('Placemark'):
            adress = i.getElementsByTagName('address')[0].firstChild.data.encode('utf-8')
            lon, lat, unknown = i.getElementsByTagName('coordinates')[0].firstChild.data.encode("utf-8").split(",")
            list.append((adress, [adress, float(lon), float(lat)]))

        self["list"].setList(list)

        if len(list):
            self["infotext"].setText("found %i Locations with '%s'" % (len(list), searchkey))
        else:
            self["infotext"].setText("nothing found with '%s'" % (searchkey))

    def onLoadFailed(self, reason):
        print(reason)
        self["infotext"].setText(str(reason))

##################################


def start_from_mainmenu(menuid, **kwargs):
    #starting from main menu
    if menuid == "mainmenu":
        return [(_("Google Maps"), start_from_pluginmenu, "googlemaps", 46)]
    return []


originalservice = None
mysession = None


def start_from_pluginmenu(session, **kwargs):
    global originalservice, mysession
    mysession = session
    originalservice = session.nav.getCurrentlyPlayingServiceReference()
    if config.plugins.GoogleMaps.stop_service_on_start.value:
        session.nav.stopService()
    session.openWithCallback(mainCB, GoogleMapsMainScreen)


def mainCB():
    global originalservice, mysession
    mysession.nav.playService(originalservice)
    config.plugins.GoogleMaps.position.x.save()
    config.plugins.GoogleMaps.position.y.save()
    config.plugins.GoogleMaps.position.z.save()


def Plugins(path, **kwargs):
    global plugin_path
    plugin_path = path + "/"
    pname = "Google Maps"
    pdesc = "browse google maps"
    desc_mainmenu = PluginDescriptor(name=pname, description=pdesc, where=PluginDescriptor.WHERE_MENU, fnc=start_from_mainmenu)
    desc_pluginmenu = PluginDescriptor(name=pname, description=pdesc, where=PluginDescriptor.WHERE_PLUGINMENU, fnc=start_from_pluginmenu, icon="plugin.png")
    list = []
    list.append(desc_pluginmenu)
    if config.plugins.GoogleMaps.add_mainmenu_entry.value:
        list.append(desc_mainmenu)
    return list
