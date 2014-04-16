#!/usr/bin/python
# -*- coding: utf-8 -*-

# Imports
import os
import re
import datetime
import requests
import json
#import shelve
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
REMOVE      = ['Film:', 'Filmklassiker:']

#CACHE_FILE  = os.path.join(os.path.dirname(__file__), 'cache')
CACHE_FILE = '/home/petterhj/projects/xbmc-addon-nrkfilm/plugin.video.nrkfilm/cache'

print CACHE_FILE


with open(CACHE_FILE, 'a+b') as fh:
    cache = pickle.load(fh)


'''

# Cache
#cache = shelve.open(os.path.join(os.path.dirname(__file__), 'cache'))
cache = pickle.load(open(CACHE_FILE, 'r+b'))
print cache

# TMDB
tmdb = TMDB(TMDB_KEY)


# Get JSON data
def get_data(url):
    try:
        resp = requests.get(url)
        data = json.loads(resp.text)
    except:
        raise Exception('Could not fetch JSON data')
    else:
        return data


# Clean title
def clean_title(title):
    title = ' '.join([w for w in title.split(' ') if w not in REMOVE])

    return title


# Find year
def find_year(desc):
    year1 = re.search('fra ([0-9]{4})', desc).group(1) if re.search('fra ([0-9]{4})', desc) else None
    year2 = re.search('([0-9]{4})', desc).group(1) if re.search('([0-9]{4})', desc) else None

    return year1 or year2


# Find origional title
def find_org_title(desc):
    title = re.findall('\(([^\)]+)\)', desc.encode('utf-8'))
    title = filter(None, [t if re.search('([0-9]+ år)', t) is None and len(t) > 2 else None for t in title])
    title = title[0] if len(title) > 0 else None

    return title


# Get TMDB data
def get_tmdb_data(title, original_title, year):
    # Search
    query = original_title or title

    search = tmdb.Search()
    response = search.movie({'query': query})

    for s in search.results:
        film = None

        if year:
            print s['title'], year, s['release_date'] 
            if year in s['release_date']:
                film = s
        else:
            film = s

        # Details
        if film:
            f = tmdb.Movies(film['id'])
            return {'info': f.info(), 'credits': f.credits()}

    return None


# Get films
def get_films():
    # Get data
    print 'get films |',
    data = get_data(URL_FILMS)
    print 'done'

    # Films
    films = {}

    # Elements
    for char in data['Data']['characters']:
        elements = [e for e in char['elements'] if '/serie/' not in e['Url']]
        elements = [f for f in elements if not any([e.lower() in f['Title'].lower() for e in FILTERS])]

        for element in elements:
            try:
                # Element ID
                eid = element['Url'].split('/')[2].encode('utf8')
            except:
                pass
            else:
                # Check cache
                if eid in cache:
                    # Load from cache
                    if cache[eid]:
                        films[eid] = cache[eid]

                else:
                    # Get element info
                    print 'get info (' + element['Title'] + ', ' + eid + ') |',
                    info = get_data((URL_FILM % eid))
                    print 'done'

                    if info['isAvailable'] and int(info['convivaStatistics']['contentLength']) > 3600:
                        # Basic data
                        films[eid] = {
                            'nrk': {
                                'title':            clean_title(info['title']),
                                'original_title':   find_org_title(info['description']),
                                'year':             find_year(info['description']),
                                'available':        info['isAvailable'],
                                'media_url':        info['mediaUrl'],
                                'duration':         info['convivaStatistics']['contentLength'],
                                'expires':          re.search('\(([0-9]{10})', info['usageRights']['availableTo']).group(1)
                            },
                            'tmdb': {}
                        }

                        # TMDB data
                        tmdb = get_tmdb_data(films[eid]['nrk']['title'], films[eid]['nrk']['original_title'], films[eid]['nrk']['year'])

                        films[eid]['tmdb']['original_title'] = tmdb['info']['original_title']
                        films[eid]['tmdb']['summary'] = tmdb['info']['overview']
                        films[eid]['tmdb']['genres'] = [g['name'] for g in tmdb['info']['genres']]
                        films[eid]['tmdb']['director'] = filter(None, [d['name'] if d['job'] == 'Director' else None for d in tmdb['credits']['crew']])
                        films[eid]['tmdb']['writer'] = filter(None, [d['name'] if d['job'] == 'Writer' else None for d in tmdb['credits']['crew']])
                        films[eid]['tmdb']['poster'] = (URL_POSTER % tmdb['info']['poster_path'])
                        films[eid]['tmdb']['fanart'] = (URL_FANART % tmdb['info']['backdrop_path'])

                        # Save to cache
                        cache[eid] = films[eid]

                    else:
                        # Cache not available (no need to check again)
                        cache[eid] = None

        # Write cache
        pickle.dump(cache, open(CACHE_FILE, 'wb'))

        
    # Return
    return films


# TEST
'''
'''

films = get_films()

for filmid in films:
    print films[filmid]['nrk']['title'], '[' + filmid + ']'
    
    #print ' > Element:\t', filmid
    #print ' > Org.title:\t', films[filmid]['original_title']
    #print ' > Year:\t', films[filmid]['year']
    #print ' > Plot:\t', films[filmid]['tmdb']['info']['overview'][0:75] + '...'
    #print ' > Duration:\t', (int(films[filmid]['nrk']['duration']) / 60)
    #print ' > Expires:\t', datetime.datetime.fromtimestamp(int(films[filmid]['nrk']['expires'])).strftime('%Y-%m-%d')
    #print ' > Genres:\t', films[filmid]['genres']
    
    print films[filmid]
    print


'''