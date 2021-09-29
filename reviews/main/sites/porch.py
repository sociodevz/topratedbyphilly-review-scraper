import requests
import sys
import re
import os
import json
import math
import datetime
import html
import time
import traceback
import wget
from random import randint, random, randrange
from time import sleep
from bs4 import BeautifulSoup

from reviews.common.network import Network
from reviews.common.config import config
from reviews.main.reviews_formatter import ReviewFormatter
from reviews.common.functions import *
from reviews.common.logger import logger
from reviews.main.scraper_interface import IScraper


class Porch(IScraper):

    platformName = None
    siteUrl = None
    scrapedRawData = None
    siteHeaders = None
    siteId = None

    def __init__(self):
        self.platformName = self.__class__.__name__
        logger.info(f'Initalized {self.platformName} Engine')
        pass

    def __del__(self):
        logger.info(f'Terminating {self.platformName} Engine\nScraping: {self.siteUrl}')

    def scrapeReviews(self, url):
        returnArr = []

        self.siteUrl = url

        logger.info(f'Scraping: {self.siteUrl}')

        if config.get('scraper_mode') == 'online':
            headersArr = {}
            scrapedRawData = Network.fetch(Network.GET, headersArr, url)
            if(scrapedRawData['code'] == 200):
                self.siteHeaders = scrapedRawData['headers']['requested']
                self.siteHeaders['referer'] = self.siteUrl

                self.scrapedRawData = scrapedRawData['body']
        elif config.get('scraper_mode') == 'offline':
            filePath = os.path.realpath(__file__)
            currentFileName = os.path.basename(__file__)
            filePath = filePath.replace(currentFileName, '')
            file = open(f"{filePath}/sample_data/{url}")
            self.scrapedRawData = file.read()

        if self.scrapedRawData is not None:
            result = self.processRawData()
            returnArr = result

        return returnArr

    def processRawData(self):
        jsonStr = self.extractJSON()
        jsonStr = fixLocalBusinessJSON(jsonStr)
        self.siteUrl = jsonStr['url']
        self.extractId()

        return {
            "id": self.siteId,
            "name": jsonStr['name'],
            "telephone": jsonStr['telephone'],
            "address": jsonStr['address'],
            "reviews": [],
            "rating": {
                "aggregate": self.extractAggregateRating(),
                "total": self.extractTotalReviewCount(),
            },
        }

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\">(.*?)</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.DOTALL)

        if len(matches) > 0:
            result = json.loads(matches[0].strip())

        return result

    def extractId(self):
        try:
            self.siteId = 0
        except Exception as e:
            pass

    def extractAggregateRating(self):
        result = 0

        try:
            soup = BeautifulSoup(self.scrapedRawData, 'lxml')
            aggregateRatingMeta = soup.find('meta', attrs={'itemprop': 'ratingValue'})
            if aggregateRatingMeta is not None:
                result = float(aggregateRatingMeta['content'].strip())
        except Exception as e:
            logger.log('Exception')

        return result

    def extractTotalReviewCount(self):
        result = 0

        try:
            soup = BeautifulSoup(self.scrapedRawData, 'lxml')
            totalReviewsCountMeta = soup.find('meta', attrs={'itemprop': 'ratingCount'})
            if totalReviewsCountMeta is not None:
                result = int(totalReviewsCountMeta['content'].strip())
        except Exception as e:
            logger.log('Exception')

        return result

    def scrapeListings(self, url, csvFileNamePath):
        pass

    def scrapeImages(self, url, imageSavePath):
        pass
