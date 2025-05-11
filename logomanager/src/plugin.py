from __future__ import print_function
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Components.Label import Label
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigSelection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.SystemInfo import BoxInfo
from os import path as os_path, listdir as os_listdir, system as os_system, remove as os_remove
###############################################################################
config.plugins.logomanager = ConfigSubsection()
config.plugins.logomanager.path = ConfigSelection([("/media/cf/bootlogos/", _("CF Drive")), ("/media/hdd/bootlogos/", _("Harddisk"))], default="/media/hdd/bootlogos/")


from mimetypes import add_type
add_type("image/mvi", ".mvi")

#########


def filescan_open(list, session, **kwargs):
    print("filescan_open", list, kwargs)
    session.open(LogoManagerScreen, file=list[0].path)


def start_from_filescan(**kwargs):
    from Components.Scanner import Scanner, ScanPath
    print("start_from_filescan", kwargs)
    return \
        Scanner(mimetypes=["image/jpeg", "image/mvi"],
            paths_to_scan=[
                    ScanPath(path="", with_subdirs=False),
                ],
            name="Logo Manager",
            description="view Bootlogo/MVI",
            openfnc=filescan_open,
        )


def main(session, **kwargs):
    if os_path.isdir(config.plugins.logomanager.path.value) is not True:
        session.open(LogoManagerConfigScreen)
    else:
        session.open(LogoManagerScreen)


def Plugins(path, **kwargs):
    global plugin_path
    plugin_path = path
    return [
             PluginDescriptor(
                name="Logo Manager",
                description="manage logos to display at boottime",
                where=PluginDescriptor.WHERE_PLUGINMENU,
                icon="plugin.png",
                fnc=main
                ),
             PluginDescriptor(name="Logo Manager", where=PluginDescriptor.WHERE_FILESCAN, fnc=start_from_filescan)
            ]
###############################################################################


