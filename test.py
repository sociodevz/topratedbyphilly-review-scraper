from reviews.main.scraper import Scraper
from argparse import ArgumentParser
import reviews.main

parser = ArgumentParser()
parser.add_argument('-engine', type=str, required=True, help='Scraping Engine [yelp,bbb]')
parser.add_argument('-url', type=str, required=True, help='Website url to crawl')
args = parser.parse_args()
print(args)
engine = args.engine.title()
url = args.url

scraper = Scraper(engine)
result = scraper.scrapeURL(url)
print(result)
