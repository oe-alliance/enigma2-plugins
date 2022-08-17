from __future__ import print_function
from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigText
from Components.FileList import FileList
from Components.Sources.StaticText import StaticText
from Screens.Console import Console
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Screens.Screen import Screen
from Screens.Setup import Setup
from Components.ActionMap import HelpableActionMap
from Components.Scanner import openFile
from os.path import isdir as os_path_isdir
from mimetypes import guess_type
from . import _

##################################
pname = _("Filebrowser")
pdesc = _("manage local Files")

config.plugins.filebrowser = ConfigSubsection()
config.plugins.filebrowser.savedirs = ConfigYesNo(default=True)
config.plugins.filebrowser.add_mainmenu_entry = ConfigYesNo(default=True)
config.plugins.filebrowser.add_extensionmenu_entry = ConfigYesNo(default=True)
config.plugins.filebrowser.path_left = ConfigText(default="/")
config.plugins.filebrowser.path_right = ConfigText(default="/")


##################################
class FilebrowserConfigScreen(Setup):
    def __init__(self, session):
        Setup.__init__(self, session, "filebrowser", plugin="Extensions/Filebrowser", PluginLanguageDomain="Filebrowser")


##################################
class FilebrowserScreen(Screen, HelpableScreen):
    skin = """
        <screen position="110,83" size="530,430" title="">
            <widget name="list_left" position="0,0" size="265,380" scrollbarMode="showOnDemand" />
            <widget name="list_right" position="265,0" size="265,380" scrollbarMode="showOnDemand" />

            <widget name="red" position="10,390" size="120,30" valign="center" halign="center" zPosition="1" transparent="1" foregroundColor="white" font="Regular;18"/>
            <widget name="green" position="140,390" size="120,30" valign="center" halign="center" zPosition="1" transparent="1" foregroundColor="white" font="Regular;18"/>
            <widget name="yellow" position="270,390" size="120,30" valign="center" halign="center" zPosition="1" transparent="1" foregroundColor="white" font="Regular;18"/>
            <widget name="blue" position="400,390" size="120,30" valign="center" halign="center" zPosition="1" transparent="1" foregroundColor="white" font="Regular;18"/>

            <ePixmap name="pred" position="10,390" size="120,30" zPosition="0" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
            <ePixmap name="pgreen" position="140,390" size="120,30" zPosition="0" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
            <ePixmap name="pyellow" position="270,390" size="120,30" zPosition="0" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
            <ePixmap name="pblue" position="400,390" size="120,30" zPosition="0" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
        </screen>
        """

    def __init__(self, session, path_left=None):
        if path_left is None:
            if os_path_isdir(config.plugins.filebrowser.path_left.value) and config.plugins.filebrowser.savedirs.value:
                path_left = config.plugins.filebrowser.path_left.value
            else:
                path_left = "/"

        if os_path_isdir(config.plugins.filebrowser.path_right.value) and config.plugins.filebrowser.savedirs.value:
            path_right = config.plugins.filebrowser.path_right.value
        else:
            path_right = "/"

        self.session = session
        Screen.__init__(self, session)
        HelpableScreen.__init__(self)

        self["list_left"] = FileList(path_left, matchingPattern="^.*")
        self["list_right"] = FileList(path_right, matchingPattern="^.*")
        self["key_red"] = self["red"] = Label(_("Delete"))
        self["key_green"] = self["green"] = Label(_("Move"))
        self["key_yellow"] = self["yellow"] = Label(_("Copy"))
        self["key_blue"] = self["blue"] = Label(_("Rename"))
        self["key_menu"] = StaticText(_("MENU"))
        self["key_help"] = StaticText(_("HELP"))

        self["actions"] = HelpableActionMap(self, ["WizardActions", "DirectionActions", "MenuActions", "NumberActions", "ColorActions"],
            {
             "ok": (self.ok, "Select item"),
             "back": (self.exit, "Exit"),
             "menu": (self.goMenu, "Open setup options"),
             "shiftDown": (self.listRight, "Select right list"),
             "shiftUp": (self.listLeft, "Select left list"),
             "up": (self.goUp, "Navigate up"),
             "down": (self.goDown, "Navigate down"),
             "left": (self.goLeft, "Page up"),
             "right": (self.goRight, "Page down"),
             "red": (self.goRed, "Delete"),
             "green": (self.goGreen, "Move"),
             "yellow": (self.goYellow, "Copy"),
             "blue": (self.goBlue, "Rename"),
             "0": (self.doRefresh, "Refresh"),
             }, prio=-1, description=_("filebrowser buttons"))
        self.onLayoutFinish.append(self.listLeft)

    def exit(self):
        if self["list_left"].getCurrentDirectory() and config.plugins.filebrowser.savedirs.value:
            config.plugins.filebrowser.path_left.value = self["list_left"].getCurrentDirectory()
            config.plugins.filebrowser.path_left.save()

        if self["list_right"].getCurrentDirectory() and config.plugins.filebrowser.savedirs.value:
            config.plugins.filebrowser.path_right.value = self["list_right"].getCurrentDirectory()
            config.plugins.filebrowser.path_right.save()

        self.close()

    def ok(self):
        if self.SOURCELIST.canDescent():  # isDir
            self.SOURCELIST.descent()
            if self.SOURCELIST.getCurrentDirectory():  # ??? when is it none
                self.setTitle(self.SOURCELIST.getCurrentDirectory())
        else:
            self.onFileAction()

    def goMenu(self):
        self.session.open(FilebrowserConfigScreen)

    def goLeft(self):
        self.SOURCELIST.pageUp()

    def goRight(self):
        self.SOURCELIST.pageDown()

    def goUp(self):
        self.SOURCELIST.up()

    def goDown(self):
        self.SOURCELIST.down()

    # copy ###################
    def goYellow(self):
        filename = self.SOURCELIST.getFilename()
        sourceDir = self.SOURCELIST.getCurrentDirectory()
        targetDir = self.TARGETLIST.getCurrentDirectory()
        self.session.openWithCallback(self.doCopy, ChoiceBox, title=_("copy file") + "?\n%s\nfrom\n%s\n%s" % (filename, sourceDir, targetDir), list=[(_("yes"), True), (_("no"), False)])

    def doCopy(self, result):
        if result is not None:
            if result[1]:
                filename = self.SOURCELIST.getFilename()
                sourceDir = self.SOURCELIST.getCurrentDirectory()
                targetDir = self.TARGETLIST.getCurrentDirectory()
                self.session.openWithCallback(self.doCopyCB, Console, title=_("copying file ..."), cmdlist=["cp \"" + sourceDir + filename + "\" \"" + targetDir + "\""])

    def doCopyCB(self):
        self.doRefresh()

    # delete ###################
    def goRed(self):
        filename = self.SOURCELIST.getFilename()
        sourceDir = self.SOURCELIST.getCurrentDirectory()
        self.session.openWithCallback(self.doDelete, ChoiceBox, title=_("delete file") + "?\n%s\nfrom dir\n%s" % (filename, sourceDir), list=[(_("yes"), True), (_("no"), False)])

    def doDelete(self, result):
        if result is not None:
            if result[1]:
                filename = self.SOURCELIST.getFilename()
                sourceDir = self.SOURCELIST.getCurrentDirectory()
                self.session.openWithCallback(self.doDeleteCB, Console, title=_("deleting file ..."), cmdlist=["rm \"" + sourceDir + filename + "\""])

    def doDeleteCB(self):
        self.doRefresh()

    # move ###################
    def goGreen(self):
        filename = self.SOURCELIST.getFilename()
        sourceDir = self.SOURCELIST.getCurrentDirectory()
        targetDir = self.TARGETLIST.getCurrentDirectory()
        self.session.openWithCallback(self.doMove, ChoiceBox, title=_("move file") + "?\n%s\nfrom dir\n%s\nto dir\n%s" % (filename, sourceDir, targetDir), list=[(_("yes"), True), (_("no"), False)])

    def doMove(self, result):
        if result is not None:
            if result[1]:
                filename = self.SOURCELIST.getFilename()
                sourceDir = self.SOURCELIST.getCurrentDirectory()
                targetDir = self.TARGETLIST.getCurrentDirectory()
                self.session.openWithCallback(self.doMoveCB, Console, title=_("moving file ..."), cmdlist=["mv \"" + sourceDir + filename + "\" \"" + targetDir + "\""])

    def doMoveCB(self):
        self.doRefresh()

    # move ###################
    def goBlue(self):
        filename = self.SOURCELIST.getFilename()
        sourceDir = self.SOURCELIST.getCurrentDirectory()
        self.session.openWithCallback(self.doRename, InputBox, text=filename, title=filename, windowTitle=_("rename file"))

    def doRename(self, newname):
        if newname:
            filename = self.SOURCELIST.getFilename()
            sourceDir = self.SOURCELIST.getCurrentDirectory()
            self.session.openWithCallback(self.doRenameCB, Console, title=_("renaming file ..."), cmdlist=["mv \"" + sourceDir + filename + "\" \"" + sourceDir + newname + "\""])

    def doRenameCB(self):
        self.doRefresh()

    #############
    def doRefresh(self):
        self.SOURCELIST.refresh()
        self.TARGETLIST.refresh()

    def listRight(self):
        self["list_left"].selectionEnabled(0)
        self["list_right"].selectionEnabled(1)
        self.SOURCELIST = self["list_right"]
        self.TARGETLIST = self["list_left"]
        self.setTitle(self.SOURCELIST.getCurrentDirectory())

    def listLeft(self):
        self["list_left"].selectionEnabled(1)
        self["list_right"].selectionEnabled(0)
        self.SOURCELIST = self["list_left"]
        self.TARGETLIST = self["list_right"]
        self.setTitle(self.SOURCELIST.getCurrentDirectory())

    def onFileAction(self):
        try:
            x = openFile(self.session, guess_type(self.SOURCELIST.getFilename())[0], self.SOURCELIST.getCurrentDirectory() + self.SOURCELIST.getFilename())
            print("RESULT OPEN FILE", x)
        except TypeError as e:
            # catching error
            #  File "/home/tmbinc/opendreambox/1.5/dm8000/experimental/build/tmp/work/enigma2-2.6git20090627-r1/image/usr/lib/enigma2/python/Components/Scanner.py", line 43, in handleFile
            #  TypeError: 'in <string>' requires string as left operand
            self.session.open(MessageBox, _("no Viewer installed for this mimetype!"), type=MessageBox.TYPE_ERROR, timeout=5, close_on_any_key=True)


