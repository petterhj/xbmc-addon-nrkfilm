#!/usr/bin/python
# -*- coding: utf-8 -*-

# Imports
import sys
import os
import re
import time
import datetime
import requests
import json
import pickle

if __name__ == '__main__':
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
    
from resources.lib.tmdbsimple import TMDB


# NRK
URL_FILMS   = 'http://tv.nrk.no/listobjects/indexelements/filmer-og-serier/page/0'
URL_FILM    = 'http://v7.psapi.nrk.no/mediaelement/%s'
URL_GFX     = 'http://m.nrk.no/m/img?kaleidoId=%s&width=%d'
USER_AGENT  = 'xbmc.org'
COOKIES     = 'NRK_PLAYER_SETTINGS_TV=devicetype=desktop&preferred-player-odm=hlslink&preferred-player-live=hlslink'
FILTERS     = ['kortfilm', 'fjernsynsteatret', 'synstolket']
CLEAN_TITLE = ['Film:', 'Filmklassiker:', 'Filmsommer:']
MIN_LENGTH  = 3600

# TMDB
URL_IMAGE   = 'http://image.tmdb.org/t/p/'
URL_POSTER  = URL_IMAGE + 'w500%s'
URL_FANART  = URL_IMAGE + 'w1280%s'
TMDB_KEY    = '8cca874e1c98f99621d8200be1b16bd0'


# Logging
class Log:
    # Init
    def __init__(self):
        self.temp = ''
        self.project = '[\033[95mNRKFilm\033[0m]'

        self.codes = {
            'REQUEST': '\033[94m',
            'PARSE': '\033[94m',
            'CACHED': '\033[36m',
            'SUCCESS': '\033[92m',
            'WARNING': '\033[93m',
            'ERROR': '\033[91m',
            'FAIL': '\033[91m',

            'not available': '\033[91m',
            'filtered': '\033[36m',
            'short': '\033[93m'
        }


    # Process
    def start(self, message, indent=0):
        self.temp  = '  '*indent
        self.temp += message + ' ' + '.'*(50 - len(message))

    def success(self, message='', results=[]):
        self.msg(self.temp + '[SUCCESS] ' + message)

        for result in results:
            print '\t>', result

    def warning(self, message):
        self.msg(self.temp + '[WARNING] ' + message)        

    def fail(self, message):
        self.msg(self.temp + '[FAIL] ' + message)

    def exception(self, message, exp):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

        self.msg(self.temp + '[FAIL] ' + str(message) + ': ' + str(exp) + ' at line ' + str(exc_tb.tb_lineno) + ' in ' + fname + ' (' + str(exc_type) + ')')


    # Out
    def msg(self, message=None, indent=0):
        out = self.project + ' '
        out += '  '*indent

        if message:
            # Colors
            for code in self.codes:
                if code in message:
                    message = message.replace(code, self.codes[code] + code + '\033[0m')

            # Print message
            out += message
            
            print out
        

