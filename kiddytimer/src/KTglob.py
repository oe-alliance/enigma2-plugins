from __future__ import absolute_import
from .__init__ import _
from Components.config import config
import time

PLUGIN_BASE = "KiddyTimer"
PLUGIN_VERSION = "1.3"

DAYNAMES = (_("Sunday"),
          _("Monday"),
          _("Tuesday"),
          _("Wednesday"),
          _("Thursday"),
          _("Friday"),
          _("Saturday"),
          )

ONEHOUR = 3600
ONEMINUTE = 60

MOVEPOSITIONSTEP = 10


#This is a hack to get the times in the current timezone to feed as default value for the ConfigClock
ONEOCLOCK = time.mktime([2000, 1, 1, 1, 0, 0, 5, 1, time.timezone])
FOUROCLOCK = time.mktime([2000, 1, 1, 4, 0, 0, 5, 1, time.timezone])
EIGHTOCLOCK = time.mktime([2000, 1, 1, 8, 0, 0, 5, 1, time.timezone])
EIGHTOCLOCKNOON = time.mktime([2000, 1, 1, 20, 0, 0, 5, 1, time.timezone])

plugin_path = ""

##############################################################################

SKIN = """
    <screen flags="wfNoBorder" position="0,0" size="82,104" title="Kiddy Timer" backgroundColor="#ff000000">
        <ePixmap pixmap="~/img/Smiley-Background.png" position="0,0" zPosition="1" size="82,82" alphatest="blend" transparent="1"/>
        <widget name="TimerSlider" pixmap="~/img/Smiley-Slider.png" zPosition="4" position="0,0" size="82,82" transparent="1" orientation="orBottomToTop" />
        <widget name="TimerSliderText" zPosition="5" position="0,83" size="82,21" font="Regular;18" halign="center" valign="center" foregroundColor="#000000" backgroundColor="#aaffffff" />
        <widget name="TimerGraph" pixmaps="~/img/Timer1000.png,~/img/Timer0950.png,~/img/Timer0900.png,~/img/Timer0850.png,~/img/Timer0800.png,~/img/Timer0750.png,~/img/Timer0700.png,~/img/Timer0650.png,~/img/Timer0600.png,~/img/Timer0550.png,~/img/Timer0500.png,~/img/Timer0450.png,~/img/Timer0400.png,~/img/Timer0350.png,~/img/Timer0300.png,~/img/Timer0250.png,~/img/Timer0200.png,~/img/Timer0150.png,~/img/Timer0100.png,~/img/Timer0050.png,~/img/Timer0000.png" position="0,0" zPosition="2" size="82,82" transparent="1" alphatest="on" />
        <widget name="TimerText" zPosition="3" position="0,30" size="82,21" font="Regular;18" halign="center" valign="center" foregroundColor="#000000" transparent = "1" />
        <widget name="TimerTransparent" pixmap="~/img/Transparent.png" zPosition="2" position="0,0" size="82,82" transparent="1" alphatest="off" />
        <widget name="TimerTransparentText" zPosition="3" position="0,30" size="82,21" font="Regular;18" halign="center" valign="center" foregroundColor="#000000" backgroundColor="#aaffffff" />
    </screen>"""

##############################################################################


def getTodaysTimeInSeconds():
    # Number of the current day
    dayNr = int(time.strftime("%w", time.localtime()))
    # Number of seconds for the current day
    iDayTime = getSecondsFromClock(config.plugins.KiddyTimer.dayTimes[dayNr].timeValue.value)
    return(iDayTime)


def getSecondsFromClock(aClock):
    iSeconds = 60 * (int(aClock[0]) * 60 + int(aClock[1]))
    return iSeconds


def getTimeFromSeconds(iSecondsLeft, bReturnSeconds):
        iHours = int(iSecondsLeft // 3600)
        iHourRest = iSecondsLeft - (iHours * 3600)
        iMinutes = int(iHourRest // 60)
        if bReturnSeconds == False:
            return(("00" + str(iHours))[-2:] + ":" + ("00" + str(iMinutes))[-2:])
        else:
            iSeconds = int(iHourRest - (iMinutes * 60))
            return(("00" + str(iHours))[-2:] + ":" + ("00" + str(iMinutes))[-2:] + ":" + ("00" + str(iSeconds))[-2:])

    