##################################

def filescan_open(list, session, **kwargs):
    path = "/".join(list[0].path.split("/")[:-1]) + "/"
    session.open(FilebrowserScreen, path_left=path)


def start_from_filescan(**kwargs):
    from Components.Scanner import Scanner, ScanPath
    return \
        Scanner(mimetypes=None,
            paths_to_scan=[
                    ScanPath(path="", with_subdirs=False),
                ],
            name=pname,
            description=pdesc,
            openfnc=filescan_open,
        )


def start_from_mainmenu(menuid, **kwargs):
    #starting from main menu
    if config.plugins.filebrowser.add_mainmenu_entry.value and menuid == "mainmenu":
        return [(pname, start_from_pluginmenu, "filecommand", 46)]
    return []


def start_from_pluginmenu(session, **kwargs):
    session.open(FilebrowserScreen)


def Plugins(path, **kwargs):
    desc_mainmenu = PluginDescriptor(name=pname, description=pdesc, where=PluginDescriptor.WHERE_MENU, fnc=start_from_mainmenu)
    desc_pluginmenu = PluginDescriptor(name=pname, description=pdesc, where=PluginDescriptor.WHERE_PLUGINMENU, fnc=start_from_pluginmenu)
    desc_extensionmenu = PluginDescriptor(name=pname, description=pdesc, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=start_from_pluginmenu)
    desc_filescan = PluginDescriptor(name=pname, where=PluginDescriptor.WHERE_FILESCAN, fnc=start_from_filescan)
    list = []
    list.append(desc_pluginmenu)
    #buggie list.append(desc_filescan)
    if config.plugins.filebrowser.add_extensionmenu_entry.value:
        list.append(desc_extensionmenu)
    list.append(desc_mainmenu)
    return list
