#!/usr/bin/python
# -*- coding: utf-8 -*-

# Imports
import os
import re
import datetime
import requests
import json
import pickle

from resources.lib.tmdbsimple import TMDB


# Constants
URL_FILMS   = 'http://tv.nrk.no/listobjects/indexelements/filmer-og-serier/page/0'
URL_FILM    = 'http://v7.psapi.nrk.no/mediaelement/%s'
URL_IMAGE   = 'http://image.tmdb.org/t/p/'
URL_POSTER  = URL_IMAGE + 'w500%s'
URL_FANART  = URL_IMAGE + 'w1280%s'
TMDB_KEY    = '8cca874e1c98f99621d8200be1b16bd0'
FILTERS     = ['kortfilm', 'fjernsynsteatret']
CLEAN_TITLE = ['Film:', 'Filmklassiker:']
MIN_LENGTH  = 3600


# 
# NRKFilm
#
class NRKFilm:
    # Init
    def __init__(self, cache_file):
        # TMDb
        self.tmdb = TMDB(TMDB_KEY)

        # Tools
        self.tools = self.Tools()

        # Cache
        self.cache = self.Cache(cache_file)
        
        # Get feature films
        self.films = self.get_films() or {}

        # Write cache
        self.cache.write(self.films)


    # Get media elements (find potential feature films)
    def get_elements(self):
        # Get data
        print '[NRK] get elements |',
        data = self.tools.get_json(URL_FILMS)

        # Elements
        elements = []

        for char in data['Data']['characters']:
            elmts = [e for e in char['elements'] if '/serie/' not in e['Url']]
            elmts = [f for f in elmts if not any([e.lower() in f['Title'].lower() for e in FILTERS])]

            for element in elmts:
                try:
                    # Element ID
                    eid = element['Url'].split('/')[2].encode('utf8')
                except:
                    pass
                else:
                    elements.append(eid)

        # Return
        print 'done (found', len(elements), 'possible feature films)'
        return elements


    # Get TMDB data
    def get_tmdb_data(self, title, original_title, year):
        # Search
        query = original_title or title

        search = self.tmdb.Search()
        response = search.movie({'query': query})

        for s in search.results:
            film = None

            if year:
                print '  [TMDb] ' + s['title'] + ', year: ' + year + ', release: ' + s['release_date'] 
                if year in s['release_date']:
                    film = s
            else:
                film = s

            # Details
            if film:
                f = self.tmdb.Movies(film['id'])
                
                return {
                    'info': f.info(), 
                    'credits': f.credits()
                }

        return None


    # Get films
    def get_films(self):
        # Films
        films = {}

        # Elements
        elements = self.get_elements()

        for element in elements:
            # Cached
            if self.cache.is_cached(element):
                films[element] = self.cache.fetch(element)

            # Not cached
            else:
                # Get element info
                print '[NRK] get element info (' + element + ') |',
                info = self.tools.get_json((URL_FILM % element))
                print 'done'

                # Check if avialable and of feature length
                if info['isAvailable'] and int(info['convivaStatistics']['contentLength']) > MIN_LENGTH:
                    # NRK Metadata
                    meta_nrk = {
                        'title':            self.tools.clean_title(info['title']),
                        'original_title':   self.tools.find_org_title(info['description']),
                        'year':             self.tools.find_year(info['description']),
                        'description':      info['description'].replace('\n', '').replace('\r', '. '),
                        'poster':           None,
                        'fanart':           info['images']['webImages'][2]['imageUrl'] or info['images']['webImages'][1]['imageUrl'] or info['images']['webImages'][0]['imageUrl'],
                        'stream':           info['mediaUrl'],
                        'duration':         (int(info['convivaStatistics']['contentLength']) / 60),
                        'expires':          re.search('\(([0-9]{10})', info['usageRights']['availableTo']).group(1),
                    }

                    # TMDB Metadata
                    tmdb = self.get_tmdb_data(meta_nrk['title'], meta_nrk['original_title'], meta_nrk['year'])

                    meta_tmdb = {
                        'title':            tmdb['info']['title'],
                        'original_title':   tmdb['info']['original_title'],
                        'year':             tmdb['info']['release_date'].split('-')[0],
                        'description':      tmdb['info']['overview'],
                        'genre':            [g['name'] for g in tmdb['info']['genres']],
                        'director':         filter(None, [d['name'] if d['job'] == 'Director' else None for d in tmdb['credits']['crew']]),
                        'writer':           filter(None, [d['name'] if d['job'] == 'Writer' else None for d in tmdb['credits']['crew']]),
                        'poster':           (URL_POSTER % tmdb['info']['poster_path']),
                        'fanart':           (URL_FANART % tmdb['info']['backdrop_path']),
                    } if tmdb else None


                    # Film
                    film = {
                        'nrk':  meta_nrk,
                        'tmdb': meta_tmdb
                    }


                # Element not available (don't check again)
                else:
                    film = None


                # Add element to cache
                films[element] = film


        # Return
        return films


    # Avialable feature films
    def feature_films(self):
        # Return
        return filter(None, self.films.values())


    # Cache
    class Cache:
        # Initialize cache
        def __init__(self, cache_file):
            # Cache file
            self.cache_file = cache_file

            # Create empty cache
            if not os.path.isfile(self.cache_file):
                self.write()

            # Read cache
            with open(self.cache_file, 'rb') as fh:
                self.films = pickle.load(fh)


        # Retrieve element
        def fetch(self, id):
            # Return
            return self.films[id]


        # Check if element is cached
        def is_cached(self, id):
            # Look by element id
            if id in self.films:
                return True
            else:
                return False


        # Write cache
        def write(self, films={}):
            # Write
            with open(self.cache_file, 'wb') as fh:
                pickle.dump(films, fh)

    
    # Tools
    class Tools:
        # Get JSON data
        def get_json(self, url):
            try:
                data = json.loads(requests.get(url).text)
            except:
                raise
            else:
                return data


        # Clean title
        def clean_title(self, title):
            # Remove any unwanted words from title
            return ' '.join([w for w in title.split(' ') if w not in CLEAN_TITLE])


        # Find year
        def find_year(self, description):
            # Find possible year
            year1 = re.search('fra ([0-9]{4})', description).group(1) if re.search('fra ([0-9]{4})', description) else None
            year2 = re.search('([0-9]{4})', description).group(1) if re.search('([0-9]{4})', description) else None

            return year1 or year2


        # Find origional title
        def find_org_title(self, description):
            # Find possible origional title
            title = re.findall('\(([^\)]+)\)', description.encode('utf-8'))
            title = filter(None, [t if re.search('([0-9]+ år)', t) is None and len(t) > 2 else None for t in title])
            title = title[0] if len(title) > 0 else None

            return title


