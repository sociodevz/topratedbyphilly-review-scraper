import requests
import sys
import importlib
from reviews.common.network import Network
from reviews.main.scraper_interface import ScraperInterface
from reviews.common.logger import logger
from reviews.main.sites import *


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
