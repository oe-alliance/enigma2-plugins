__doc__ = '''
Beyonwiz T3 Plugin
For any recorded series (configurable number of episodes with same name)
create a sub-directory and move the series episodes into it

Mike Griffin  8/02/2015

TODO:
auto-run at intervals
'''

from Plugins.Plugin import PluginDescriptor
from Screens.MovieSelection import MovieSelection
from Screens.MessageBox import MessageBox
from Screens.TextBox import TextBox
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
import Screens.Standby
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ConfigList import ConfigListScreen
from Components.PluginComponent import plugins
from Components.Task import job_manager as JobManager
from Components.UsageConfig import defaultMoviePath
from Components.config import config, ConfigText, getConfigListEntry
from Tools import ASCIItranslit
from time import time, localtime, strftime
from boxbranding import getMachineBrand, getMachineName
from collections import defaultdict
from os.path import isfile, isdir, splitext, join as joinpath, split as splitpath
import os

def menu(session, service, **kwargs):
    session.open(Series2Folder, service)

def buttonSeries2Folder(session, service, **kwargs):
    actions = Series2FolderActions(session)
    actions.doMoves()

def buttonSelSeries2Folder(session, service, **kwargs):
    actions = Series2FolderActions(session)
    actions.doMoves(service)

pluginSeries2Folder = PluginDescriptor(
    name=_('Series2Folder'),
    description=_('Series to Folder'),
    where=PluginDescriptor.WHERE_MOVIELIST,
    needsRestart=False,
    fnc=buttonSeries2Folder
)

pluginSelSeries2Folder = PluginDescriptor(
    name=_('SelSeries2Folder'),
    description=_('Sel Series to Folder'),
    where=PluginDescriptor.WHERE_MOVIELIST,
    needsRestart=False,
    fnc=buttonSelSeries2Folder
)

def Plugins(**kwargs):
    plugins = [PluginDescriptor(
        name=_('Series2Folder...'),
        description=_('Series to Folder...'),
        where=PluginDescriptor.WHERE_MOVIELIST,
        needsRestart=True,
        fnc=menu
    )]
    if config.plugins.seriestofolder.showmovebutton.value:
        plugins.append(pluginSeries2Folder)
    if config.plugins.seriestofolder.showselmovebutton.value:
        plugins.append(pluginSelSeries2Folder)
    return plugins

def addRemovePlugin(configElement, plugin):
    if configElement.value:
        if plugin not in plugins.pluginList:
            plugins.addPlugin(plugin)
    else:
        if plugin in plugins.pluginList:
            plugins.removePlugin(plugin)

config.plugins.seriestofolder.showmovebutton.addNotifier(
    lambda conf: addRemovePlugin(conf, pluginSeries2Folder),
    initial_call=False,
    immediate_feedback=False
)
config.plugins.seriestofolder.showselmovebutton.addNotifier(
    lambda conf: addRemovePlugin(conf, pluginSelSeries2Folder),
    initial_call=False,
    immediate_feedback=False
)

class Series2FolderActions:
    def __init__(self, session):
        self.session = session
        self.movieSelection = session.current_dialog if isinstance(session.current_dialog, MovieSelection) else None

    def doMoves(self, service=None):

        if Screens.Standby.inTryQuitMainloop:
            self.MsgBox("Your %s %s is trying to shut down. No recordings moved." % (getMachineBrand(), getMachineName()), timeout=10)
            return

        if JobManager.getPendingJobs():
            self.MsgBox("Your %s %s running tasks that may be accessing the recordings. No recordings moved." % (getMachineBrand(), getMachineName()), timeout=10)
            return

        # Selection if called on a specific recording
        moveSelection = None

        # Movie recording path
        rootdir = defaultMoviePath()

        errMess = []

        if service is not None:
                dir, fullname = splitpath(service.getPath())
                if dir + '/' == rootdir and fullname:
                    showname, __, date_time, err = self.getShowInfo(rootdir, fullname)
                    if showname:
                        moveSelection = self.cleanName(self.stripRepeat(showname))
                    elif err:
                        errMess.append(err)

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
                origShowname, pending_merge, date_time, err = self.getShowInfo(rootdir, f)
                noRepeatName = self.stripRepeat(origShowname)
                showname = self.cleanName(noRepeatName)
                if showname and (not moveSelection or showname == moveSelection) and not pending_merge:
                    if moviesFolder and noRepeatName.lower().startswith("movie: "):
                        shows[moviesFolder].append((origShowname, f, date_time))
                    else:
                        shows[showname].append((origShowname, f, date_time))
                elif err:
                    errMess.append(err)
            elif isdir(fullpath):
                dirs.add(f)

        # create a directory for each series and move shows into it
        # also add any single shows to existing series directories
        moves = []
        numRecordings = int(config.plugins.seriestofolder.autofolder.value)
        for foldername, fileInfo in sorted(shows.items()):
            if (numRecordings != 0 and len(fileInfo) >= numRecordings) or foldername == moviesFolder or foldername in dirs or moveSelection:
                errorText = ''
                nerrors = 0
                for origShowname, fullname, date_time in fileInfo:
                    for f in self.recFileList(rootdir, fullname):
                        try:
                            os.renames(joinpath(rootdir, f), joinpath(rootdir, foldername, f))
                            print "[Series2Folder] rename", joinpath(rootdir, f), "to", joinpath(rootdir, foldername, f)
                        except Exception, e:
                            errMess.append(e.__str__())
                            nerrors += 1
                            errorText = ngettext(" - Error", " - Errors", nerrors)
                    moves.append('%s - %s%s' % (origShowname, date_time, errorText))

        if moves and self.movieSelection:
                self.movieSelection.reloadList()

        if moves:
            title = _("Series to Folder moved the following episodes")
            if errMess:
                title += ngettext(" - with an error", " - with errors", len(errMess))
        else:
            title = _("Series to Folder did not find anything to move in %s") % rootdir

        if errMess or len(moves) > 20:
            if errMess:
                moves.append("--------")
            moves += errMess
            self.session.open(ErrorBox, text='\n'.join(moves), title=title)
        elif moves:
            self.MsgBox('\n'.join([title + ':'] + moves))
        else:
            self.MsgBox(title, timeout=10)

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

    def stripRepeat(self, name):
        name = name.strip()

        if config.plugins.seriestofolder.striprepeattags.value:
            repeat_str = config.plugins.seriestofolder.repeatstr.value.strip()
            if repeat_str:
                if name.startswith(repeat_str):
                    name = name[len(repeat_str):].strip()
                elif name.endswith(repeat_str):
                    name = name[:-len(repeat_str)].strip()
        return name

    def cleanName(self, name):
        name = name.strip()

        if not config.plugins.seriestofolder.portablenames.value:
            return name

        # filter out non-allowed characters
        non_allowed_characters = "/.\\:*?<>|\""
        name = name.replace('\xc2\x86', '').replace('\xc2\x87', '')
        name = ''.join(['_' if c in non_allowed_characters or ord(c) < 32 else c for c in name])
        return name

    def getShowInfo(self, rootdir, fullname):
        path = joinpath(rootdir, fullname) + '.meta'
        err_mess = None
        try:
            lines = open(path).readlines()
            showname = lines[1].strip()
            t = int(lines[3].strip())
            pending_merge = len(lines) > 4 and "pts_merge" in lines[4].strip().split(' ')
            date_time = strftime("%d.%m.%Y %H:%M", localtime(t))
            filebase = splitext(fullname)[0]
            if filebase[-4:-3] == "_" and filebase[-3:].isdigit():
                date_time += '#' + filebase[-3:]
        except:
            showname, date_time, False, err_mess = self.recSplit(fullname)

        if showname:
            showname.replace('/', '_')
            showname = showname[:255]

        return showname, pending_merge, date_time, err_mess

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
            return None, None, False, _("Can't extract show name for: %s") % fullname
        return showname, date_time, False, None

