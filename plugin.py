__doc__ = '''
Beyonwiz T series Plugin
For any recorded series (configurable number of episodes with same name)
create a sub-directory and move the series episodes into it, with
an option to do the processing automatically in the background.

Mike Griffin  8/02/2015
'''

__version__ = "1.11dev2"

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
from Components.Sources.Boolean import Boolean
from Components.ConfigList import ConfigListScreen
from Components.PluginComponent import plugins
from Components.Task import job_manager as JobManager
from Components.UsageConfig import defaultMoviePath
from Components.config import config, ConfigText, getConfigListEntry
from Tools import Notifications
from Tools.BoundFunction import boundFunction
import NavigationInstance
from enigma import eTimer, iRecordableService, iPlayableService, ePoint
from time import time, localtime, strftime
from boxbranding import getMachineBrand, getMachineName
from collections import defaultdict
from os.path import isfile, isdir, splitext, join as joinpath, split as splitpath, lexists
import os

from .FileScreens import activeFileScreens

_autoSeries2Folder = None
_session = None

def menu(session, service, serviceList=None, **kwargs):
    session.open(Series2Folder, service, serviceList=serviceList)

def buttonSeries2Folder(session, service, *args, **kwargs):
    actions = Series2FolderActions(session)
    actions.doMoves(service)

def buttonSelSeries2Folder(session, service, serviceList=None, *args, **kwargs):
    actions = Series2FolderActions(session)
    actions.doMoves(service, selectedOnly=True, serviceList=serviceList)

def autoSeries2Folder(reason, session, **kwargs):
    global _autoSeries2Folder
    global _session

    if _session is None:
        _session = session

    if reason == 0:
        if config.plugins.seriestofolder.auto.value:
            if not _autoSeries2Folder:
                _autoSeries2Folder = Series2FolderAutoActions(session)
                _autoSeries2Folder.autoStart()
    elif reason == 1:
        if _autoSeries2Folder:
            _autoSeries2Folder.autoStop()
            _autoSeries2Folder = None

def __autoSwitched(conf):
    autoSeries2Folder(int(not config.plugins.seriestofolder.auto.value), _session)

config.plugins.seriestofolder.auto.addNotifier(__autoSwitched, initial_call=False, immediate_feedback=False, extra_args=None)

def multiPluginDescriptor(name="Plugin", where=None, description="", icon=None, fnc=None, wakeupfnc=None, needsRestart=None, internal=False, weight=0, multi=False):
    try:
        return PluginDescriptor(name=name, where=where, description=description, icon=icon, fnc=fnc, wakeupfnc=wakeupfnc, needsRestart=needsRestart, internal=internal, weight=weight, multi=multi)
    except TypeError:
        return PluginDescriptor(name=name, where=where, description=description, icon=icon, fnc=fnc, wakeupfnc=wakeupfnc, needsRestart=needsRestart, internal=internal, weight=weight)

pluginSeries2Folder = multiPluginDescriptor(
    name=_('Series2Folder'),
    description=_('Series to Folder'),
    where=PluginDescriptor.WHERE_MOVIELIST,
    needsRestart=False,
    fnc=buttonSeries2Folder,
    multi=True
)

pluginSelSeries2Folder = multiPluginDescriptor(
    name=_('SelSeries2Folder'),
    description=_('Sel Series to Folder'),
    where=PluginDescriptor.WHERE_MOVIELIST,
    needsRestart=False,
    fnc=buttonSelSeries2Folder,
    multi=True
)


def Plugins(**kwargs):
    plugins = [
        PluginDescriptor(
            name="AutoSeries2Folder",
            where=PluginDescriptor.WHERE_SESSIONSTART,
            description=_("Auto Series to Folder"),
            needsRestart=False,
            fnc=autoSeries2Folder
        ),
        multiPluginDescriptor(
            name=_('Series2Folder...'),
            description=_('Series to Folder...'),
            where=PluginDescriptor.WHERE_MOVIELIST,
            needsRestart=True,
            fnc=menu,
            multi=True
        ),
    ]
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

