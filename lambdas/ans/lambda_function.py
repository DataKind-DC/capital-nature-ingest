import bs4
import requests
import json
import csv
import sys
import os
sys.path.append(os.getcwd())
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import boto3

def fetch_page(options):
  url = options['url']
  fetch_months = options['fetch_months'] 
  if len(fetch_months) > 0:
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome()
    driver.get(url) 
    # TODO: iterate
    month = fetch_months[0]
    timeout = 5
    try:
      wait = WebDriverWait(driver, timeout)
      wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@title="{0}"]'.format(month))))
    except Exception as e:
      print(e)
    driver.execute_script('document.querySelector("a[title=\'{0}\']").click()'.format(month))

    try:
      wait = WebDriverWait(driver, timeout)
      expected_text = '{0}, 2019'.format(month)
      ec = EC.text_to_be_present_in_element((By.ID, "evcal_cur"), expected_text)
      wait.until(ec)
    except Exception as e:
      print(e)
    html_doc = driver.page_source
    driver.close()
  else:
    html_doc = requests.get(url).content
  return html_doc

def handler(event, context):
  url = event['url']
  bucket = 'aimeeb-datasets-public'
  if 'fetch_months' in event:
    fetch_months = event['fetch_months']
  else:
    fetch_months = []
  page = fetch_page({'url': url, 'fetch_months': fetch_months})
  soup = bs4.BeautifulSoup(page, 'html.parser')
  events = soup.find_all('div', {'class': 'event'})
  event_output = []
  for e in events:
    latLong = e.find('p').find('span', {'class': 'evcal_desc'})['data-latlng'].split(',')
    spanTime = e.find('p').find('span', {'class': 'evo_time'})
    event_data = {
      'website': e.find('a')['href'],
      'startDate': e.find('time', {'itemprop': 'startDate'})['datetime'],
      'startTime': spanTime.find('span', {'class': 'start'}).text,
      'endDate': e.find('time', {'itemprop': 'endDate'})['datetime'],
      'endTime': spanTime.find('span', {'class': 'end'}).text.replace('- ', ''),
      'venueName': e.find('span', {'itemprop': 'name'}).text,
      'venueAddress': e.find('item', {'itemprop': 'streetAddress'}).text,
      'latitude': float(latLong[0]),
      'longitude': float(latLong[1])
    }
    event_output.append(event_data)

  filename = 'ans-results.csv'
  with open('/tmp/{0}'.format(filename), mode = 'w') as f:
    writer = csv.DictWriter(f, fieldnames = event_output[0].keys())
    writer.writeheader()
    [writer.writerow(event) for event in event_output]
  s3 = boto3.resource('s3')
  s3.meta.client.upload_file(
    '/tmp/{0}'.format(filename),
    bucket,
    'capital-nature/{0}'.format(filename)
  )  
  return json.dumps(event_output, indent=2)

event = { 'url': 'https://anshome.org/events-calendar/' }
handler(event, {})
