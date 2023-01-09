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
from __future__ import print_function
__author__ = 'cmikula'
__version__ = '1.0'
config = None


def setLocale(lng):
    global config
    print('[AdvancedMovieSelection] Set tvdb locale to', lng)
    config = {}
    config['locale'] = lng
    config['apikey'] = '7E9EC2ECC1B1EB3A'
    config['urls'] = {}
    config['urls']['movie.search'] = 'http://www.thetvdb.com/api/GetSeries.php?seriesname=%%s' % config
    config['urls']['movie.getInfo'] = 'http://www.thetvdb.com/api/%(apikey)s/series/%%s/all/%(locale)s.xml' % config
    config['urls']['movie.getImage'] = 'http://www.thetvdb.com/banners/_cache/%%s' % config


def getLocale():
    return config['locale']


from six.moves.urllib.request import urlopen
from six.moves.urllib.parse import quote
import xml.etree.cElementTree as ElementTree


class TvdBaseError(Exception):
    pass


class TvdNoResults(TvdBaseError):
    pass


class TvdHttpError(TvdBaseError):
    pass


class TvdXmlError(TvdBaseError):
    pass


class XmlHandler:
    """Deals with retrieval of XML files from API"""

    def __init__(self, url):
        self.url = url

    def _grabUrl(self, url):
        try:
            urlhandle = urlopen(url)
        except IOError as errormsg:
            raise TvdHttpError(errormsg)

        if urlhandle.code >= 400:
            raise TvdHttpError('HTTP status code was %d' % urlhandle.code)
        return urlhandle.read()

    def getEt(self):
        xml = self._grabUrl(self.url)
        try:
            et = ElementTree.fromstring(xml)
        except SyntaxError as errormsg:
            raise TvdXmlError(errormsg)

        return et


class SearchResults(list):
    """Stores a list of Movie's that matched the search"""

    def __repr__(self):
        return '<Search results: %s>' % list.__repr__(self)


class MovieResult(dict):
    """A dict containing the information about a specific search result"""

    def __repr__(self):
        return '<MovieResult: %s (%s)>' % (self.get('name'), self.get('released'))

    def info(self):
        """Performs a MovieDb.getMovieInfo search on the current id, returns
        a Movie object
        """
        cur_id = self['id']
        info = MovieDb().getMovieInfo(cur_id)
        return info


class Serie(dict):
    """A dict containing the information about the serie"""

    def __repr__(self):
        return '<SerieResult: %s (%s)>' % (self.get('SeriesName'), self.get('Genre'))


class Episodes(list):
    """A dict containing the information about the episode"""

    def __repr__(self):
        return '<EpisodeResult: %s (%s)>' % (self.get('EpisodeName'), self.get('EpisodeNumber'))


class Episode(dict):
    """A dict containing the information about the episode"""

    def __repr__(self):
        return '<EpisodeResult: %s (%s)>' % (self.get('EpisodeName'), self.get('EpisodeNumber'))