class Series2FolderActionsBase(object):
    TS = ".ts"
    META = ".meta"
    BAREEXTS = frozenset((".eit",))
    TSEXTS = frozenset((".ap", ".cuts", ".meta", ".sc"))

    def __init__(self, session):
        self.session = session

        # Movie recording path
        self.rootdir = defaultMoviePath()

        # Information about moves and errors
        self.moves = []
        self.errMess = []

    def prepare(self, service, selectedOnly=False, serviceList=None):
        # Get local copies of config variables in case they change during a run
        self.conf_autofolder = config.plugins.seriestofolder.autofolder.value
        self.conf_movies = config.plugins.seriestofolder.movies.value
        self.conf_moviesfolder = config.plugins.seriestofolder.moviesfolder.value
        self.conf_portablenames = config.plugins.seriestofolder.portablenames.value
        self.conf_striprepeattags = config.plugins.seriestofolder.striprepeattags.value
        self.conf_repeatstr = config.plugins.seriestofolder.repeatstr.value

        # Update rootdir in case defaultMoviePath changes during
        # the lifetime of a persistent instance

        self.rootdir = defaultMoviePath()

        # Selection if called on specific recordings
        self.moveSelection = set()

        # Information about moves and errors
        self.moves = []
        self.errMess = []

        if serviceList is None and service is not None:
                serviceList = [service]

        if serviceList is not None:
            for serv in serviceList:
                dir, fullname = splitpath(serv.getPath())
                self.rootdir = dir
                if fullname and selectedOnly:
                    showname, __, __, err = self.getShowInfo(self.rootdir, fullname)
                    if showname:
                        self.moveSelection.add(self.cleanName(self.stripRepeat(showname)))
                    elif err:
                        self.errMess.append(err)

        # Full pathnames of current recordings' .ts files
        self.isRecording = set([timer.Filename + self.TS for timer in self.session.nav.RecordTimer.timer_list if timer.state in (timer.StatePrepared, timer.StateRunning) and not timer.justplay and hasattr(timer, "Filename")])

        # Folder for movies
        self.moviesFolder = self.conf_movies and self.conf_moviesfolder

        # lists of shows in each series and for movies
        self.shows = defaultdict(list)

        # directories
        self.dirs = set()

    def addRecording(self, f):
        fullpath = joinpath(self.rootdir, f)
        if self.recNameType(f) is not None and fullpath not in self.isRecording and isfile(fullpath):
            origShowname, pending_merge, date_time, err = self.getShowInfo(self.rootdir, f)
            noRepeatName = self.stripRepeat(origShowname)
            showname = self.cleanName(noRepeatName)
            if showname and (not self.moveSelection or showname in self.moveSelection) and not pending_merge:
                if not self.isPlaying(fullpath):
                    if self.moviesFolder and noRepeatName.lower().startswith("movie: "):
                        self.shows[self.moviesFolder].append((origShowname, f, date_time))
                    else:
                        self.shows[showname].append((origShowname, f, date_time))
            elif err:
                self.errMess.append(err)
        elif isdir(fullpath):
            self.dirs.add(f)

    def processRecording(self):
        foldername, fileInfo = self.shows.pop(0)
        numRecordings = int(self.conf_autofolder)
        if (numRecordings != 0 and len(fileInfo) >= numRecordings) or foldername == self.moviesFolder or foldername in self.dirs or self.moveSelection:
            for origShowname, fullname, date_time in fileInfo:
                if not self.isPlaying(joinpath(self.rootdir, fullname)):

                    errorText = self.renameRecording(foldername, fullname)
                    self.moves.append('%s - %s%s' % (origShowname, date_time, errorText))

    def renameRecording(self, foldername, fullname):
        errorText = ''
        nerrors = 0
        renameList = self.recRenameList(foldername, fullname)
        if renameList:
            for fromPath, toPath in renameList:
                try:
                    os.renames(fromPath, toPath)
                    print "[Series2Folder] rename", fromPath, "to", toPath
                except Exception as e:
                    self.errMess.append(e.__str__())
                    nerrors += 1
                    errorText = ngettext(" - Error", " - Errors", nerrors)
        else:
            self.errMess.append(_("Too many recordings with similar filenames: %s") % fullname)
            errorText = _(" - Error")
        return errorText

    def recRenameList(self, foldername, fullname):
        i = 0
        destBase, destExt = splitext(fullname)
        while True:
            if i:
                suffix = "_%03d" % i
            else:
                suffix = ''
            i += 1
            renameList = tuple(((joinpath(self.rootdir, f), joinpath(self.rootdir, foldername, self.addSuffix(f, suffix))) for f in self.recFileList(self.rootdir, fullname)))
            if not any((lexists(t[1]) for t in renameList)):
                return renameList
            if i > 999:
                return []

    def addSuffix(self, f, suffix):
        if not suffix:
            return f
        base1, ext1 = splitext(f)
        if ext1 in self.TSEXTS:
            base2, ext2 = splitext(base1)
            if base2[-4:-3] == '_' and base2[-3:].isdigit():
                base2 = base2[0:-4]
            return base2 + suffix + ext2 + ext1
        if base1[-4:-3] == '_' and base1[-3:].isdigit():
            base1 = base1[0:-4]
        return base1 + suffix + ext1

    def finish(self, notification=False, stopping=False):
        if self.moves:
            title = ngettext("Series to Folder moved the following recording", "Series to Folder moved the following recordings", len(self.moves))
            if self.errMess:
                title += ngettext(" - with an error", " - with errors", len(self.errMess))
        else:
            title = _("Series to Folder did not find anything to move in %s") % self.rootdir

        if self.errMess or len(self.moves) > 20:
            if self.errMess:
                self.moves.append("--------")
            self.moves += self.errMess
            self.session.open(ErrorBox, text='\n'.join(self.moves), title=title)
        elif self.moves:
            self.MsgBox('\n'.join([title + ':'] + self.moves), notification=notification)
        else:
            self.MsgBox(title, timeout=10, notification=notification)
        self.moves = []
        self.errMess = []

    def MsgBox(self, msg, timeout=30, notification=False, msgType=MessageBox.TYPE_INFO):
        if notification:
            Notifications.AddNotification(MessageBox, msg, msgType, timeout=timeout)
        else:
            self.session.open(MessageBox, msg, type=msgType, timeout=timeout)

    def isPlaying(self, fullpath):
        playing = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
        return playing is not None and playing.valid() and playing.getPath() == fullpath

    def recFileList(self, rootdir, fullname):
        base, ext = splitext(fullname)
        l = [fullname]
        for e in self.BAREEXTS:
            f = base + e
            if isfile(joinpath(rootdir, f)):
                l.append(f)
        base = fullname
        for e in self.TSEXTS:
            f = base + e
            if isfile(joinpath(rootdir, f)):
                l.append(f)
        return l

    def stripRepeat(self, name):
        name = name.strip()

        if self.conf_striprepeattags:
            repeat_str = self.conf_repeatstr.strip()
            if repeat_str:
                if name.startswith(repeat_str):
                    name = name[len(repeat_str):].strip()
                elif name.endswith(repeat_str):
                    name = name[:-len(repeat_str)].strip()
        return name

    def cleanName(self, name):
        name = name.strip()

        if not self.conf_portablenames:
            return name

        # filter out non-allowed characters
        non_allowed_characters = "/.\\:*?<>|\""
        name = name.replace('\xc2\x86', '').replace('\xc2\x87', '')
        name = ''.join(['_' if c in non_allowed_characters or ord(c) < 32 else c for c in name])
        return name

    def getShowInfo(self, rootdir, fullname):
        path = joinpath(rootdir, fullname) + self.META
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
            showname, date_time, pending_merge, err_mess = self.recSplit(fullname)

        if showname:
            showname.replace('/', '_')
            showname = showname[:255]

        return showname, pending_merge, date_time, err_mess

    def recNameType(self, fullname):
        def isDate(s):
            return s.isdigit() and len(s) == 8 and int(s[4:6]) <= 12 and int(s[6:8]) <= 31

        def isHHMM(s):
            return s.isdigit() and len(s) == 4 and int(s[0:2]) < 24 and int(s[2:4]) < 60

        base, ext = splitext(fullname)
        if ext == self.TS:
            parts = base.split(' - ')
            if len(parts) > 1:
                t = parts[0]
                if len(t) == 8 and isDate(t[0:8]):
                        return "short"
                elif len(t) == 13 and isDate(t[0:8]) and t[8] == ' ' and isHHMM(t[9:13]):
                        return "long" if len(parts) >= 4 else "standard"
                else:
                    t = parts[-1]
                    if len(t) >= 14 and isDate(t[0:8]) and t[8] == ' ' and isHHMM(t[9:13]) and t[13] == '_':
                        return "event"
        return None

    def recSplit(self, fullname):
        nameType = self.recNameType(fullname)
        if nameType is None:
            return None, None, False, _("Can not extract show name for: %s") % fullname
        base = splitext(fullname)[0]
        parts = base.split(' - ')
        if nameType == "event":
            t = parts[-1]
            date_time = '.'.join((t[6:8], t[4:6], t[0:4])) + ' ' + t[9:11] + ':' + t[11:13]
            showname = parts[0]
        else:
            t = parts[0]
            showname = parts[1]
            date_time = '.'.join((t[6:8], t[4:6], t[0:4]))
            if nameType in ("standard", "long"):
                date_time += ' ' + t[9:11] + ':' + t[11:13]
                showname = parts[2]
        if base[-4:-3] == "_" and base[-3:].isdigit():
            date_time += '#' + base[-3:]
            if nameType != "event":
                showname = showname[0:-4]
        return showname, date_time, False, None


