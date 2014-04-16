#!/usr/bin/python
# -*- coding: utf-8 -*-


# Imports
from xbmcswift2 import xbmc, xbmcgui, Plugin

from resources.lib.nrkfilm import nrkfilm


# Plugin
plugin = Plugin()


# Generate list item
def listitem(film):
    print film 
    # Info
    poster  = film['tmdb']['poster'] or film['nrk']['poster'] or film['nrk']['fanart'] or ''
    fanart  = film['tmdb']['fanart'] or film['nrk']['fanart'] or ''
    title   = film['tmdb']['title'] or film['nrk']['title'] or ''
    otitle  = film['tmdb']['original_title'] or film['nrk']['original_title'] or title
    plot    = film['tmdb']['description'] or film['nrk']['description'] or ''
    year    = film['tmdb']['year'] or film['nrk']['year'] or 0
    genre   = ', '.join(film['tmdb']['genre'])
    cast    = []
    rating  = 10

    stream  = film['nrk']['stream'] if not _isDebug() else plugin.url_for('index')

    # Item
    item = {
        'icon':         poster,
        'thumbnail':    poster,
        'label':        title,
        'info': {
            'title':        title,
            'originaltitle':otitle,
            'plot':         plot,
            'plotoutline':  plot,
            'year':         year,
            'genre':        genre,
            'cast':         cast,
            'rating':       rating
        },
        'properties': {
            'fanart_image': fanart,
        },
        'path':         stream
    }

    return item


# Films
@plugin.route('/')
def index():
    # Content type
    plugin.set_content('movies')

    # Get feature films
    cache = plugin.storage_path + 'cache' if not _isDebug() else '/tmp/cache'

    films = nrkfilm.NRKFilm(cache).feature_films()
    
    # Items
    items = [listitem(film) for film in films]
    
    # Return
    return items


# Debug
def _isDebug():
    try:
        import xbmc
    except ImportError:
        return True
    else:
        return False

# Main
if __name__ == '__main__':
    plugin.run()