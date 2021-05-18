from reviews.main.sites.yelp import Yelp
import requests
import sys
import importlib
from reviews.main.sites import *
from reviews.common.network import Network


class Scraper:
    SCRAPER_YELP = 'Yelp'
    SCRAPER_BBB = 'BBB'
    scraper_client = ''

    def __init__(self, reviewSite):
        self.scraper_client = getattr(sys.modules[__name__], reviewSite)()
        pass

    def scrapeURL(self, url):
        return self.scraper_client.scrapeURL(url)
