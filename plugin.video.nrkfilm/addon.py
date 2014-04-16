# Imports
import nrkfilm

from xbmcswift2 import xbmc, xbmcgui, Plugin


# Plugin
plugin = Plugin()


# Films
@plugin.route('/')
def index():
	# Content type
	plugin.set_content('movies')

	# Get diary
	films = nrkfilm.get_films()

	print films
	
	items = [{
		'icon':			films[id]['tmdb']['poster'],
		'thumbnail': 	films[id]['tmdb']['poster'],
		'label':		films[id]['tmdb']['original_title'] or films[id]['nrk']['original_title'] or films[id]['nrk']['title'],
		'info': {
			'genre': 		'Genres',
			'rating': 		10
		},
		'path':			films[id]['nrk']['media_url']
	} for id in films]
		
	
	# Return
	return items


# Main
if __name__ == '__main__':
	plugin.run()