class Series2FolderActions(Series2FolderActionsBase):
    def __init__(self, session):
        super(Series2FolderActions, self).__init__(session)

    def doMoves(self, service=None, selectedOnly=False, serviceList=None):

        if Screens.Standby.inTryQuitMainloop:
            self.MsgBox(_("Your %s %s is trying to shut down. No recordings moved.") % (getMachineBrand(), getMachineName()), timeout=10)
            return

        if JobManager.getPendingJobs():
            self.MsgBox(_("Your %s %s is running tasks that may be accessing the recordings. No recordings moved.") % (getMachineBrand(), getMachineName()), timeout=10)
            return

        if _autoSeries2Folder and _autoSeries2Folder.isActive():
            self.MsgBox(_("Series to Folder is already running in the background."), timeout=10)
            return

        self.prepare(service, selectedOnly=selectedOnly, serviceList=serviceList)

        try:
            contents = os.listdir(self.rootdir)
        except Exception as ex:
            self.errMess.append("Can not process folder: %s" % str(ex))
            self.finish()
            return

        for f in contents:
            self.addRecording(f)

        # create a directory for each series and move shows into it
        # also add any single shows to existing series directories

        self.shows = sorted(self.shows.items())
        while self.shows:
            self.processRecording()

        self.updateCallerScreen()

        self.finish()

    def updateCallerScreen(self):
        fails = False
        if self.moves:
            for (dialog, action) in activeFileScreens(self.session, False):
                try:
                    getattr(dialog, action)()
                except Exception as e:
                    fails = True
                    pass
            if fails:
                msg = "Series2Folder doesn't know how to update some of your active file screens after moving recordings to folders.\nPlease refresh the screens manually."
                self.MsgBox(msg, msgType=MessageBox.TYPE_WARNING)
        return not fails

