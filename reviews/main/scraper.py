from reviews.common.logger import logger
from reviews.main.sites.yelp import Yelp
from reviews.main.sites.bbb import Bbb
from reviews.main.sites.trustpilot import Trustpilot
from reviews.main.sites.houzz import Houzz
from reviews.main.sites.homeadvisor import Homeadvisor
from reviews.main.sites.googlemaps import Googlemaps
from reviews.main.sites.buildzoom import Buildzoom
from reviews.main.sites.angi import Angi
from reviews.main.sites.gaf import Gaf
from reviews.main.sites.bestpickreports import Bestpickreports
from reviews.main.sites.facebook import Facebook
from reviews.main.sites.thumbtack import Thumbtack

import requests
import sys
import importlib
from reviews.main.sites import *
from reviews.common.network import Network
from reviews.main.scraper_interface import ScraperInterface


class Scraper(ScraperInterface):
    scraper_client = ''

    def __init__(self, reviewSite):
        self.scraper_client = getattr(sys.modules[__name__], reviewSite)()
        pass

    def scrapeListings(self, url, csvFileNamePath):
        return self.scraper_client.scrapeListings(url, csvFileNamePath)

    def scrapeReviews(self, url):
        return self.scraper_client.scrapeReviews(url)

    def scrapeImages(self, url, imageSavePath):
        return self.scraper_client.scrapeImages(url, imageSavePath)