# NRKFilm
class NRKFilm:
    # Init
    def __init__(self, cache_file, debug=False):
        # Logging
        self.log = Log()

        self.log.start('Initializing (debug = ' + str(debug) + ')')

        # Debug
        self.debug = debug

        # Session
        try:
            self.session = requests.session()
            self.session.headers['User-Agent'] = USER_AGENT
            self.session.headers['Cookie'] = COOKIES

            # TMDb
            self.tmdb = TMDB(TMDB_KEY)

            # Tools
            self.tools = self.Tools()

        except Exception, e:
            self.log.exception('Could not initialize lib', e)

        else:
            self.log.success('Done')

            # Load cache
            self.log.start('Loading cache')

            try:
                # Cache
                self.cache = self.Cache(cache_file)

            except Exception, e:
                self.log.exception('Could not load cache', e)

            else:
                self.log.success('Found ' + str(len(self.cache.films)) + ' cached films')
            
                # Get feature films
                self.films = self.get_films() or {}

                # Write cache
                self.log.start('Update cache')

                if len(self.films) > 0:
                    try:
                        self.cache.write(self.films)

                    except Exception, e:
                        self.log.exception('Could not update cache', e)

                    else:
                        self.log.success('Wrote ' + str(len(self.films)) + ' films to cache')
                else:
                    self.log.warning('Nothing to add')


    # Get films
    def get_films(self):
        # Films
        films = {}

        # Get elements
        self.log.start('Get elements from NRK')

        try:
            elements = self.get_elements()

        except Exception, e:
            self.log.exception('Could fetch elements', e)

        else:
            self.log.success('Found ' + str(len(elements)) + ' possible feature films')

            # Elements
            for element in elements:
                # Cached
                if self.cache.is_cached(element):
                    films[element] = self.cache.fetch(element)

                    self.log.start('[CACHED] Loading ' + element + ' from cache', indent=1)

                    if 'skipped' not in films[element]:
                        self.log.success('Loaded "' + str(films[element]['nrk']['title']) + '" as "' + str(films[element]['tmdb']['title']) + '"')
                    else:
                        self.log.warning('Skipped "' + str(films[element]['title']) + '" (' + films[element]['reason'] + ')')

                # Not cached
                else:
                    self.log.start('[REQUEST] Get ' + element + ' info from NRK', indent=1)

                    try:
                        # Get info
                        info = self.tools.get_json((URL_FILM % element), self.session)

                    except Exception, e:
                        self.log.exception('Could not get data', e)

                    else:
                        # Title
                        title = self.tools.clean_title(info['title'])

                        # Check if available
                        if not info['isAvailable']:
                            self.log.warning('Skipped "' + title + '" (not available)')
                            film = {'skipped': True, 'title': title, 'reason': 'not available'}

                        # Check if of feature length
                        elif int(info['convivaStatistics']['contentLength']) < MIN_LENGTH:
                            self.log.warning('Skipped "' + title + '" (short)')
                            film = {'skipped': True, 'title': title, 'reason': 'short'}

                        # Check if element description for filter matches
                        elif any([e.lower() in info['description'].lower() for e in FILTERS]):
                            self.log.warning('Skipped "' + title + '" (filtered)')
                            film = {'skipped': True, 'title': title, 'reason': 'filtered'}

                        else:
                            self.log.success('Found "' + title + '"')

                            # Metadata
                            try:
                                # NRK Metadata
                                self.log.start('[PARSE] NRK metadata', indent=2)

                                meta_nrk = {
                                    'title':            self.tools.clean_title(info['title']),
                                    'original_title':   self.tools.find_org_title(info['description']),
                                    'year':             self.tools.find_year(info['description']),
                                    'description':      info['description'].replace('\n', '').replace('\r', '.').replace('..', '. '),
                                    'poster':           None,
                                    # 'fanart':           info['images']['webImages'][2]['imageUrl'] or info['images']['webImages'][1]['imageUrl'] or info['images']['webImages'][0]['imageUrl'],
                                    'fanart':           URL_GFX % (info['image']['id'], 1920),
                                    'stream':           info['mediaUrl'],
                                    'duration':         (int(info['convivaStatistics']['contentLength']) / 60),
                                    'expires':          self.tools.expiration(info['usageRights']['availableTo']),
                                }

                            except Exception, e:
                                self.log.exception('Could not get metadata', e)

                            else:
                                self.log.success('Done')

                                # TMDB Metadata
                                try:
                                    self.log.start('[REQUEST] TMDB metadata', indent=2)

                                    tinfo, tcredits = self.get_tmdb_data(meta_nrk['title'], meta_nrk['original_title'], meta_nrk['year'])

                                except Exception, e:
                                    self.log.exception('Could not get metadata', e)

                                else:
                                    meta_tmdb = {
                                        'title':            tinfo['title'] if 'title' in tinfo else None,
                                        'original_title':   tinfo['original_title'] if 'original_title' in tinfo else None,
                                        'year':             tinfo['release_date'].split('-')[0] if 'release_date' in tinfo and tinfo['release_date'] else None,
                                        'description':      tinfo['overview'] if 'overview' in tinfo else None,
                                        'genre':            [g['name'] for g in tinfo['genres']] if 'genres' in tinfo else [],
                                        'director':         filter(None, [d['name'] if d['job'] == 'Director' else None for d in tcredits['crew']]) if 'crew' in tcredits else [],
                                        'writer':           filter(None, [d['name'] if d['job'] == 'Writer' else None for d in tcredits['crew']]) if 'crew' in tcredits else [],
                                        'cast':             filter(None, [d['name'] for d in tcredits['cast']]) if 'cast' in tcredits else [],
                                        'poster':           (URL_POSTER % tinfo['poster_path']) if 'poster_path' in tinfo and tinfo['poster_path'] else None,
                                        'fanart':           (URL_FANART % tinfo['backdrop_path']) if 'backdrop_path' in tinfo and tinfo['backdrop_path'] else None,
                                    }

                                    # Check if match
                                    if 'title' in tinfo:
                                        self.log.success('Found "' + tinfo['title'] + '"')

                                    else:
                                        self.log.warning('No match')

                                # Film
                                film = {
                                    'nrk':  meta_nrk,
                                    'tmdb': meta_tmdb
                                }

                        # Add element to cache
                        films[element] = film

        # Return
        return films


    # Get media elements (find potential feature films)
    def get_elements(self):
        # Get data
        data = self.tools.get_json(URL_FILMS, self.session)

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
                if year in s['release_date']:
                    film = s
                else:
                    # TODO: BUG HERE!!!!!
                    if (title.lower() == s['title'].lower()) or (original_title.lower() == s['original_title'].lower()):
                        film = s
            else:
                film = s

            # Details
            if film:
                f = self.tmdb.Movies(film['id'])

                return f.info(), f.credits()

        return {}, {}


    # Available feature films
    def feature_films(self):
        # Available films
        films = []

        for film in self.films.values():
            if 'skipped' not in film:
                films.append(film)

        # Return
        return films


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
        def get_json(self, url, session):
            try:
                data = json.loads(session.get(url).text)
            except:
                raise
            else:
                return data


        # Clean title
        def clean_title(self, title):
            # Remove any unwanted words from title
            return ' '.join([w for w in title.split(' ') if w not in CLEAN_TITLE]).encode('utf-8')


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


        # Expiration timestamp
        def expiration(self, timestamp):
            time = re.search('\(([0-9]{10})[0-9]+\+[0-9]([0-9])', timestamp)
            gmt = int(time.group(1))
            tz = int(time.group(2))
            return (gmt + (tz * 3600))