class Series2FolderAutoActions(Series2FolderActionsBase):

    ITER_STEP = 20  # ms Time to wait between search and processing steps
    START_DELAY = 2 * 60  # sec Delay time before first scan after restart
    TASK_DEFER = 1 * 60  # sec Defer time when task running
    FILESCREEN_DEFER = 1 * 60  # sec Defer time when in a file list screen
    TSRECORD_DEFER = 1 * 60  # sec Defer time when timeshift recording is active
    RECPLAYEND_DEFER = 5  # sec Defer time after a recording or playback ends
    RECPLAYENDACTIVE_DEFER = 1 * 60  # sec Defer time after a recording or playback ends while Series2FolderAutoActions is active

    def __init__(self, session):
        super(Series2FolderAutoActions, self).__init__(session)
        self.iterTimer = eTimer()
        self.iterTimer.callback.append(self.runStep)
        self.runTimer = eTimer()
        self.runTimer.callback.append(self.runMoves)
        self.nextRun = -1
        self.conf_autonotifications = config.plugins.seriestofolder.autonotifications.value

    def prepare(self, service):
        super(Series2FolderAutoActions, self).prepare(service)

        self.conf_autonotifications = config.plugins.seriestofolder.autonotifications.value

        # Listing of the recording directory
        self.dirList = []

    def autoStart(self):
        self.runTimer.stop()
        if self.gotRecordEvent not in NavigationInstance.instance.record_event:
            NavigationInstance.instance.record_event.append(self.gotRecordEvent)
        if self.gotPlayEvent not in NavigationInstance.instance.event:
            NavigationInstance.instance.event.append(self.gotPlayEvent)
        self.iterTimer.stop()
        self.runTimer.stop()
        self.runTimer.startLongTimer(self.START_DELAY)

    def autoStop(self):
        self.finish(stopping=True)
        self.__del__()

    def __del__(self):
        self.iterTimer.stop()
        self.runTimer.stop()
        if self.gotRecordEvent in NavigationInstance.instance.record_event:
            NavigationInstance.instance.record_event.remove(self.gotRecordEvent)
        if self.gotPlayEvent in NavigationInstance.instance.event:
            NavigationInstance.instance.event.remove(self.gotPlayEvent)

    def isActive(self):
        return self.iterTimer.isActive()

    def gotPlayEvent(self, event):
        if event == iPlayableService.evEnd:
            playing = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
            playing = playing and playing.valid() and playing.getPath() or ""
            if playing.startswith(self.rootdir):
                self.gotServiceEvent(event)

    def gotRecordEvent(self, record, event):
        if event == iRecordableService.evRecordStopped:
            self.gotServiceEvent(event)

    def gotServiceEvent(self, event):
        self.runTimer.stop()
        if self.isActive():
            self.runTimer.startLongTimer(self.RECPLAYENDACTIVE_DEFER)
        else:
            self.runTimer.startLongTimer(self.RECPLAYEND_DEFER)

    def runMoves(self):
        self.prepare(None)

        try:
            self.dirList = os.listdir(self.rootdir)
        except Exception as ex:
            self.dirList = []
            self.errMess.append("Can not process folder: %s" % str(ex))
            self.finish()
            return

        self.iterTimer.start(self.ITER_STEP, True)

    def runStep(self):
        if self.dirList or self.shows:
            defer = self.runWhen()
            if defer < 0:
                self.finish()
                return
            elif defer > 0:
                self.runTimer.stop()
                self.runTimer.startLongTimer(defer)
                return
            if self.dirList:
                self.addRecording(self.dirList.pop(0))
                if not self.dirList:
                    self.shows = sorted(self.shows.items())
                self.iterTimer.start(self.ITER_STEP, True)
            else:
                self.iterTimer.stop()
                if self.shows:
                    self.processRecording()
                if self.shows:
                    self.iterTimer.start(self.ITER_STEP, True)
                else:
                    self.finish()

    def runWhen(self):
        if Screens.Standby.inTryQuitMainloop:
            return -1
        if JobManager.getPendingJobs():
            return self.TASK_DEFER
        if activeFileScreens(self.session, True):
            return self.FILESCREEN_DEFER
        if config.timeshift.isRecording.value:
            return self.TSRECORD_DEFER
        return 0

    def finish(self, notification=True, stopping=False):
        self.iterTimer.stop()

        doNotification = {
            "all": not stopping,
            "error+move": self.moves or self.errMess,
            "error": self.errMess,
            "none": False,
        }[self.conf_autonotifications]

        if doNotification:
            super(Series2FolderAutoActions, self).finish(notification=notification, stopping=stopping)


