import requests
import json

resp = requests.get('http://tv.nrk.no/listobjects/indexelements/filmer-og-serier/page/0')
data = json.loads(resp.text)

FILTERS     = ['kortfilm', 'fjernsynsteatret']
REMOVE      = ['Film:', 'Filmklassiker:']

for char in data['Data']['characters']:
    elements = [e for e in char['elements'] if '/serie/' not in e['Url']]
    elements = [f for f in elements if not any([e.lower() in f['Title'].lower() for e in FILTERS])]

    for element in elements:
        element_id = element['Url'].split('/')[2].encode('utf8')
        resp = requests.get('http://v7.psapi.nrk.no/mediaelement/' + element_id)
        info = json.loads(resp.text)

        print info['description'].replace('\r', '. ').replace('\n', '')
        print