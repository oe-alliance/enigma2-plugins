__doc__ = '''
Beyonwiz T3 Plugin
For any recorded series (2 or more episodes with same name)
create a sub-directory and move the series episodes into it

Mike Griffin  8/02/2015

TODO:
auto-run at intervals
'''

from Plugins.Plugin import PluginDescriptor
from Screens.MovieSelection import MovieSelection
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ConfigList import ConfigListScreen
from Components.UsageConfig import defaultMoviePath
from Components.config import config, ConfigText, getConfigListEntry
from time import time, localtime, strftime
from collections import defaultdict
from os.path import isfile, isdir, splitext, join as joinpath, split as splitpath
import os

def Plugins(**kwargs):
    return PluginDescriptor(
        name='Series to Folder',
        description='Move series recordings into folders',
        where=PluginDescriptor.WHERE_MOVIELIST,
        needsRestart=False,
        fnc=main
    )

def main(session, service, **kwargs):
    session.open(Series2Folder, service)

class Series2Folder(ChoiceBox):
    def __init__(self, session, service):
        self.movieSelection = session.current_dialog if isinstance(session.current_dialog, MovieSelection) else None
        list = [
            (_("Move series recordings to folders"), "CALLFUNC", self.doMoves),
            (_("Move selected series recording to folder"), "CALLFUNC", self.doMoves, service),
            (_("Configure move series recordings to folders"), "CALLFUNC", self.doConfig),
            (_("Cancel"), "CALLFUNC", self.doCancel),
        ]
        ChoiceBox.__init__(self, session, _("Series to Folder"), list=list, selection=0)

    def doConfig(self, arg):
        self.session.open(Series2FolderConfig)

    def doCancel(self, arg):
        self.close(False)

    def doMoves(self, service):

        # Selection if called on a specific recording
        moveSelection = None

        # Movie recording path
        rootdir = defaultMoviePath()

        initErrMess = "--------\n"
        errMess = initErrMess

        if service is not None:
                dir, fullname = splitpath(service.getPath())
                if dir + '/' == rootdir and fullname:
                    showname, date_time, err = self.getShowInfo(rootdir, fullname)
                    if showname:
                        moveSelection = showname
                    elif err:
                        errMess += err

        # Full pathnames of current recordings' .ts files
        isRecording = set([timer.Filename + '.ts' for timer in self.session.nav.RecordTimer.timer_list if timer.state in (timer.StatePrepared, timer.StateRunning)])

        # Folder for movies
        moviesFolder = config.plugins.seriestofolder.movies.value and config.plugins.seriestofolder.moviesfolder.value

        # lists of shows in each series and for movies
        shows = defaultdict(list)

        # directories
        dirs = set()

        for f in os.listdir(rootdir):
            fullpath = joinpath(rootdir, f)
            if f.endswith('.ts') and f[0:8].isdigit() and fullpath not in isRecording and isfile(fullpath):
                showname, date_time, err = self.getShowInfo(rootdir, f)
                if showname and (not moveSelection or showname == moveSelection):
                    if moviesFolder and showname.lower().startswith("movie: "):
                        shows[moviesFolder].append((showname, f, date_time))
                    else:
                        shows[showname].append((showname, f, date_time))
                elif err:
                    errMess += err
            elif isdir(fullpath):
                dirs.add(f)

        # create a directory for each series and move shows into it
        # also add any single shows to existing series directories
        moves = ''
        numRecordings = int(config.plugins.seriestofolder.autofolder.value)
        for foldername, fileInfo in sorted(shows.items()):
            if (numRecordings != 0 and len(fileInfo) >= numRecordings) or foldername == moviesFolder or foldername in dirs or moveSelection:
                errorText = ''
                nerrors = 0
                for showname, fullname, date_time in fileInfo:
                    for f in self.recFileList(rootdir, fullname):
                        try:
                            os.renames(joinpath(rootdir, f), joinpath(rootdir, foldername, f))
                            print "[Series2Folder] rename", joinpath(rootdir, f), "to", joinpath(rootdir, foldername, f)
                        except Exception, e:
                            errMess += e.__str__() + "\n"
                            nerrors += 1
                            errorText = ngettext(" - Error", " - Errors", nerrors)
                    moves += '%s - %s%s\n' % (showname, date_time, errorText)

        if errMess != initErrMess:
                moves += errMess
        if moves:
            if self.movieSelection:
                self.movieSelection.reloadList()
            self.MsgBox('Series to Folder moved the following episodes:\n%s' % moves)
        else:
            self.MsgBox('Series to Folder did not find anything to move in %s' % rootdir, 5)
        self.close()

    def MsgBox(self, msg, timeout=30):
        self.session.open(MessageBox, _(msg), type=MessageBox.TYPE_INFO, timeout=timeout)

    def recFileList(self, rootdir, fullname):
        base, ext = splitext(fullname)
        l = [fullname]
        for e in (".eit",):
            f = base + e
            if isfile(joinpath(rootdir, f)):
                l.append(f)
        base = fullname
        for e in (".ap", ".cuts", ".meta", ".sc"):
            f = base + e
            if isfile(joinpath(rootdir, f)):
                l.append(f)
        return l

    def getShowInfo(self, rootdir, fullname):
        path = joinpath(rootdir, fullname) + '.meta'
        try:
            lines = open(path).readlines()
            showname = lines[1].strip()
            t = int(lines[3].strip())
            date_time = strftime("%d.%m.%Y %H:%M", localtime(t))
            filebase = splitext(fullname)[0]
            if filebase[-4:-3] == "_" and filebase[-3:].isdigit():
                date_time += '#' + filebase[-3:]
        except:
            return self.recSplit(fullname)
        return showname, date_time, None

    def recSplit(self, fullname):
        try:
            startOffset = 2
            parts = fullname.split(' - ')
            date_time = parts[0][6:8] + '.' + parts[0][4:6] + '.' + parts[0][0:4]
            if len(parts[0]) > 8:
                date_time += ' ' + parts[0][9:11] + ':' + parts[0][11:13]
            else:
                startOffset = 1
            showname = splitext(parts[-1])[0]
            if showname[-4:-3] == "_" and showname[-3:].isdigit():
                date_time += '#' + showname[-3:]
                showname = showname[0:-4]
            showname = ' - '.join(parts[startOffset:-1] + [showname])
        except:
            return None, None, "Can't extract show name for: %s\n" % fullname
        return showname, date_time, None

