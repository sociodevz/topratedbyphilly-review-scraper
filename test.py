from reviews.main.scraper import Scraper
import json
from argparse import ArgumentParser
import reviews.main
from reviews.common.config import config, updateConfigFromArgs

parser = ArgumentParser()
parser.add_argument('-engine', type=str, required=True, help='Scraping Engine [yelp,bbb]')
parser.add_argument('-url', type=str, required=True, help='Website url to crawl')
args = parser.parse_args()

engine = args.engine.title()
url = args.url

if 'https://' not in url:
    updateConfigFromArgs({f'scraper_mode=offline'})

scraper = Scraper(engine)
result = scraper.scrapeURL(url)
print(json.dumps(result, indent=3))
