from typing import Pattern
import requests
import sys
import re
import os
import json
import math
from random import randint, random, randrange
from time import sleep
from reviews.common.network import Network
from reviews.common.config import config
from reviews.main.reviews_formatter import ReviewFormatter
from reviews.common.functions import *
from reviews.common.logger import logger
from reviews.main.scraper_interface import IScraper


class Trustpilot(IScraper):

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
        logger.info(f'Terminating {self.platformName} Engine')

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

        return {
            "id": jsonStr['@id'],
            "name": jsonStr['name'],
            "telephone": None,
            "address": jsonStr['address'],
            "reviews": self.fetchReviews(jsonStr['review'], self.extractNextPageUrl()),
            "rating": {
                "aggregate": jsonStr['aggregateRating']['ratingValue'],
                "total": jsonStr['aggregateRating']['reviewCount'],
            },
        }

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\" data-business-unit-json-ld>\n(.*?)\n.*</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = self.reviewsCleanup(matches[0].strip())
            result = json.loads(result)

        return result[0]

    def reviewsCleanup(self, reviewJSON):
        result = reviewJSON

        result = result.replace(',"@type":"Person"', '')
        result = result.replace(',"@type":"Review"', '')
        result = result.replace(',"@type":"Rating"', '')
        result = result.replace(',"@type":"Thing"', '')
        result = result.replace(',"@type":"PostalAddress"', '')

        return result

    def extractNextPageUrl(self):
        result = None
        pattern = r"<link rel=\"next\" href=\"(https://www.trustpilot.com/review/.*?)\" />"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0].strip()

        return result

    def fetchReviews(self,  currentReviews, reviewBaseUrl):
        result = []

        reviewFormatter = ReviewFormatter(self.platformName)

        if len(currentReviews) > 0:
            for review in currentReviews:
                formattedReview = reviewFormatter.format(review)
                result.append(formattedReview)

        while reviewBaseUrl is not None:
            scrapedRawData = Network.fetch(Network.GET, self.siteHeaders, reviewBaseUrl)
            if(scrapedRawData['code'] == 200):
                self.scrapedRawData = scrapedRawData['body']
                reviewBaseUrl = self.extractNextPageUrl()
                jsonStr = self.extractJSON()
                for review in jsonStr['review']:
                    formattedReview = reviewFormatter.format(review)
                    result.append(formattedReview)


                sleep(randrange(1, 3))

        return result

