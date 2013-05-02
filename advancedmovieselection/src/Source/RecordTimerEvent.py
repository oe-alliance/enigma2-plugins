#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright (C) 2012 cmikula

In case of reuse of this source code please do not remove this copyright.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    For more information on the GNU General Public License see:
    <http://www.gnu.org/licenses/>.

For example, if you distribute copies of such a program, whether gratis or for a fee, you 
must pass on to the recipients the same freedoms that you received. You must make sure 
that they, too, receive or can get the source code. And you must show them these terms so they know their rights.
'''
from Globals import printStackTrace

class RecordTimerEvent():
    def __init__(self):
        self.on_state_changed = []
        import NavigationInstance
        if not self.timerStateChanged in NavigationInstance.instance.RecordTimer.on_state_change:
            NavigationInstance.instance.RecordTimer.on_state_change.append(self.timerStateChanged)

    def appendCallback(self, callback):
        if not callback in self.on_state_changed:
            self.on_state_changed.append(callback)

    def removeCallback(self, callback):
        if callback in self.on_state_changed:
            self.on_state_changed.remove(callback)

    def timerStateChanged(self, timer):
        try:
            print "[AdvancedMovieSelection] timer state changed event"
            print str(timer.justplay), str(timer.cancelled), str(timer.state) 
            if timer.justplay:
                print "[AdvancedMovieSelection] cancel justplay event"
                return
            if not hasattr(timer, 'Filename'):
                print "[AdvancedMovieSelection] cancel timer state changed, no Filename in timer event"
                return
            for callback in self.on_state_changed:
                callback(timer)
        except:
            printStackTrace()

recordTimerEvent = RecordTimerEvent()

from Components.config import config

class CoverLoader():
    def __init__(self):
        recordTimerEvent.appendCallback(self.timerStateChanged)

    def timerStateChanged(self, timer):
        if not config.AdvancedMovieSelection.cover_auto_download.value:
            return
        from timer import TimerEntry
        print "[AdvancedMovieSelection] RecordTimerEvent:", str(timer.state), str(timer.cancelled), timer.Filename
        if timer.state == TimerEntry.StateEnded and not timer.cancelled:
            from thread import start_new_thread
            start_new_thread(self.downloadMovieInfo, (timer.name, timer.Filename + ".ts"))

    def downloadMovieInfo(self, name, filename=None):
        from MovieDB import tmdb
        from EventInformationTable import createEIT
        print "[AdvancedMovieSelection] RecordTimerEvent, loading info from tmdb:", name
        results = tmdb.search(name)
        if results and len(results) > 0:
            searchResult = results[0]
            movie = tmdb.getMovieInfo(searchResult['id'])
            createEIT(filename, name, config.AdvancedMovieSelection.coversize.value, movie)

coverLoader = CoverLoader()
