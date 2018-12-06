import csv
import wp_etl.utils as utils

# This dictionary maps from the CSV columns
# to the MySQL (table, attribute) pairs in Wordpress
DATA_TRANSFORMS = {
    "id": {"source_col": "_id", "default": None, "required": True},
    "title": {"source_col": ["_source/name","_source/title"], "default": None, "required": True},
    "description": {"source_col": "_source/description", "default": None, "required": False},
    "image": {"source_col": "_source/image", "default": None, "required": False},
    "event_url": {"source_col": "_source/url", "default": None, "required": False},
    "physical_requirements": {"source_col": "_source/physicalRequirements", "default": None, "required": False},
    
    "organization_name": {"source_col": ["_source/organization","_source/organizationDetails/name"], "default": None, "required": False},
    "organization_contact_person": {"source_col": None, "default": None, "required": False},
    "organization_phone_number": {"source_col": None, "default": None, "required": False},
    "organization_email": {"source_col": "_source/organizationDetails/email", "default": None, "required": False},
    "organization_url": {"source_col": "_source/organizationDetails/url", "default": None, "required": False},
    
    "start_date": {"source_col": "_source/startDate", "default": None, "required": True, "handler": "get_date"},
    "end_date": {"source_col": "_source/endDate", "default": None, "required": False, "handler": "get_date"},
    # TODO: parse times from datetimes
    "start_time": {"source_col": "_source/startDate", "default": None, "required": False, "handler": "get_time"},
    "end_time": {"source_col": "_source/endDate", "default": None, "required": False, "handler": "get_time"},
    "all_day": {"source_col": None, "default": None, "required": False},
    
    "location_venue": {"source_col": ["_source/location/name", "_source/venue"], "default": None, "required": False},
    "location_country": {"source_col": ["_source/location/addressCountry","_source/location/address/addressCountry"], "default": "USA", "required": False},
    "location_address1": {"source_col": ["_source/location/streetAddress","_source/location/address/streetAddress"], "default": None, "required": False},
    "location_address2": {"source_col": None, "default": None, "required": False},
    "location_city": {"source_col": ["_source/location/addressLocality","_source/location/address/addressLocality"], "default": None, "required": False},
    "location_state": {"source_col": ["_source/location/addressRegion","_source/location/address/addressRegion"], "default": None, "required": False},
    "location_zipcode": {"source_col": ["_source/location/postalCode","_source/location/address/postalCode"], "default": None, "required": False},
    "location_lat": {"source_col": ["_source/geo/lat", "_source/location/geo/latitude"], "default": None, "required": True, "handler": "coord_check"},
    "location_lon": {"source_col": ["_source/geo/lon", "_source/location/geo/longitude"], "default": None, "required": True, "handler": "coord_check"},
    "location_description": {"source_col": "_source/location/description", "default": None, "required": False},
    "location_url": {"source_col": "_source/location/url", "default": None, "required": False},
    "location_phone": {"source_col": "_source/location/telephone", "default": None, "required": False},

    "is_ticket_required": {"source_col": "_source/registrationRequired", "default": None, "required": False},
    "is_ticket_free": {"source_col": "_source/fee", "default": None, "required": False},
    "ticket_cost": {"source_col": "_source/fee", "default": None, "required": False},
    "ticketing_url": {"source_col": "_source/registrationURL", "default": None, "required": False},
    "registration_by_date": {"source_col": "_source/registrationByDate", "default": None, "required": False},

    "ingesting_script": {"source_col": "_source/ingested_by", "default": None, "required": True},
    "ingest_source_url": {"source_col": "_source/url", "default": None, "required": True},
    "ingest_source_name": {"source_col": None, "default": None, "required": False},
    "activity_category": {"source_col": None, "default": None, "required": False},
    "activity_tags": {"source_col": None, "default": None, "required": False}
}

class CSVParser:

    def __init__(self):
        self.data = []
        self.colnames = None
        self.parsed_events = {"events": []}

    def open(self, f):
        with open(f, "r") as data:
            reader = csv.reader(data)
            self.colnames = next(reader)
            for row in reader:
                self.data.append(row)
        print(f"Loaded {len(self.data)} rows from {f}.")

    def parse(self):
        success_count = 0
        for i, row in enumerate(self.data):
            print("Parsing event " + str(i+1))
            try:
                self.parsed_events['events'].append(self.__get_vals(row))
                success_count += 1
            except Exception as E:
                print(E)
                print("...skipping event")
        print(f"Successfully parsed {success_count} rows")


    def __get_vals(self, row):
        vals = {}
        for k in DATA_TRANSFORMS:
            scraped_val = ''
            try:
                if isinstance(DATA_TRANSFORMS[k]['source_col'], str):
                    scraped_val = row[self.__get_col_idx(DATA_TRANSFORMS[k]['source_col'])]
                elif isinstance(DATA_TRANSFORMS[k]['source_col'], list):
                    scraped_vals = [row[self.__get_col_idx(c)] for c in DATA_TRANSFORMS[k]['source_col']]
                    for v in scraped_vals:
                        scraped_val = v
                        if v:
                            break
                if "handler" in DATA_TRANSFORMS[k]:
                    handler = getattr(utils, DATA_TRANSFORMS[k]['handler'])
                    scraped_val = handler(scraped_val)
            except Exception as E:
                scraped_val = ''
                if DATA_TRANSFORMS[k]['required'] == True:
                    print("Couldn't parse data for required attribute " + k)
                    raise E
                elif DATA_TRANSFORMS[k]['default'] != None:
                    scraped_val = DATA_TRANSFORMS[k]['default']
            vals[k] = scraped_val
        return vals


    def __get_col_idx(self, colname):
        return self.colnames.index(colname)
