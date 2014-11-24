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
		self.nrk_duration 	= 0
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


	# String representation
	def __str__(self):
		strr  = 'Film: ' + str(self.id) + '\n'
		strr += '  > Feature: ' + str(self.feature) + ' (' + self.reason + ')\n'
		strr += '  * NRK:\n'
		strr += '    > Title: ' + str(self.nrk_title) + '\n'
		strr += '    > Year: ' + str(self.nrk_year) + '\n'
		strr += '    > Org.title: ' + str(self.nrk_org_title) + '\n'
		strr += '    > Plot: ' + str(self.nrk_plot) + '\n'
		strr += '    > Backdrop: ' + str(self.nrk_backdrop) + '\n'
		strr += '    > Stream: ' + str(self.nrk_stream) + '\n'
		strr += '    > Duration: ' + str(self.nrk_duration) + '\n'
		strr += '    > Expires: ' + str(self.nrk_expires) + '\n'
		strr += '  * TMDB:\n'
		strr += '    > Title: ' + str(self.tmdb_title) + '\n'
		strr += '    > Year: ' + str(self.tmdb_year) + '\n'
		strr += '    > Org.title: ' + str(self.tmdb_org_title) + '\n'
		strr += '    > Plot: ' + str(self.tmdb_plot) + '\n'
		strr += '    > Poster: ' + str(self.tmdb_poster) + '\n'
		strr += '    > Backdrop: ' + str(self.tmdb_backdrop) + '\n'
		strr += '    > Genres: ' + str(self.tmdb_genres) + '\n'
		strr += '    > Directors: ' + str(self.tmdb_directors) + '\n'
		strr += '    > Writers: ' + str(self.tmdb_writers) + '\n'
		strr += '    > Cast: ' + str(self.tmdb_cast) + '\n'

		return strr


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