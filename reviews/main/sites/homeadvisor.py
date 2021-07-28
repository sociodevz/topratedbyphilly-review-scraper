from requests.sessions import extract_cookies_to_jar
from reviews.common.useragents import UserAgent
from typing import List, Pattern
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


class Homeadvisor:

    platformName = None
    siteUrl = None
    scrapedRawData = None
    siteHeaders = None
    siteId = None

    def __init__(self):
        self.platformName = self.__class__.__name__
        print(f'Initalized {self.platformName} Engine')
        pass

    def scrapeURL(self, url):
        returnArr = []

        self.siteUrl = url

        if config.get('scraper_mode') == 'online':
            headersArr = {}

            userAgent = UserAgent()
            userAgentList = userAgent.getRandom()
            headersArr.update(userAgentList)
            scrapedRawData = Network.fetch(Network.GET, url, headersArr)

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
        jsonStr = self.extractJSON()['@graph'][1]
        jsonStr = fixLocalBusinessJSON(jsonStr)

        self.siteUrl = jsonStr['@id']
        self.extractId()

        return {
            "id": self.siteId,
            "name": jsonStr['name'],
            "telephone": jsonStr['telephone'],
            "address": jsonStr['address'],
            "reviews": self.fetchReviews(self.generateReviewUrl(), jsonStr['aggregateRating']['reviewCount']),
            "rating": {
                "aggregate": jsonStr['aggregateRating']['ratingValue'],
                "total": jsonStr['aggregateRating']['reviewCount'],
            },
        }

    def extractId(self):
        pattern = r"rated\..*?\.(.*?)\.html"
        matches = re.findall(pattern, self.siteUrl, re.MULTILINE)

        if len(matches) > 0:
            self.siteId = int(matches[0].strip())

    def extractName(self):
        result = None

        pattern = r"\"companyName\":\"(.*?)\","
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0].strip()

        return result

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\">(.*?)</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE | re.DOTALL)

        if len(matches) > 0:
            result = self.reviewsCleanup(matches[0].strip())
            result = json.loads(result)

        return result

    def generateReviewUrl(self):
        result = f"https://www.homeadvisor.com/sm/reviews/{self.siteId}?page=PAGE_NUMBER&sort=newest&pageSize=10"

        return result

    def reviewsCleanup(self, reviewJSON):
        result = reviewJSON

        result = result.replace(',"@type":"Person"', '')
        result = result.replace(',"@type":"Review"', '')
        result = result.replace(',"@type":"Rating"', '')
        result = result.replace(',"@type":"Thing"', '')
        result = result.replace(',"@type":"PostalAddress"', '')

        return result

    def fetchReviews(self, reviewBaseUrl, totalReviews):
        result = []

        reviewFormatter = ReviewFormatter(self.platformName)
        for i in range(math.ceil(int(totalReviews/10))+1):
            reviewUrl = reviewBaseUrl.replace("PAGE_NUMBER", str(i+1))
            scrapedRawData = Network.fetch(Network.GET, reviewUrl, self.siteHeaders)
            if(scrapedRawData['code'] == 200):
                reviewsRawData = json.loads(scrapedRawData['body'])
                if 'ratings' in reviewsRawData:
                    if len(reviewsRawData['ratings']) > 0:
                        for review in reviewsRawData['ratings']:
                            formattedReview = reviewFormatter.format(review)
                            result.append(formattedReview)
                sleep(randrange(1, 3))

        return result

