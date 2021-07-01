from reviews.main.sites.yelp import Yelp
from reviews.main.sites.bbb import BBB
from reviews.main.sites.trustpilot import Trustpilot
from reviews.main.sites.houzz import Houzz
from reviews.main.sites.homeadvisor import Homeadvisor
from reviews.main.sites.googlemaps import Googlemaps

import requests
import sys
import importlib
from reviews.main.sites import *
from reviews.common.network import Network


class Scraper:
    scraper_client = ''

    def __init__(self, reviewSite):
        self.scraper_client = getattr(sys.modules[__name__], reviewSite)()
        pass

    def scrapeURL(self, url):
        return self.scraper_client.scrapeURL(url)