#
# TESTING
#
if __name__ == '__main__':
    nrk = NRKFilm('/tmp/cache')

    print '-'*100
    print 'NRK tests'
    print '-'*100
    print 'Cache:', len(nrk.cache.films.keys())
    print 'Films:', len(nrk.films.keys()), '(no new films found)' if len(nrk.cache.films.keys()) == len(nrk.films.keys()) else ''
    print
    print 'Avialable feature films'
    print '-'*75

    for film in nrk.feature_films():
        print '*', film['nrk']['title']
        print '  > Title:\t', film['nrk']['original_title']
        print '  > Year:\t', film['nrk']['year']
        print '  > Plot:\t', film['nrk']['description'][0:75], '...'
        print '  > Poster:\t', film['nrk']['poster']
        print '  > Fanart:\t', film['nrk']['fanart']
        print '  > Stream:\t', film['nrk']['stream'][0:50], '...'
        print '  > Duration:\t', film['nrk']['duration']
        print '  > Expires:\t', film['nrk']['expires']
        print
        print '  > Title:\t', film['tmdb']['title']
        print '  > Org.Title:\t', film['tmdb']['original_title']
        print '  > Year:\t', film['tmdb']['year']
        print '  > Plot:\t', film['tmdb']['description'][0:75], '...'
        print '  > Genre:\t', film['tmdb']['genre']
        print '  > Director:\t', film['tmdb']['director']
        print '  > Writer:\t', film['tmdb']['writer']
        print '  > Poster:\t', film['tmdb']['poster']
        print '  > Fanart:\t', film['tmdb']['fanart']
        print
    print
