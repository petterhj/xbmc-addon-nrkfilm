#!/usr/bin/python
# -*- coding: utf-8 -*-

# Imports
import sys
import os
import re
import time
import json
import time
import datetime
import requests

if __name__ == '__main__':
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
    
from resources.lib.tmdbsimple import TMDB
from resources.lib.prettytable import PrettyTable

from film import Film
from cache import Cache


# NRK
URL_FILMS       = 'http://tv.nrk.no/listobjects/indexelements/filmer-og-serier/page/0'
URL_FILM        = 'http://v7.psapi.nrk.no/mediaelement/%s'
URL_GFX         = 'http://m.nrk.no/m/img?kaleidoId=%s&width=%d'
USER_AGENT      = 'xbmc.org'
COOKIES         = 'NRK_PLAYER_SETTINGS_TV=devicetype=desktop&preferred-player-odm=hlslink&preferred-player-live=hlslink'
FILTERS         = ['kortfilm', 'fjernsynsteatret', 'synstolket']
CLEAN_TITLE     = ['Film:', 'Filmklassiker:', 'Filmsommer:']
MIN_LENGTH      = 3600

# TMDB
URL_IMAGE       = 'http://image.tmdb.org/t/p/'
URL_POSTER      = URL_IMAGE + 'w500%s'
URL_FANART      = URL_IMAGE + 'w1280%s'
TMDB_KEY        = '8cca874e1c98f99621d8200be1b16bd0'

# Colors
COLOR_RED       = '\033[91m'
COLOR_GREEN     = '\033[92m'
COLOR_YELLOW    = '\033[93m'
COLOR_BLUE      = '\033[94m'
COLOR_MAGENTA   = '\033[95m'
COLOR_CYAN      = '\033[96m'
COLOR_RESET     = '\033[0m'
        

