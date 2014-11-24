# Imports


# Film
class Film:
	# Init
	def __init__(self, element_id):
		# Properties
		self.id 			= element_id
		self.feature 		= False
		self.reason			= ''

		# Metadata
		self.nrk_title 		= None
		self.nrk_year 		= None
		self.nrk_org_title	= None
		self.nrk_plot 		= None
		self.nrk_backdrop	= None

		self.nrk_stream		= None
		self.nrk_duration 	= None
		self.nrk_expires	= None

		self.tmdb_title		= None
		self.tmdb_org_title = None
		self.tmdb_year		= None
		self.tmdb_plot		= None
		self.tmdb_poster	= None
		self.tmdb_backdrop	= None
		self.tmdb_genres	= []
		self.tmdb_directors	= []
		self.tmdb_writers	= []
		self.tmdb_cast		= []


# Testing
if __name__ == '__main__':
	film = Film('KOFI123123141')

	film.nrk_title 		= None
	film.nrk_org_title 	= None
	film.tmdb_title		= None

	print film.nrk_title
	print film.nrk_org_title
	print film.tmdb_title

	title = film.tmdb_title or film.nrk_org_title or film.nrk_title or '!'

	print
	print title