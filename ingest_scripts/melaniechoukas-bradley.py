import bs4
import geocoder
import json
import os
import requests
import re

url = 'https://melaniechoukas-bradley.com/schedule.php'
page = requests.get(url)
soup = bs4.BeautifulSoup(page.content, 'html.parser')
elasticsearch_domain = os.environ['ELASTICSEARCH_DOMAIN']

## Dates
dates = soup.find_all('p', {'class': 'date'})

for date in dates:
  organization = date.findNext('p', {'class': 'style25green'}).text.encode('utf-8').strip()
  title = date.findNext('p', {'class': 'title'}).text.encode('utf-8').strip()
  link = date.findNext('a')
  link_text = link.text.lower()
  registrationURL = ''
  if ('here' or 'register' in link_text) and ('href' in link):
    registrationURL = link['href']
  nextTag = None
  descriptionTag = date.findNext('blockquote')
  description = ''
  latitude, longitude = None, None
  if descriptionTag:
    description = descriptionTag.text
    paras = descriptionTag.find_all('p', {'class', 'style2'})
    for p in paras:
      if len(p.text) < 100:
        g = geocoder.osm(descriptionTag.text)
        if g.ok:
          latitude = g.lat
          longitude = g.lng      
  event_data = {
    'description': description,
    'organization': organization,
    'title': title,
    'url': url,
    'registrationURL': registrationURL,
    'ingested_by': 'https://github.com/DataKind-DC/capital-nature-ingest/blob/master/melaniechoukas-bradley.py'
  }
  if latitude and longitude:
    event['geo'] = {
      'lat': latitude,
      'lon': longitude
    }
  title_words = title.lower().split(' ')
  title_words = [re.sub('[^A-Za-z0-9]+', '', word) for word in title_words]
  event_id = '-'.join(title_words)
  r = requests.put(
    "{0}/capital_nature/event/{1}".format(elasticsearch_domain, event_id),
    data=json.dumps(event_data),
    headers = {'content-type': 'application/json'})
  print(r.status_code)

