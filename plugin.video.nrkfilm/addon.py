#!/usr/bin/python
# -*- coding: utf-8 -*-


# Imports
from xbmcswift2 import xbmc, xbmcgui, Plugin

from resources.lib.nrkfilm import nrkfilm


# Plugin
plugin = Plugin()


# Films
@plugin.route('/')
def index():
    # Content type
    plugin.set_content('movies')

    # Get feature films
    cache = plugin.storage_path + 'cache' if not _isDebug() else '/tmp/cache'

    films = nrkfilm.NRKFilm(cache).feature_films()
    
    # Items
    items = [
        {
            'icon':         film['tmdb']['poster'] or film['nrk']['poster'] or film['nrk']['fanart'] or '',
            'thumbnail':    film['tmdb']['poster'] or film['nrk']['poster'] or film['nrk']['fanart'] or '',
            'label':        film['tmdb']['title'] or film['nrk']['title'] or '',
            'info': {
                'title':        film['tmdb']['title'] or film['nrk']['title'] or '',
                'originaltitle':film['tmdb']['original_title'] or film['nrk']['original_title'] or film['tmdb']['title'] or film['nrk']['title'] or '',
                'plot':         film['tmdb']['description'] or film['nrk']['description'] or '',
                'plotoutline':  film['tmdb']['description'] or film['nrk']['description'] or '',
                'year':         film['tmdb']['year'] or film['nrk']['year'] or 0,
                'genre':        ', '.join(film['tmdb']['genre']),
                'director':     film['tmdb']['director'][0] if len(film['tmdb']['director']) > 0 else '',
                'writer':       film['tmdb']['writer'][0] if len(film['tmdb']['writer']) > 0 else '',
                'cast':         film['tmdb']['cast'],
                'rating':       10
            },
            'properties': {
                'fanart_image': film['tmdb']['fanart'] or film['nrk']['fanart'] or '',
            },
            'path':         film['nrk']['stream'] if not _isDebug() else plugin.url_for('index'),
            'is_playable':  True,
            'stream_info': {
                'video': {
                    'codec':        'h264',
                    'width':        1280,
                    'height':       720
                },
                'audio': {
                    'codec':        'aac',
                    'channels':     2
                }
            }
        }
    for film in films]
    
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