#
# TESTING
#
if __name__ == '__main__':
    nrk = NRKFilm('/tmp/nrkcache', debug=True)

    print '-'*100
    print 'NRK tests'
    print '-'*100
    print 'Cache:', len(nrk.cache.films.keys())
    print 'Films:', len(nrk.films.keys()), '(no new films found)' if len(nrk.cache.films.keys()) == len(nrk.films.keys()) else ''
    print
    print 'Available feature films'
    print '-'*75

    for film in nrk.feature_films():
        print '*', film['nrk']['title']
        print '-'*50
        print '  > Title:\t', film['nrk']['title']
        print '  > Org.Title:\t', film['nrk']['original_title']
        print '  > Year:\t', film['nrk']['year']
        print '  > Plot:\t', film['nrk']['description']
        print '  > Poster:\t', film['nrk']['poster']
        print '  > Fanart:\t', film['nrk']['fanart']
        print '  > Stream:\t', film['nrk']['stream'][0:30], '...', film['nrk']['stream'][-20:]
        print '  > Duration:\t', film['nrk']['duration']
        print '  > Expires:\t', film['nrk']['expires'], '(Now:', str(int(time.time())) + ')'
        print
        if film['tmdb']:
            print '  > Title:\t', film['tmdb']['title']
            print '  > Org.Title:\t', film['tmdb']['original_title']
            print '  > Year:\t', film['tmdb']['year']
            print '  > Plot:\t', film['tmdb']['description']
            print '  > Genre:\t', film['tmdb']['genre']
            print '  > Director:\t', film['tmdb']['director']
            print '  > Writer:\t', film['tmdb']['writer']
            print '  > Cast:\t', film['tmdb']['cast']
            print '  > Poster:\t', film['tmdb']['poster']
            print '  > Fanart:\t', film['tmdb']['fanart']
            print
    print
