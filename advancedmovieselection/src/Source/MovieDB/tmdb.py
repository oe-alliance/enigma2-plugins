"""
Copyright (C) 2013 cmikula

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
from __future__ import absolute_import
config = None
poster_sizes = ('w92', 'w154', 'w185', 'w342', 'w500', 'original')


def setPosterSize(size):
    global config
    value = size.value
    if value in poster_sizes:
        print('[AdvancedMovieSelection] Set tmdb poster size to', value)
        config['poster_size'] = value


def setLocale(lng):
    global config
    print('[AdvancedMovieSelection] Set tmdb locale to', lng)
    config = {}
    config['locale'] = lng
    config['apikey'] = '1f834eb425728133b9a2c1c0c82980eb'
    config['poster_size'] = 'w185'


def getLocale():
    return config['locale']


def decodeCertification(releases):
    cert = None
    if 'US' in releases:
        cert = releases['US'].certification
    certification = {'G': 'VSR-0',
     'PG': 'VSR-6',
     'PG13': 'VSR-12',
     'PG-13': 'VSR-12',
     'R': 'VSR-16',
     'NC-13': 'VSR-18',
     'NC17': 'VSR-18'}
    if cert in certification:
        return certification[cert]


def nextImageIndex(movie):
    if len(movie.poster_urls) > 1:
        item = movie.poster_urls.pop(0)
        movie.poster_urls.append(item)
    movie.poster_url = movie.poster_urls[0]


def prevImageIndex(movie):
    if len(movie.poster_urls) > 1:
        item = movie.poster_urls.pop(-1)
        movie.poster_urls.insert(0, item)
    movie.poster_url = movie.poster_urls[0]


def poster_url(poster):
    sizes = poster.sizes()
    size = config['poster_size']
    if size in sizes:
        return poster.geturl(size)
    p_index = poster_sizes.index(size)
    p_range = range(p_index, len(poster_sizes) - 1)
    for x in p_range:
        size = poster_sizes[x]
        if size in sizes:
            return poster.geturl(size)

    poster.geturl()


def __collect_poster_urls(movie):
    l = []
    if movie.poster is not None:
        l.append(poster_url(movie.poster))
    for p in movie.posters:
        url = poster_url(p)
        if url not in l:
            l.append(url)

    movie.poster_urls = l
    if len(movie.poster_urls) > 0:
        movie.poster_url = movie.poster_urls[0]
    else:
        movie.poster_url = None


def __searchMovie(title):
    res = original_search(title)
    for movie in res:
        __collect_poster_urls(movie)

    return res


from . import tmdb3
original_search = tmdb3.searchMovie
tmdb3.searchMovie = __searchMovie


def init_tmdb3():
    tmdb3.set_key(config['apikey'])
    tmdb3.set_cache('null')
    lng = config['locale']
    if lng == 'en':
        tmdb3.set_locale(lng, 'US')
    elif lng == 'el':
        tmdb3.set_locale(lng, 'GR')
    elif lng == 'cs':
        tmdb3.set_locale(lng, 'CZ')
    elif lng == 'da':
        tmdb3.set_locale(lng, 'DK')
    elif lng == 'uk':
        tmdb3.set_locale('en', 'GB')
    elif lng == 'fy':
        tmdb3.set_locale(lng, 'NL')
    else:
        tmdb3.set_locale(lng, lng.upper())
    print('tmdbv3 locale', tmdb3.get_locale())
    return tmdb3


def main():
    setLocale('de')
    tmdb3 = init_tmdb3()
    res = tmdb3.searchMovie('James Bond 007 - Skyfall')
    print(res)
    movie = res[0]
    print(movie.title)
    print(movie.releasedate.year)
    print(movie.overview)
    for p in movie.poster_urls:
        print(p)

    for p in movie.posters:
        print(p)

    for p in movie.backdrops:
        print(p)

    p = movie.poster
    print(p)
    print(p.sizes())
    print(p.geturl())
    print(p.geturl('w185'))
    p = movie.backdrop
    print(p)
    print(p.sizes())
    print(p.geturl())
    print(p.geturl('w300'))
    crew = [x.name for x in movie.crew if x.job == 'Director']
    print(crew)
    crew = [x.name for x in movie.crew if x.job == 'Author']
    print(crew)
    crew = [x.name for x in movie.crew if x.job == 'Producer']
    print(crew)
    crew = [x.name for x in movie.crew if x.job == 'Director of Photography']
    print(crew)
    crew = [x.name for x in movie.crew if x.job == 'Editor']
    print(crew)
    crew = [x.name for x in movie.crew if x.job == 'Production Design']
    print(crew)
    cast = [x.name for x in movie.cast]
    print(cast)
    genres = [x.name for x in movie.genres]
    print(genres)
    studios = [x.name for x in movie.studios]
    print(studios)
    countries = [x.name for x in movie.countries]
    print(countries)


if __name__ == '__main__':
    main()