class MovieDb:

    def addImage(self, current, item):
        if item.text:
            if item.tag.lower() == 'poster':
                current[item.tag.lower()] = config['urls']['movie.getImage'] % item.text
            elif item.tag.lower() == 'banner':
                current[item.tag.lower()] = config['urls']['movie.getImage'] % item.text
            elif item.tag.lower() == 'fanart':
                current[item.tag.lower()] = config['urls']['movie.getImage'] % item.text
            else:
                return False
            return True
        else:
            return False

    def _parseSearchResults(self, movie_element):
        cur_movie = MovieResult()
        for item in movie_element.getchildren():
            if self.addImage(cur_movie, item):
                pass
            else:
                cur_movie[item.tag] = item.text

        return cur_movie

    def _parseSeries(self, element):
        cur_serie = Serie()
        for item in element.getchildren():
            if self.addImage(cur_serie, item):
                pass
            elif item.tag == 'Actors' and item.text and item.text.startswith('|'):
                cur_serie[item.tag] = item.text[1:-1].split('|')
            elif item.tag == 'Genre' and item.text and item.text.startswith('|'):
                cur_serie[item.tag] = item.text[1:-1].split('|')
            else:
                cur_serie[item.tag] = item.text

        return cur_serie

    def _parseEpisode(self, element):
        curr = Episode()
        for item in element.getchildren():
            if item.tag.lower() == 'filename' and item.text:
                curr[item.tag.lower()] = config['urls']['movie.getImage'] % item.text
            elif item.tag == 'Director' and item.text and item.text.startswith('|'):
                curr[item.tag] = item.text[1:-1].split('|')
            else:
                curr[item.tag] = item.text

        return curr

    def search(self, title):
        """Searches for a film by its title.
        Returns SearchResults (a list) containing all matches (Movie instances)
        """
        title = quote(title.encode('utf-8'))
        url = config['urls']['movie.search'] % title
        etree = XmlHandler(url).getEt()
        search_results = SearchResults()
        for cur_result in etree.findall('Series'):
            cur_movie = self._parseSearchResults(cur_result)
            search_results.append(cur_movie)

        return search_results

    def getMovieInfo(self, _id):
        """Returns movie info by it's thetvdb ID.
        Returns a Movie instance
        """
        url = config['urls']['movie.getInfo'] % _id
        etree = XmlHandler(url).getEt()
        serie = Serie()
        serie['Serie'] = []
        serie['Episode'] = []
        seriesTree = etree.findall('Series')
        episodeTree = etree.findall('Episode')
        if len(seriesTree) == 0 or len(episodeTree) == 0:
            raise TvdNoResults('No results for id %s' % _id)
        for cur_result in seriesTree:
            cur_movie = self._parseSeries(cur_result)
            serie['Serie'].append(cur_movie)

        for cur_result in etree.findall('Episode'):
            cur_movie = self._parseEpisode(cur_result)
            serie['Episode'].append(cur_movie)

        return serie


def search(name):
    mdb = MovieDb()
    return mdb.search(name)


def getMovieInfo(series_id):
    mdb = MovieDb()
    return mdb.getMovieInfo(series_id)


def printKey(item, key):
    if item[key] is not None:
        print(key + ':', item[key])


def searchEpisode(episodes, episode_name):
    for episode in episodes:
        ep_name = episode['EpisodeName']
        if ep_name:
            ep_name = ep_name.encode('utf-8', 'ignore')
            if ep_name.lower() == episode_name.lower():
                return episode


def main():
    setLocale('de')
    results = search('Law & Order')
    for searchResult in results:
        print(searchResult['SeriesName'])
        print(searchResult['Overview'])
        print(searchResult['banner'])
        movie = getMovieInfo(searchResult['id'])
        serie = movie['Serie'][0]
        print()
        print(serie)
        print(serie['SeriesName'])
        print(serie['Overview'])
        print(serie['Rating'])
        print(serie['Runtime'])
        if serie['Genre']:
            print(' ,'.join(serie['Genre']))
        if serie['Actors']:
            print(' ,'.join(serie['Actors']))
        print(serie['poster'])
        print(serie['banner'])
        print(serie['fanart'])
        epi = searchEpisode(movie['Episode'], 'Die Wunderdoktorin')
        print(epi)
        for episode in movie['Episode']:
            print()
            print(episode)
            print(episode['EpisodeName'])
            print(episode['EpisodeNumber'])
            print(episode['SeasonNumber'])
            print(episode['seasonid'])
            print(episode['seriesid'])
            print(episode['id'])
            print(episode['FirstAired'])
            print(episode['Overview'])
            print(episode['Writer'])
            printKey(episode, 'filename')
            print(episode['Rating'])
            print(episode['Director'])
            print(episode['GuestStars'])
            print(episode['Rating'])


if __name__ == '__main__':
    main()
