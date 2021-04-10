from __future__ import print_function
from Plugins.Extensions.NETcaster.StreamInterface import StreamInterface
from Plugins.Extensions.NETcaster.StreamInterface import Stream
from Screens.ChoiceBox import ChoiceBox


class Interface(StreamInterface):
    name = "listen to SHOUTcast Streams"
    nameshort = "SHOUTcast"
    description = "This is a Plugin to browse www.shoutcast.com and listen to webradios listed there."

    def __init__(self, session, cbListLoaded=None):
        StreamInterface.__init__(self, session, cbListLoaded=cbListLoaded)
        self.genrefeed = GenreFeed()
    
    def getList(self):
        glist = []
        #self.genrefeed.fetch_genres()
        self.genrefeed.parse_genres()
        for i in self.genrefeed.genre_list:            
            glist.append((str(i), i))
        self.session.openWithCallback(self.GenreSelected, ChoiceBox, _("select Genre to search for streams"), glist)

    def GenreSelected(self, selectedGenre):
        if selectedGenre is not None:
            feed = ShoutcastFeed(selectedGenre[1])
            #feed.fetch_stations()
            feed.parse_stations()
            self.list = []
            for station in feed.station_list:
                stream = Stream(str(station['Name']), "Bitrate: " + str(station['Bitrate']) + ", Type: " + str(station['MimeType']), str(station['PLS_URL']), type="pls")
                self.list.append(stream)
        self.OnListLoaded()

####################################################
# feeds.py - Gets the current listings of Shoutcast stations
# $Id$
# Copyright (C) 2005-2006 Matthew Schick <matt@excentral.org>

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


from six.moves.urllib.request import FancyURLopener
from xml.sax import parseString
from xml.sax.handler import ContentHandler
from os import stat, mkdir
from os.path import dirname, isdir
import time
from stat import ST_MTIME

from six.moves.cPickle import dump, load


tmpxml = 'shout.xml'
DEBUG = 0


def write_cache(cache_file, cache_data):
    """
    Does a cPickle dump
    """
    if not isdir(dirname(cache_file)):
        try:
            mkdir(dirname(cache_file))
        except OSError:
            print(dirname(cache_file), 'is a file')
    fd = open(cache_file, 'wb')
    dump(cache_data, fd, -1)
    fd.close()


def cacheTime(cache_file):
    """
    Returns None if no cache file, its MTIME otherwise
    """
    try:
        mtime = stat(cache_file)[ST_MTIME]
    except:
        return None
    return mtime


def load_cache(cache_file):
    """
    Does a cPickle load
    """
    fd = open(cache_file, 'rb')
    cache_data = load(fd)
    fd.close()
    return cache_data


class StationParser(ContentHandler):
    """
    SAX handler for xml feed, not for public consumption
    """

    def __init__(self, min_bitrate):
        self.isStationList = False
        self.isTuneIn = False
        self.isStation = False
        self.station_list = []
        self.min_bitrate = min_bitrate
        self.mimeType = ''
        self.Id = ''
        self.Name = ''
        self.Bitrate = ''
        self.nowPlaying = ''
        self.Listeners = ''
        self.stationUrl = ''
        self.Genre = ''
        self.count = 0
        self.shoutUrl = 'http://www.shoutcast.com'

    def startElement(self, name, attrs):
        if name == 'stationlist':
            self.isStationList = True
        if name == 'tunein':
            self.isTuneIn = True
            self.baseUrl = attrs.get('base', None)
        if name == 'station':
            self.isStation = True
            self.Name = attrs.get('name', None)
            self.mimeType = attrs.get('mt', None)
            self.Id = attrs.get('id', None)
            self.Bitrate = attrs.get('br', None)
            self.nowPlaying = attrs.get('ct', None)
            self.Listeners = attrs.get('lc', None)
            self.Genre = attrs.get('genre', None)

    def endElement(self, name):
        if name == 'station':
            self.isStation = False
        if name == 'tunein':
            self.isTuneIn = False
        if name == 'station':
            self.isStation = False
            if int(self.Bitrate) >= self.min_bitrate:
                self.stationUrl = self.shoutUrl + self.baseUrl + '?id=' + self.Id
                self.station_list.append({'Name': self.Name.encode("utf-8"), 'PLS_URL': self.stationUrl.encode("utf-8"), 'NowPlaying': self.nowPlaying.encode("utf-8"), 'Listeners': self.Listeners.encode("utf-8"), 'Bitrate': self.Bitrate.encode("utf-8"), 'MimeType': self.mimeType.encode("utf-8"), 'Genres': self.Genre.encode("utf-8")})
                self.count += 1
        if name == 'stationlist':
            self.isStationList = False
            if DEBUG == 1:
                print('Parsed ', self.count, ' stations')


