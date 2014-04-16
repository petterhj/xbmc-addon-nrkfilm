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
    cache = plugin.storage_path + 'cache'

    films = nrkfilm.NRKFilm(cache).feature_films()
    
    # Items
    items = [{
        'icon':         film['tmdb']['poster'] if film['tmdb'] else film['nrk']['poster'],
        'thumbnail':    film['tmdb']['poster'] if film['tmdb'] else film['nrk']['poster'],
        'label':        film['tmdb']['original_title'] if film['tmdb'] else film['nrk']['original_title'] or film['nrk']['title'],
        'info': {
            'title':        film['tmdb']['title'] if film['tmdb'] else film['nrk']['title'],
            'originaltitle':film['tmdb']['original_title'] if film['tmdb'] else film['nrk']['original_title'] or film['tmdb']['title'] or film['nrk']['title'],
            'year':         film['tmdb']['year'] if film['tmdb'] else film['nrk']['year'],
            'genre':        ', '.join(film['tmdb']['genre']),
            'rating':       10
        },
        'path':         film['nrk']['stream'] if not _isDebug() else plugin.url_for('index')
    } for film in films]
        
    
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