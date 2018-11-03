import bs4
import requests

elasticsearch_domain = XXX

event = {
  "eventType": "Volunteer",
  "description": "Join us in planting 80 trees on Heritage Island.",
  "venue": "Heritage Island",
  "address": {
    "streetAddress": "575 Oklahoma Ave NE",
    "addressLocality": "Washington",
    "addressRegion": "DC",
    "postalCode": "20002",
    "addressCountry": "US"
  },  
  "geo": {
    "lat": 38.8959751,
    "lon": -76.9709448
  },
  "startDate": "2018-10-06T09:00:00-04:00",
  "endDate": "2018-10-06T12:00:00-04:00",
  "url": "https://caseytrees.org/event/volunteer-heritage-island-community-tree-planting/",
  "image": "https://caseytrees.org/wp-content/uploads/2018/08/387e7949d4f5d75504bfae95a9019b18.jpg"  
}

r = requests.post('{0}/capital_nature/events/1'.format(elasticsearch_domain), data=event)