# NRKFilm
class NRKFilm:
    # Init
    def __init__(self, cache_file, ignore_geoblock=False):
        # Tools
        self.tools = self.Tools()
            
        # Logging
        self.results = PrettyTable([
            'Element', 'Cached', 'Feature', 'Reason', 'Expires', 'Duration',
            'Title', 'Year', 'Org.Title',
            'T.Title', 'T.Year', 'T.Ds', 'T.Ws', 'T.C'
        ])
        self.results.align = 'l'

        self.errors = PrettyTable([
            'Line', 'Filename', 'Type', 'Exception', 'Message'
        ])
        self.errors.align = 'l'

        self.tools.log('Initializing (ignore geoblock = ' + str(ignore_geoblock) + ')')

        # Debug
        self.geoblock = ignore_geoblock

        # Initialize
        try:
            # Session
            self.session = self.init_session()

            # TMDb
            self.tmdb = TMDB(TMDB_KEY)

        except Exception, e:
            self.tools.catch_error(self.errors, e, 'Could not initialize library')

        else:
            # Load cache
            self.tools.log('Loading cache...')

            try:
                # Cache
                self.cache = Cache(cache_file)

            except Exception, e:
                self.tools.catch_error(self.errors, e, 'Could not load cache')

            else:
                self.tools.log('Found ' + str(len(self.cache.films)) + ' cached films')
            
                # Get feature films
                self.films = self.get_films() or {}

                # Write cache
                self.tools.log('Updating cache...')

                if len(self.films) > 0:
                    try:
                        self.cache.write(self.films)

                    except Exception, e:
                        self.tools.catch_error(self.errors, e, 'Could not write cache')

                    else:
                        self.tools.log('Wrote ' + str(len(self.films)) + ' films to cache')
                else:
                    self.tools.log('Nothing to update')
                    

        # Errors
        print self.errors


    # Get films
    def get_films(self):
        # Films
        films = {}

        # Get elements
        self.tools.log('Getting elements from NRK API...')

        try:
            elements = self.get_elements()

        except Exception, e:
            self.tools.catch_error(self.errors, e, 'Could not fetch elements from NRK')

        else:
            self.tools.log('Found ' + str(len(elements)) + ' possible feature films')

            # Elements
            for element in elements:
                # Check if cached
                if element in self.cache.films:
                    # Load from cache
                    film = self.cache.films[element]

                else:
                    # New film
                    film = Film(element_id=element)

                    try:
                        # Get info
                        info = self.tools.get_json((URL_FILM % element), self.session)

                    except Exception, e:
                        self.tools.catch_error(self.errors, e, 'Could not fetch element details')

                    else:
                        # Title
                        film.nrk_title = self.tools.clean_title(info['title'])

                        # Check if available (or debug)
                        if info['isAvailable'] or self.geoblock:
                            # Check length
                            if self.geoblock or int(info['convivaStatistics']['contentLength']) > MIN_LENGTH:
                                # Check if element description for filter matches
                                if not any([e.lower() in info['description'].lower() for e in FILTERS]):
                                    # Passed
                                    film.feature        = True

                                    # NRK metadata
                                    film.nrk_year       = self.tools.find_year(info['description'])
                                    film.nrk_org_title  = self.tools.find_org_title(info['description'])
                                    film.nrk_plot       = self.tools.clean_plot(info['description'])
                                    film.nrk_backdrop   = URL_GFX % (info['image']['id'], 1920)
                                    film.nrk_stream     = info['mediaUrl'] if 'mediaUrl' in info else None
                                    film.nrk_duration   = info['convivaStatistics']['contentLength'] if info['isAvailable'] else None,
                                    film.nrk_expires    = self.tools.expiration(info['usageRights']['availableTo'])

                                    # TMDB metadata
                                    try:
                                        tinfo, tcredits = self.get_tmdb_data(film.nrk_title, film.nrk_org_title, film.nrk_year)

                                    except Exception, e:
                                        self.tools.catch_error(self.errors, e, 'Could not fetch TMDB data for "' + film.nrk_title + '"')

                                    else:
                                        film.tmdb_title     = tinfo['title'] if 'title' in tinfo else None
                                        film.tmdb_org_title = tinfo['original_title'] if 'original_title' in tinfo else None
                                        film.tmdb_year      = tinfo['release_date'].split('-')[0] if 'release_date' in tinfo and tinfo['release_date'] else None
                                        film.tmdb_plot      = tinfo['overview'] if 'overview' in tinfo else None
                                        film.tmdb_poster    = (URL_POSTER % tinfo['poster_path']) if 'poster_path' in tinfo and tinfo['poster_path'] else None
                                        film.tmdb_backdrop  = (URL_FANART % tinfo['backdrop_path']) if 'backdrop_path' in tinfo and tinfo['backdrop_path'] else None
                                        film.tmdb_genres    = [g['name'] for g in tinfo['genres']] if 'genres' in tinfo else []
                                        film.tmdb_directors = filter(None, [d['name'] if d['job'] == 'Director' else None for d in tcredits['crew']]) if 'crew' in tcredits else []
                                        film.tmdb_writers   = filter(None, [d['name'] if d['job'] == 'Writer' else None for d in tcredits['crew']]) if 'crew' in tcredits else []
                                        film.tmdb_cast      = filter(None, [d['name'] for d in tcredits['cast']]) if 'cast' in tcredits else []

                                else:
                                    film.reason = 'Filtered'
                            else:
                                film.reason = 'Short'
                        else:
                            film.reason = 'Not available'


                # Add to films
                films[film.id] = film

                # Log: Result
                if film.nrk_expires:
                    expires = datetime.datetime.fromtimestamp(film.nrk_expires).strftime('%d.%m.%y (%H:%M)')
                    expires = COLOR_RED + expires + COLOR_RESET if int(time.time()) > film.nrk_expires else COLOR_YELLOW + expires + COLOR_RESET
                else:
                    expires = ''                        

                self.results.add_row([
                    # Element
                    COLOR_CYAN + film.id + COLOR_RESET, 
                    COLOR_GREEN + 'True' + COLOR_RESET if element in self.cache.films else COLOR_BLUE + 'False' + COLOR_RESET,
                    COLOR_GREEN + 'True' + COLOR_RESET if film.feature else COLOR_RED + 'False' + COLOR_RESET,
                    film.reason,
                    expires,
                    COLOR_CYAN + str(film.nrk_duration[0]) + COLOR_RESET if film.nrk_duration > 0 else '',


                    # Meta
                    film.nrk_title if film.nrk_title else '',
                    film.nrk_year if film.nrk_year else '',
                    film.nrk_org_title if film.nrk_org_title else '',

                    film.tmdb_title if film.tmdb_title else '',
                    film.tmdb_year if film.tmdb_year else '',
                    len(film.tmdb_directors) if film.tmdb_directors else '',
                    len(film.tmdb_writers) if film.tmdb_writers else '',
                    len(film.tmdb_cast) if film.tmdb_cast else ''
                ])

            # Log: Results
            print self.results
            
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
        # Return feature films
        return [film for film in self.films.values() if film.feature]


    # Session
    def init_session(self):
        session = requests.session()
        session.headers['User-Agent'] = USER_AGENT
        session.headers['Cookie'] = COOKIES

        return session


    # Tools
    class Tools:
        # Get JSON data
        def get_json(self, url, session):
            data = json.loads(session.get(url).text)
            
            return data


        # Clean title
        def clean_title(self, title):
            # Remove any unwanted words from title
            return ' '.join([w for w in title.split(' ') if w not in CLEAN_TITLE]).encode('utf-8')


        # Clean plot
        def clean_plot(self, plot):
            plot = plot.replace('\n', '')
            plot = plot.replace('\r', '.')
            plot = ' '.join(plot.split())
            plot = plot.replace('..', '. ')

            return plot.encode('utf-8')


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


        # Log
        def log(self, message):
            print '[\033[95mNRKFilm\033[0m] %s' % (message)

        # Error
        def catch_error(self, table, exception, message):
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

            table.add_row([
                COLOR_GREEN + str(exc_tb.tb_lineno) + COLOR_RESET,
                COLOR_CYAN + fname + COLOR_RESET,
                COLOR_MAGENTA + str(exc_type) + COLOR_RESET,
                COLOR_RED + str(exception) + COLOR_RESET,
                COLOR_YELLOW + message + COLOR_RESET
            ])



# Testing
if __name__ == '__main__':
    nrk = NRKFilm('/tmp/nrkcache', debug=True)