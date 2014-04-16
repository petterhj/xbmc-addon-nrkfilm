'''
from resources.lib.nrkfilm import nrkfilm

nrk = nrkfilm.NRKFilm('/tmp/cache2')

info = nrk.tools.get_json('http://v7.psapi.nrk.no/mediaelement/fbua61001682')
print info
meta_nrk = {
    'title':            nrk.tools.clean_title(info['title']),
    'original_title':   nrk.tools.find_org_title(info['description']),
    'year':             nrk.tools.find_year(info['description']),
    'description':      info['description'].replace('\n', '').replace('\r', '.').replace('..', '. '),
    'poster':           None,
    'fanart':           info['images']['webImages'][2]['imageUrl'] or info['images']['webImages'][1]['imageUrl'] or info['images']['webImages'][0]['imageUrl'],
    'stream':           info['mediaUrl'],
    'duration':         (int(info['convivaStatistics']['contentLength']) / 60),
    'expires':          re.search('\(([0-9]{10})', info['usageRights']['availableTo']).group(1),
}

#info, credits = nrk.get_tmdb_data(meta_nrk['title'], meta_nrk['original_title'], meta_nrk['year'])

#print info
'''

import requests
import json

from resources.lib.tmdbsimple import TMDB

tmdb = TMDB('8cca874e1c98f99621d8200be1b16bd0')

def get_tmdb_data(title, original_title, year):
    # Search
    query = original_title or title

    search = tmdb.Search()
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
            f = tmdb.Movies(film['id'])
            
            return f.info(), f.credits()

    return None


print get_tmdb_data('Med Grimm og Gru', None, '1976')