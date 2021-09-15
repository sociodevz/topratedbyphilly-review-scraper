import requests
import json

from reviews.main.scraper import ScraperFactory
from argparse import ArgumentParser
import reviews.main
from reviews.common.config import config, updateConfigFromArgs


scraperSites = config.get('scraper_sites')
parser = ArgumentParser()
parser.add_argument('--module', type=str, required=True, help=f"Scrape Listing,Reviews or Images [list,reviews, images]")
parser.add_argument('--engine', type=str, required=True, help=f"Scraping Engine [{scraperSites}]")
parser.add_argument('--url', type=str, required=True, help='Website url to crawl')
parser.add_argument('--csvfile', type=str, required=False, help='CSV filename with path for directory listing')
parser.add_argument('--image_save_path', type=str, required=False, help='Directory where images will be saved')
args = parser.parse_args()

module = args.module
engine = args.engine.title()
url = args.url

if args.module == 'list' and args.csvfile is None:
    parser.error("--module=list requires --csvfile")
elif args.module == 'images' and args.image_save_path is None:
    parser.error("--module=images requires --image_save_path")

csvFileNamePath = args.csvfile
imageSavePath = args.image_save_path

if 'https://' not in url:
    updateConfigFromArgs({f'scraper_mode=offline'})

scraper = ScraperFactory.get_client(engine)
if module == 'reviews':
    result = scraper.scrapeReviews(url)
elif module == 'list':
    result = scraper.scrapeListings(url, csvFileNamePath)
elif module == 'images':
    result = scraper.scrapeImages(url, imageSavePath)

print(json.dumps(result, indent=3))
