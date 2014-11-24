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
    cache = plugin.storage_path + 'nrkcache' if not _isDebug() else '/tmp/cache'

    films = nrkfilm.NRKFilm(cache).feature_films() if not _isDebug() else nrkfilm.NRKFilm(cache, ignore_geoblock=True).feature_films()
  
    # Items
    items = [
        {
            'icon':         film.tmdb_poster or film.nrk_backdrop or '',
            'thumbnail':    film.tmdb_poster or film.nrk_backdrop or '',
            'label':        film.tmdb_title or film.tmdb_org_title or film.nrk_title or film.nrk_org_title or '',
            'info': {
                'title':        film.tmdb_title or film.tmdb_org_title or film.nrk_title or film.nrk_org_title or '',
                'originaltitle':film.tmdb_org_title or film.nrk_org_title or film.tmdb_title or film.nrk_title or '',
                'plot':         film.tmdb_plot or film.nrk_plot or '',
                'plotoutline':  film.tmdb_plot or film.nrk_plot or '',
                'year':         film.tmdb_year or film.nrk_year or 0,
                'genre':        ', '.join(film.tmdb_genres),
                'director':     ', '.join(film.tmdb_directors),
                'writer':       ', '.join(film.tmdb_writers),
                'cast':         film.tmdb_cast,
                'rating':       10 # TODO!
            },
            'properties': {
                'fanart_image': film.tmdb_backdrop or film.nrk_backdrop or '',
            },
            'path':         plugin.url_for('play', url=film.nrk_stream) if film.nrk_stream else '',
            'is_playable':  True if film.nrk_stream else False,
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

    # No films
    if len(films) == 0:
        # No films available
        plugin.notify(msg='No films available (norwegian IP?)', title='NRKFilm', delay=5000)
    
    # Return
    return items


# Play
@plugin.route('/play/<url>/')
def play(url):
    plugin.log.info('Playing url: %s' % url)
    plugin.set_resolved_url(url)


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