class GenreParse(ContentHandler):
    def __init__(self):
        self.isGenre = False
        self.isGenreList = False
        self.genreList = []

    def startElement(self, name, attrs):
        if name == 'genrelist':
            self.isGenreList = True
        if name == 'genre':
            self.isGenre == True
            self.genre_name = attrs.get('name', None)

    def endElement(self, name):
        if name == 'genre':
            self.isGenre = False
            self.genreList.append(self.genre_name.encode("utf-8"))
        if name == 'genrelist':
            self.isGenreList = False


class GenreFeed:
    def __init__(self, cache_ttl=3600, cache_dir='/tmp/pyshout_cache'):
        self.cache_ttl = cache_ttl
        self.cache_file = cache_dir + '/genres.cache'
    self.genre_list = ['Sorry, failed to load', '...try again later', 'Rock', 'Pop', 'Alternative']

    def fetch_genres(self):
        """
        Grabs genres and returns tuple of genres
        """
        self.genre_url = 'http://www.shoutcast.com/sbin/newxml.phtml'
        self.urlhandler = FancyURLopener()
        self.fd = self.urlhandler.open(self.genre_url)
        self.genre = self.fd.read()
        self.fd.close()
        return self.genre

    def parse_genres(self):
        ct = None
        if self.cache_ttl:
            ct = cacheTime(self.cache_file)
            try:
                self.genre_list = load_cache(self.cache_file)
            except:
                ct = None
        if not ct or (time.time() - ct) > self.cache_ttl:
            if DEBUG == 1:
                print('Getting fresh feed')
            try:
                parseXML = GenreParse()
                self.genres = self.fetch_genres()
                parseString(self.genres, parseXML)
                self.genre_list = parseXML.genreList
                write_cache(self.cache_file, self.genre_list)
            except:
                print("Failed to get genres from server, sorry.")
        return self.genre_list


class ShoutcastFeed:
    def __init__(self, genre, min_bitrate=128, cache_ttl=600, cache_dir='/tmp/pyshout_cache'):
        """
        Parses the xml feed and spits out a list of dictionaries with the station info
        keyed by genre. Params are as follows:
        min_bitrate - 128 default, Minimum bitrate filter
        cache_ttl - 600 default, 0 disables, Seconds cache is considered valid
        cache_dir - /tmp/pyshout_cache default, Path to cache directory
        """
        self.min_bitrate = min_bitrate
        self.cache_ttl = cache_ttl
        self.genre = genre
        self.cache_file = cache_dir + '/' + self.genre + '.pickle'
        self.station_list = []

    def fetch_stations(self):
        """
        Grabs the xml list of stations from the shoutcast server
        """
        self.shout_url = 'http://www.shoutcast.com/sbin/newxml.phtml?genre=' + self.genre
        self.urlhandler = FancyURLopener()
        self.fd = self.urlhandler.open(self.shout_url)
        self.stations = self.fd.read()
        self.fd.close()
        return self.stations

    def parse_stations(self):
        ct = None
        if self.cache_ttl:
            ct = cacheTime(self.cache_file)
        if ct:
            try:
                self.station_list = load_cache(self.cache_file)
            except:
            	print("Failed to load cache.")
        if not ct or (time.time() - ct) > self.cache_ttl:
            try:
                parseXML = StationParser(self.min_bitrate)
                self.stations = self.fetch_stations()
                parseString(self.stations, parseXML)
                self.station_list = parseXML.station_list
                write_cache(self.cache_file, self.station_list)
            except:
            	print("Failed to get a new station list, sorry.")
        return self.station_list
