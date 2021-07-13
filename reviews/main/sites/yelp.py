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


class Yelp:

    siteUrl = None
    scrapedRawData = None
    siteHeaders = None

    def __init__(self):
        print('Initalized Yelp Engine')
        pass

    def scrapeURL(self, url):
        returnArr = []

        self.siteUrl = url

        if config.get('scraper_mode') == 'online':
            headersArr = {}
            scrapedRawData = Network.fetch(url, headersArr)
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

        return {
            "id": self.extractId(),
            "name": jsonStr['name'],
            "telephone": jsonStr['telephone'],
            "address": jsonStr['address'],
            "reviews": self.fetchReviews(self.generateReviewUrl(self.extractId()), jsonStr['aggregateRating']['reviewCount']),
            "rating": {
                "aggregate": jsonStr['aggregateRating']['ratingValue'],
                "total": jsonStr['aggregateRating']['reviewCount'],
            },
        }

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\">({\"@context\":\"https://schema.org\",\"@type\":\"LocalBusiness\".*?)</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0]

        return json.loads(result)

    def extractId(self):
        result = None
        pattern = r"meta.*?name=\"yelp-biz-id\" content=\"(.*?)\""
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0]

        return result

    def extractName(self):
        result = None
        pattern = r"meta name=\"yelp-biz-id\" content=\"(.*?)\""
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0]

        return result

    def generateReviewUrl(self, businessId):
        return f"https://www.yelp.com/biz/{businessId}/review_feed?rl=en&q=&sort_by=relevance_desc"

    def fetchReviews(self, reviewBaseUrl, totalReviews):
        result = []

        reviewFormatter = ReviewFormatter('yelp')
        for i in range(math.ceil(int(totalReviews/10))+1):
            if i < 1:
                appendPage = ''
            else:
                appendPage = f"&start={i*10}"

            reviewUrl = f"{reviewBaseUrl}{appendPage}"
            scrapedRawData = Network.fetch(reviewUrl, self.siteHeaders)
            if(scrapedRawData['code'] == 200):
                reviewsRawData = json.loads(scrapedRawData['body'])
                if 'reviews' in reviewsRawData:
                    if len(reviewsRawData['reviews']) > 0:
                        for review in reviewsRawData['reviews']:
                            formattedReview = reviewFormatter.format(review)
                            result.append(formattedReview)
                sleep(randrange(1, 3))

        return result
