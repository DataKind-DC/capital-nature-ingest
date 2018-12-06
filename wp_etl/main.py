from wp_etl.csv_parser import CSVParser
from wp_etl.loader import DatabaseLoader

def main():
    cp = CSVParser()
    cp.open("result.csv")
    cp.parse()

    # Settings to connect to Docker test container
    dbl = DatabaseLoader(host="127.0.0.1", port=3306, user="wordpress", db="wordpress", passwd="wordpress")
    dbl.load_events(cp.parsed_events)

if __name__ == "__main__":
    main()