class Series2Folder(ChoiceBox):
    def __init__(self, session, service, serviceList=None):
        list = [
            (ngettext("Move selected series recording to folder", "Move selected series recordings to folder", int(serviceList is None or len(serviceList))), "CALLFUNC", boundFunction(self.doMoves, selectedOnly=True, serviceList=serviceList), service),
            (_("Move series recordings to folders"), "CALLFUNC", self.doMoves, service),
            (_("Configure move series recordings to folders"), "CALLFUNC", self.doConfig),
        ]
        super(Series2Folder, self).__init__(session, _("Series to Folder actions"), list=list, selection=0)
        self.actions = Series2FolderActions(session)

    def doMoves(self, service, selectedOnly=False, serviceList=None):
        self.actions.doMoves(service, selectedOnly=selectedOnly, serviceList=serviceList)
        self.close()

    def doConfig(self, arg):
        self.session.open(Series2FolderConfig)


class ErrorBox(TextBox):
    skin = """<screen name="Series2Folder" backgroundColor="background" position="90,150" size="1100,450" title="Log">
        <widget font="Regular;18" name="text" position="0,4" size="1100,446"/>
</screen>"""

class Series2FolderConfig(ConfigListScreen, Screen):
    skin = """
<screen name="Series2FolderConfig" position="center,center" size="640,376" title="Configure Series To Folder" >
    <widget name="config" position="20,10" size="600,250" />
    <widget name="description" position="20,e-106" size="600,66" font="Regular;18" foregroundColor="grey" halign="left" valign="top" />
    <ePixmap name="red" position="20,e-28" size="15,16" pixmap="skin_default/buttons/button_red.png" alphatest="blend" />
    <ePixmap name="green" position="170,e-28" size="15,16" pixmap="skin_default/buttons/button_green.png" alphatest="blend" />
    <widget source="VKeyIcon" position="470,e-28" size="15,16" render="Pixmap" pixmap="skin_default/buttons/button_blue.png" alphatest="blend" zPosition="1" >
        <convert type="ConditionalShowHide" />
    </widget>
    <widget name="key_red" position="40,e-30" size="150,25" valign="top" halign="left" font="Regular;20" />
    <widget name="key_green" position="190,e-30" size="150,25" valign="top" halign="left" font="Regular;20" />
    <widget name="key_yellow" position="340,e-30" size="150,25" valign="top" halign="left" font="Regular;20" />
    <widget source="VKeyIcon" position="490,e-30" size="150,25" render="FixedLabel" text="%s" valign="top" halign="left" font="Regular;20" >
        <convert type="ConditionalShowHide" />
    </widget>
    <widget name="HelpWindow" conditional="HelpWindow" position="0,0" size="1,1" transparent="1" alphatest="on"/>
</screen>""" % _("Keyboard")

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        self["description"] = Label()
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("Save"))
        self["key_yellow"] = Label()
        self["VKeyIcon"] = Boolean(False)
        self.list = []
        self.noShowHelp = True

        if self.__layoutFinished not in self.onLayoutFinish:
            self.onLayoutFinish.append(self.__layoutFinished)

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
            _("Repeat tag to strip"),
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

        self._confAuto = getConfigListEntry(
            _("Allow Series to Folder to run in the background"),
            config.plugins.seriestofolder.auto,
            _("If enabled, Series to Folder will run automatically in the background shortly after startup and after each recording finishes.")
        )

        self._confAutoNotifications = getConfigListEntry(
            _("Series to Folder notifications"),
            config.plugins.seriestofolder.autonotifications,
            _("Configure which notification popups will be shown by Series to Folder when run in the background")
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

        if self.noShowHelp:
            self["HelpWindow"] = Label()

    def createConfig(self, configList):
        list = []
        disabled = []

        def addConditional(cond, item):
            (list if cond[1].value else disabled).append(item)

        list += [
            self._confShowmovebutton,
            self._confShowselmovebutton,
            self._confAutofolder,
            self._confStripRepeats,
        ]
        addConditional(self._confStripRepeats, self._confRepeatStr)
        list += [
            self._confPortableNames,
            self._confMovies,
        ]
        addConditional(self._confMovies, self._confMoviesfolder)
        list.append(self._confAuto)
        addConditional(self._confAuto, self._confAutoNotifications)

        self.list = list
        configList.list = list
        configList.l.setList(list)

        self.noShowHelp = False
        for confItem in list + disabled:
            if isinstance(confItem[1], ConfigText) and (not hasattr(confItem[1], "show_help") or confItem[1].show_help):
                self.noShowHelp = True
                break

    def updateConfig(self):
        currConf = self["config"].getCurrent()
        if currConf in (self._confStripRepeats, self._confMovies, self._confAuto):
            self.createConfig(self["config"])

    def __layoutFinished(self):
        self.title += " v" + __version__
        screen_size = self.session.desktop.size()
        if self.noShowHelp:
                self["HelpWindow"].instance.move(ePoint(screen_size.width(), screen_size.height()))

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