class Series2FolderConfig(ConfigListScreen, Screen):
    skin = """
<screen name="Series2FolderConfig" position="center,center" size="640,201" title="Configure Series To Folder" >
    <widget name="config" position="20,10" size="600,75" />
    <widget name="description" position="20,e-103" size="600,66" font="Regular;18" foregroundColor="grey" halign="left" valign="top" />
    <ePixmap name="red" position="20,e-28" size="15,16" pixmap="skin_default/buttons/button_red.png" alphatest="blend" />
    <ePixmap name="green" position="170,e-28" size="15,16" pixmap="skin_default/buttons/button_green.png" alphatest="blend" />
    <widget name="VKeyIcon" position="470,e-28" size="15,16" pixmap="skin_default/buttons/button_blue.png" alphatest="blend" />
    <widget name="key_red" position="40,e-30" size="150,25" valign="top" halign="left" font="Regular;20" />
    <widget name="key_green" position="190,e-30" size="150,25" valign="top" halign="left" font="Regular;20" />
    <widget name="key_yellow" position="340,e-30" size="150,25" valign="top" halign="left" font="Regular;20" />
    <widget name="key_blue" position="490,e-30" size="150,25" valign="top" halign="left" font="Regular;20" />
</screen>"""

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        self["description"] = Label()
        self["HelpWindow"] = Label()
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("Save"))
        self["key_yellow"] = Label()
        self["key_blue"] = Label(_("Keyboard"))
        self["VKeyIcon"] = Pixmap()
        self.list = []

        self._confAutofolder = getConfigListEntry(
            _("Automatically create folders"),
            config.plugins.seriestofolder.autofolder,
            _("Create a folder for a series automatically if there are this number of recordings or more. If set to \"no autocreate\" only move recordings if a folder already exists for them.")
        )
        self._confMovies = getConfigListEntry(
            _("Put movies into folder"),
            config.plugins.seriestofolder.movies,
            _("Move recordings whose names start with \"Movie: \" (case insensitive) to a folder for movies.")
        )
        self._confMoviesfolder = getConfigListEntry(
            _("Folder for movies"),
            config.plugins.seriestofolder.moviesfolder,
            _("The name of the folder for movies.")
        )

        ConfigListScreen.__init__(self, self.list, session)

        self["Conf"] = ActionMap(contexts=["SetupActions", "ColorActions"], actions={
            "cancel": self.cancel,
            "red": self.cancel,
            "green": self.save,
            "blue": self.keyboard,
            "ok": self.keyboard,
        }, prio=-2)

        self.createConfig(self["config"])

    def createConfig(self, configList):
        list = [
            self._confAutofolder,
            self._confMovies,
        ]
        if self._confMovies[1].value:
            list.append(self._confMoviesfolder)
        self.list = list
        configList.list = list
        configList.l.setList(list)

    def updateConfig(self):
        currConf = self["config"].getCurrent()
        if currConf is self._confMovies:
            self.createConfig(self["config"])

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.updateConfig()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.updateConfig()

    def keyboard(self):
        selection = self["config"].getCurrent()
        if isinstance(selection[1], ConfigText):
            self.KeyText()

    def cancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close(False)

    def save(self):
        self.saveAll()
        self.close()
