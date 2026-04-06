import math

# for localized messages
from . import _

# GUI (Screens)
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Notifications import AddPopup

# Timer
from enigma import eTimer

# For monitoring
from enigma import iPlayableService
from Components.ServiceEventTracker import ServiceEventTracker

# Get remaining time if timer is already active
from time import time

# Get event for monitoring
from enigma import eEPGCache

# Config
from Components.config import config


class WerbeZapperChoiceBox(ChoiceBox):
    def __init__(
        self,
        session,
        title="",
        list=None,
        keys=None,
        selection=0,
        zap_time=0,
        zap_service=None,
        monitored_event=None,
        monitored_service=None,
        skin_name=None,
    ):
        if list is None:
            list = []
        if skin_name is None:
            skin_name = []

        ChoiceBox.__init__(self, session, title, list, keys, selection, skin_name)

        self.update_timer = eTimer()
        self.update_timer.callback.append(self.update)

        self.zap_time = zap_time
        self.zap_service = zap_service
        self.monitored_event = monitored_event
        self.monitored_service = monitored_service

        self.update_timer.start(1000)
        self.setTitle("WerbeZapper")
        self.update()

    def update(self):
        text = ""
        if self.monitored_event:
            name = self.monitored_event.getEventName()
            remaining = int(self.monitored_event.getDuration() - (time() - self.monitored_event.getBeginTime()))
            if remaining > 0:
                text += _("Monitoring: %s (%d:%02d Min)") % (name, remaining // 60, remaining % 60)
        if self.zap_time:
            remaining = int(math.floor(self.zap_time - time()))
            if remaining > 0:
                text += "\n" + _("Zapping back in %d:%02d Min") % (remaining // 60, remaining % 60)
        if text:
            self.setText(text)

    def setText(self, text):
        self["text"].setText(text)

    def close(self, param=None):
        self.update_timer.stop()
        ChoiceBox.close(self, param)


class WerbeZapper(Screen):
    """Simple Plugin to automatically zap back to a Service after a given amount of time."""

    def __init__(self, session, servicelist, cleanupfnc=None):
        Screen.__init__(self, session)

        self.session = session
        self.servicelist = servicelist

        self.zap_time = None
        self.zap_timer = eTimer()
        self.zap_timer.callback.append(self.zap)

        self.monitor_timer = eTimer()
        self.monitor_timer.callback.append(self.stopMonitoring)

        self.delay_timer = eTimer()
        self.delay_timer.callback.append(self.zappedAway)

        self.zap_service = None
        self.move_service = None
        self.root = None

        self.monitored_service = None
        self.monitored_event = None
        self.__event_tracker = None

        self.cleanupfnc = cleanupfnc

    def showSelection(self):
        title = _("When to Zap back?")
        select = int(config.werbezapper.duration.value)
        keys = []

        choices = [
            (_("Custom"), "custom"),
            ("1 " + _("minute"), 1),
            ("2 " + _("minutes"), 2),
            ("3 " + _("minutes"), 3),
            ("4 " + _("minutes"), 4),
            ("5 " + _("minutes"), 5),
            ("6 " + _("minutes"), 6),
            ("7 " + _("minutes"), 7),
            ("8 " + _("minutes"), 8),
            ("9 " + _("minutes"), 9),
        ]
        keys.extend(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])

        choices.append(("------", "close"))
        keys.append("")

        if self.monitor_timer.isActive():
            choices.append((_("Stop monitoring"), "stopmonitoring"))
        else:
            choices.append((_("Start monitoring"), "startmonitoring"))
        keys.append("blue")

        if self.zap_timer.isActive():
            if self.zap_time:
                remaining = int(math.floor(self.zap_time - time()))
                remaining = remaining if remaining > 0 else 0
                remaining //= 60
                select = remaining if 0 < remaining < 10 else select
            choices.append((_("Stop timer"), "stoptimer"))
            keys.append("red")
        else:
            choices.append(("------", "close"))
            keys.append("")

        if self.zap_timer.isActive():
            choices.append((_("Rezap"), "rezap"))
            keys.append("green")
        else:
            choices.append(("------", "close"))
            keys.append("")

        self.session.openWithCallback(
            self.choicesCallback,
            WerbeZapperChoiceBox,
            title,
            choices,
            keys,
            select,
            self.zap_time,
            self.zap_service,
            self.monitored_event,
            self.monitored_service,
        )

    def choicesCallback(self, result):
        result = result and result[1]

        if result == "custom":
            from Screens.InputBox import InputBox
            from Components.Input import Input

            self.session.openWithCallback(
                self.inputCallback,
                InputBox,
                title=_("How many minutes to wait until zapping back?"),
                text="10",
                maxSize=False,
                type=Input.NUMBER,
            )
            return

        if result == "startmonitoring":
            self.startMonitoring()
        elif result == "stopmonitoring":
            self.stopMonitoring()
        elif result == "rezap":
            self.stopTimer()
            self.zap()
        elif result == "stoptimer":
            self.stopTimer()
        elif result == "reopen":
            self.showSelection()
        elif result == "close":
            pass
        elif isinstance(result, int):
            self.startTimer(result)

        self.cleanup()

    def inputCallback(self, result):
        if result is not None:
            self.startTimer(int(result))
        else:
            self.cleanup()

    def startMonitoring(self, notify=True):
        self.stopTimer()

        service = self.session.nav.getCurrentService()
        ref = self.session.nav.getCurrentlyPlayingServiceReference()
        self.monitored_service = ref

        if not self.__event_tracker:
            self.__event_tracker = ServiceEventTracker(
                screen=self,
                eventmap={
                    iPlayableService.evStart: self.serviceStarted,
                },
            )

        info = service and service.info()
        event = info and info.getEvent(0)
        if not event:
            epg = eEPGCache.getInstance()
            event = ref and ref.valid() and epg.lookupEventTime(ref, -1)
        if event:
            self.monitored_event = event
            duration = int(event.getDuration() - (time() - event.getBeginTime()))
            if duration > 0:
                self.monitor_timer.startLongTimer(duration)
            if notify:
                name = event.getEventName()
                AddPopup(
                    _("WerbeZapper\nMonitoring started\n%s") % (name),
                    MessageBox.TYPE_INFO,
                    3,
                    "WerbeZapperMonitoringStarted",
                )
        else:
            if notify:
                AddPopup(
                    _("WerbeZapper\nMonitoring started unlimited\nHas to be deactivated manually"),
                    MessageBox.TYPE_INFO,
                    10,
                    "WerbeZapperMonitoringStartedUnlimited",
                )

    def stopMonitoring(self, notify=True):
        self.stopTimer()
        self.monitor_timer.stop()

        if notify:
            name = self.monitored_event and self.monitored_event.getEventName()
            AddPopup(
                _("WerbeZapper\nMonitoring ends\n%s") % (name),
                MessageBox.TYPE_INFO,
                3,
                "WerbeZapperMonitoringStopped",
            )

        self.monitored_service = None
        self.monitored_event = None

    def serviceStarted(self):
        if self.monitor_timer.isActive() and not self.zap_timer.isActive() and not self.delay_timer.isActive():
            self.delay_timer.startLongTimer(3)

    def zappedAway(self):
        ref = self.session.nav.getCurrentlyPlayingServiceReference()
        if ref and self.monitored_service != ref:
            self.startTimer(zapto=self.monitored_service)

    def startTimer(self, duration=0, notify=True, zapto=None):
        if duration > 0:
            config.werbezapper.duration.value = duration
            config.werbezapper.duration.save()
        else:
            duration = int(config.werbezapper.duration.value)

        self.zap_service = zapto or self.session.nav.getCurrentlyPlayingServiceReference()
        self.move_service = None if zapto else self.servicelist.getCurrentSelection()
        self.root = self.servicelist.getRoot()

        self.zap_time = time() + (duration * 60)
        self.zap_timer.startLongTimer(int(duration * 60))

        if notify:
            AddPopup(
                _("Zapping back in %d Minute(s)") % (duration),
                MessageBox.TYPE_INFO,
                3,
                "WerbeZapperZapStarted",
            )

    def stopTimer(self):
        self.zap_timer.stop()
        self.zap_time = None

    def zap(self, notify=True):
        if self.zap_service is not None:
            if self.root:
                import ServiceReference

                if not self.servicelist.preEnterPath(str(ServiceReference.ServiceReference(self.root))):
                    if self.servicelist.isBasePathEqual(self.root):
                        self.servicelist.pathUp()
                        self.servicelist.enterPath(self.root)
                    else:
                        currentRoot = self.servicelist.getRoot()
                        if currentRoot is None or currentRoot != self.root:
                            self.servicelist.clearPath()
                            self.servicelist.enterPath(self.root)

            if self.move_service:
                self.servicelist.setCurrentSelection(self.move_service)
                self.servicelist.zap()

            self.session.nav.playService(self.zap_service)

        if notify:
            AddPopup(
                _("Zapping back"),
                MessageBox.TYPE_INFO,
                3,
                "WerbeZapperZapBack",
            )

        if not self.monitor_timer.isActive():
            self.zap_service = None
            self.move_service = None
            self.root = None

    def cleanup(self):
        if (
            self.monitor_timer
            and not self.monitor_timer.isActive()
            and self.zap_timer
            and not self.zap_timer.isActive()
        ):
            if self.cleanupfnc:
                self.cleanupfnc()

    def shutdown(self):
        if self.zap_timer is not None:
            self.zap_timer.callback.remove(self.zap)
            self.zap_timer = None
        if self.monitor_timer is not None:
            self.monitor_timer.callback.remove(self.stopMonitoring)
            self.monitor_timer = None
        if self.delay_timer is not None:
            self.delay_timer.callback.remove(self.zappedAway)
            self.delay_timer = None
