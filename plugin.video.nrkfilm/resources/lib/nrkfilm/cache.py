# Imports
import os
import pickle

# Cache
class Cache:
    # Initialize cache
    def __init__(self, cache_file):
        # Cache file
        self.cache_file = cache_file

        # Create empty cache
        if not os.path.isfile(self.cache_file):
            self.write()

        # Read cache
        with open(self.cache_file, 'rb') as fh:
            self.films = pickle.load(fh)


    # Write cache
    def write(self, films={}):
        # Write
        with open(self.cache_file, 'wb') as fh:
            pickle.dump(films, fh)