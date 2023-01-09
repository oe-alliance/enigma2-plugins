"""
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
"""
from Components.EpgList import EPGList
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN
from MovieScanner import movieScanner
IMAGE_PATH = 'Extensions/AdvancedMovieSelection/images/'
av1_pixmap = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + 'movie.png'))
av2_pixmap = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + 'blue_movieicon.png'))
savedPixmapForEntry = EPGList.getPixmapForEntry
savedBuildSingleEntry = EPGList.buildSingleEntry
savedBuildMultiEntry = EPGList.buildMultiEntry
savedBuildSimilarEntry = EPGList.buildSimilarEntry


def getPixmapForEntry(self, service, eventId, beginTime, duration):
    pixmap = savedPixmapForEntry(self, service, eventId, beginTime, duration)
    icon_index = epgListExtension.isMovieRecorded()
    if pixmap[0] == None and icon_index > 0:
        if icon_index == 2:
            return (av2_pixmap, 1)
        return (av1_pixmap, 1)
    return pixmap


def buildSingleEntry(self, service, eventId, beginTime, duration, EventName):
    epgListExtension.current_name = EventName
    return savedBuildSingleEntry(self, service, eventId, beginTime, duration, EventName)


def buildMultiEntry(self, changecount, service, eventId, beginTime, duration, EventName, nowTime, service_name):
    epgListExtension.current_name = EventName
    return savedBuildMultiEntry(self, changecount, service, eventId, beginTime, duration, EventName, nowTime, service_name)


def buildSimilarEntry(self, service, eventId, beginTime, service_name, duration):
    return savedBuildSimilarEntry(self, service, eventId, beginTime, service_name, duration)


class EPGListExtension:

    def __init__(self):
        self.current_name = ''

    def setEnabled(self, enabled):
        print('[AdvancedMovieSelection] Set epg extension: %s' % str(enabled))
        if enabled:
            EPGList.getPixmapForEntry = getPixmapForEntry
            EPGList.buildSingleEntry = buildSingleEntry
            EPGList.buildMultiEntry = buildMultiEntry
        else:
            EPGList.getPixmapForEntry = savedPixmapForEntry
            EPGList.buildSingleEntry = savedBuildSingleEntry
            EPGList.buildMultiEntry = savedBuildMultiEntry

    def isMovieRecorded(self):
        return movieScanner.isMovieRecorded(self.current_name)

    def timerStateChanged(self, timer):
        movieScanner.timerStateChanged(timer)


epgListExtension = EPGListExtension()