class Series2Folder(ChoiceBox):
    def __init__(self, session, service):
        list = [
            (_("Move series recordings to folders"), "CALLFUNC", self.doMoves),
            (_("Move selected series recording to folder"), "CALLFUNC", self.doMoves, service),
            (_("Configure move series recordings to folders"), "CALLFUNC", self.doConfig),
            (_("Cancel"), "CALLFUNC", self.doCancel),
        ]
        ChoiceBox.__init__(self, session, _("Series to Folder"), list=list, selection=0)
        self.actions = Series2FolderActions(session)

    def doMoves(self, service):
        self.actions.doMoves(service)
        self.close()

    def doConfig(self, arg):
        self.session.open(Series2FolderConfig)

    def doCancel(self, arg):
        self.close(False)


class ErrorBox(TextBox):
    skin = """<screen name="Series2Folder" backgroundColor="background" position="90,150" size="1100,450" title="Log">
        <widget font="Regular;18" name="text" position="0,4" size="1100,446"/>
</screen>"""

class Series2FolderConfig(ConfigListScreen, Screen):
    skin = """
<screen name="Series2FolderConfig" position="center,center" size="640,326" title="Configure Series To Folder" >
    <widget name="config" position="20,10" size="600,200" />
    <widget name="description" position="20,e-106" size="600,88" font="Regular;18" foregroundColor="grey" halign="left" valign="top" />
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
        self._confPortableNames = getConfigListEntry(
            _("Use portable folder names"),
            config.plugins.seriestofolder.portablenames,
            _("Use more portable (Windows-friendly) names for folders.")
        )
        self._confStripRepeats = getConfigListEntry(
            _("Strip repeat tags from series names"),
            config.plugins.seriestofolder.striprepeattags,
            _("Strip repeat tagging from series titles when creating directory names.")
        )
        self._confRepeatStr = getConfigListEntry(
            _("Strip repeat tags from series names"),
            config.plugins.seriestofolder.repeatstr,
            _("Repeat tag to be stripped from from series titles when creating directory names.")
        )
        self._confMovies = getConfigListEntry(
            _("Put movies into folder"),
            config.plugins.seriestofolder.movies,
            _('Move recordings whose names start with "Movie: " (case insensitive) to a folder for movies.')
        )
        self._confMoviesfolder = getConfigListEntry(
            _("Folder for movies"),
            config.plugins.seriestofolder.moviesfolder,
            _("The name of the folder for movies.")
        )
        self._confShowmovebutton = getConfigListEntry(
            _("Show move series option"),
            config.plugins.seriestofolder.showmovebutton,
            _("Single-action move series to folder shown in menu and as button option. Requires restart if changed.")
        )
        self._confShowselmovebutton = getConfigListEntry(
            _("Show move selected series option"),
            config.plugins.seriestofolder.showselmovebutton,
            _("Single-action move selected series to folder shown in menu and as button option. Requires restart if changed.")
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
            self._confShowmovebutton,
            self._confShowselmovebutton,
            self._confAutofolder,
            self._confStripRepeats,
        ]
        if self._confStripRepeats[1].value:
            list.append(self._confRepeatStr)
        list += [
            self._confPortableNames,
            self._confMovies,
        ]
        if self._confMovies[1].value:
            list.append(self._confMoviesfolder)
        self.list = list
        configList.list = list
        configList.l.setList(list)

    def updateConfig(self):
        currConf = self["config"].getCurrent()
        if currConf in (self._confStripRepeats, self._confMovies):
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
