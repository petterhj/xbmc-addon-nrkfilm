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
