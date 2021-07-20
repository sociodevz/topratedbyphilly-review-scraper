from typing import Pattern
import requests
import sys
import re
import os
import json
import math
import pickle
from random import randint, random, randrange
from time import sleep
from bs4 import BeautifulSoup
from reviews.common.network import Network
from reviews.common.config import config
from reviews.main.reviews_formatter import ReviewFormatter
from reviews.common.functions import *


class Angi:

    siteUrl = None
    scrapedRawData = None
    siteHeaders = None
    siteId = None

    def __init__(self):
        print('Initalized Angi Engine')
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
        jsonStr = fixLocalBusinessJSON(jsonStr)
        self.siteUrl = jsonStr['url']
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

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\">(.*?)</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.DOTALL)

        if len(matches) > 0:
            #result = reviewsCleanup(matches[0].strip())
            result = json.loads(matches[0].strip())[1]

        return result

    def extractId(self):
        try:
            self.siteId = int(self.siteUrl.replace('.htm', '').split('-')[-1])
        except Exception as e:
            pass

    def generateReviewUrl(self):
        result = f"https://www.angi.com/gateway/spprofile-visitor/v2/leaf/getReviewsBySpidWithFilters?categoryId=CATEGORY_ID&limit=10&offset=OFFSET_NUMBER&serviceProviderId={self.siteId}"

        return result

    def fetchReviews(self, reviewBaseUrl, totalReviews):
        result = []

        try:
            reviewFormatter = ReviewFormatter('angi')

            soup = BeautifulSoup(self.scrapedRawData, 'lxml')
            if soup is not None:
                reviewCategoriesObj = soup.find_all("span", id=lambda x: x and x.startswith('review-filter-pill-'))
                for reviewFilterCategory in reviewCategoriesObj:
                    categoryReviewCount = int(reviewFilterCategory['data-count'])
                    categoryFilterId = int(reviewFilterCategory['data-key'])

                    limitPerPage = 10
                    for i in range(math.ceil(int(categoryReviewCount/limitPerPage))+1):
                        offset = i * limitPerPage
                        categoryReviewUrl = reviewBaseUrl.replace('OFFSET_NUMBER', str(offset)).replace('CATEGORY_ID', str(categoryFilterId))

                        scrapedRawData = Network.fetch(categoryReviewUrl, self.siteHeaders)
                        if(scrapedRawData['code'] == 200):
                            reviewsRawData = json.loads(scrapedRawData['body'])
                            if 'reviews' in reviewsRawData:
                                if len(reviewsRawData['reviews']) > 0:
                                    for review in reviewsRawData['reviews']:
                                        formattedReview = reviewFormatter.format(review)
                                        result.append(formattedReview)
                            sleep(randrange(1, 3))
        except Exception as e:
            error = e
            pass

        return result