class LogoManagerScreen(Screen):
    skin = """
        <screen flags="wfNoBorder" position="60,450" size="600,29" title="Logo Manager" >
            <widget name="filelist" position="0,0" size="600,30"  />
         </screen>"""

    targets = [
                ("bootlogo", "/boot/bootlogo.mvi"), ("wait", "/boot/bootlogo_wait.mvi"), ("backdrop", "/boot/backdrop.mvi"), ("radio", "/usr/share/enigma2/radio.mvi")
               ]

    def __init__(self, session, file=None):
        self.session = session
        self.skin = LogoManagerScreen.skin
        Screen.__init__(self, session)
        self["filelist"] = MenuList([])
        self["filelist"].onSelectionChanged.append(self.showSelected)
        self["actions"] = ActionMap(["WizardActions", "DirectionActions", "MenuActions", "ShortcutActions", "GlobalActions"],
            {
             "ok": self.showSelected,
             "back": self.exit,
             "menu": self.openMenu,
             }, -1)
        ##
        if BoxInfo.getItem("model") == "dm800":
            self.targets.append(("switchoff", "/boot/switchoff.mvi"))
        ## stop current service to free the videodevice
        self.current_service = self.session.nav.getCurrentlyPlayingServiceReference()
        self.session.nav.stopService()

        self.check_backup()

        self.makeBootWritable()
        if file is None:
            self.setlist_to_avaiable()
            self.onShown.append(self.showSelected)
        elif os_path.isfile(file):
            e = lambda: self.reloadPictures([file])
            self.onShown.append(e)
            d = lambda: self.showMVI(file)
            self.onShown.append(d)

    def check_backup(self):
        """ if a copy of the original file is not found in the plugindir, backup them """
        global plugin_path
        for target in self.targets:
            file = target[1].split("/")[-1]
            if os_path.isfile(plugin_path + file) is not True:
                print("backing up original ", target[0], " from ", file)
                os_system("cp '%s' '%s'" % (target[1], plugin_path + "/" + file))

    def restoreOriginal(self):
        """ restoring original mvis from the backuped mvi in the plugindir"""
        global plugin_path
        for target in self.targets:
            file = target[1].split("/")[-1]
            if os_path.isfile(plugin_path + "/" + file) is True:
                print("restoring original ", target[0], " from ", plugin_path + "/" + file, "to", target[1])
                os_system("cp '%s' '%s'" % (plugin_path + "/" + file, target[1]))

    def exit(self):
        """ quit me """
        self.makeBootReadonly()
        self.session.nav.playService(self.current_service)
        self.close()

    def showSelected(self):
        """ show the currently selected MVI of the list """
        sel = self["filelist"].getCurrent()
        if sel is not None:
          self.showMVI(sel[1])

    def openMenu(self):
        """ opens up the Main Menu """
        menu = []
        menu.append(("install selected Logo as ...", self.action_install))
        menu.append(("show active Logos", self.setlist_to_current))
        menu.append(("show available Logos", self.setlist_to_avaiable))
        menu.append(("reset all Logos to default", self.restoreOriginal))
        menu.append(("open configuration", self.openConfig))
        self.session.openWithCallback(self.selectedMenu, ChoiceBox, _("please select a option"), menu)

    def openConfig(self):
        self.session.open(LogoManagerConfigScreen)

    def selectedMenu(self, choice):
        if choice is not None:
            choice[1]()

    def setlist_to_current(self):
        """ fills the list with the target MVIs"""
        global plugin_path
        filelist = []
        for i in self.targets:
            filelist.append(i[1])
        self.reloadPictures(filelist)

    def setlist_to_avaiable(self):
        """ fills the list with all found new MVIs"""
        filelist = []
        for i in os_listdir(config.plugins.logomanager.path.value):
            if i.endswith(".mvi"):
                filelist.append(config.plugins.logomanager.path.value + i)
        filelist.sort()
        self.reloadPictures(filelist)

    def action_install(self):
        """ choicebox, to select target to install an mvi to"""
        self.session.openWithCallback(self.selectedTarget, ChoiceBox, _("select Target for logo"), self.targets)

    def selectedTarget(self, choice):
        if choice is not None:
            self.installMVI(choice, self["filelist"].getCurrent()[1])

    def reloadPictures(self, filelist):
        """ build the menulist with givven files """
        list = []
        for i in filelist:
                list.append((i.split("/")[-1], i))
        self["filelist"].l.setList(list)

    def showMVI(self, mvifile):
        """ shows a mvi """
        print("playing MVI", mvifile)
        os_system("/usr/bin/showiframe '%s'" % mvifile)

    def installMVI(self, target, sourcefile):
        """ installs a mvi by overwriting the target with a source mvi """
        print("installing %s as %s on %s" % (sourcefile, target[0], target[1]))
        if os_path.isfile(target[1]):
            os_remove(target[1])
        os_system("cp '%s' '%s'" % (sourcefile, target[1]))

    def makeBootWritable(self):
        """ because /boot isnt writeable by default, we will change that here """
        os_system("mount -o rw,remount /boot")

    def makeBootReadonly(self):
        """ make /boot writeprotected back again """
        os_system("mount -o r,remount /boot")


class LogoManagerConfigScreen(ConfigListScreen, Screen):
    skin = """
        <screen position="100,100" size="550,400" title="LogoManager Setup" >
        <widget name="config" position="0,0" size="550,360" scrollbarMode="showOnDemand" />
        <widget name="buttonred" position="10,360" size="100,40" backgroundColor="red" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/>
        <widget name="buttongreen" position="120,360" size="100,40" backgroundColor="green" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/>
        </screen>"""

    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self.list = []
        self.list.append(getConfigListEntry(_("Directory to scan for Logos"), config.plugins.logomanager.path))
        ConfigListScreen.__init__(self, self.list)
        self["buttonred"] = Label(_("cancel"))
        self["buttongreen"] = Label(_("ok"))
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
