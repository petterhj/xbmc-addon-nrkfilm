import requests
import json


session = requests.session()
session.headers['User-Agent'] = 'xbmc.org'
#session.headers['X-Requested-With'] = 'XMLHttpRequest'
session.headers['Cookie'] = "NRK_PLAYER_SETTINGS_TV=devicetype=desktop&preferred-player-odm=hlslink&preferred-player-live=hlslink"

url = 'http://v7.psapi.nrk.no/mediaelement/koif40003408'
  
print session.get(url).json()['mediaUrl']
print requests.get(url).json()['mediaUrl']