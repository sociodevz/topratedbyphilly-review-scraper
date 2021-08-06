import requests
import json

from reviews.main.scraper import Scraper
from argparse import ArgumentParser
import reviews.main
from reviews.common.config import config, updateConfigFromArgs


scraperSites = config.get('scraper_sites')
parser = ArgumentParser()
parser.add_argument('-module', type=str, required=True, help=f"Scrape Listing or Reviews [list,reviews]")
parser.add_argument('-engine', type=str, required=True, help=f"Scraping Engine [{scraperSites}]")
parser.add_argument('-url', type=str, required=True, help='Website url to crawl')
args = parser.parse_args()

module = args.module
engine = args.engine.title()
url = args.url

if 'https://' not in url:
    updateConfigFromArgs({f'scraper_mode=offline'})

scraper = Scraper(engine)
if module == 'reviews':
    result = scraper.scrapeReviews(url)
elif module == 'list':
    result = scraper.scrapeListings(url)

print(json.dumps(result, indent=3))
