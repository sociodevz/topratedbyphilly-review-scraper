import requests
import sys
import importlib
from reviews.common.network import Network
from reviews.main.scraper_interface import IScraper
from reviews.common.logger import logger
from reviews.main.sites import *


class ScraperFactory():
    """Factory file to return site scraper clients"""

    def get_client(reviewSite):
        return getattr(sys.modules[__name__], reviewSite)()
