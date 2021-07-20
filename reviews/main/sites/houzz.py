from requests.sessions import extract_cookies_to_jar
from reviews.common.useragents import UserAgent
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

class Houzz:

    siteUrl = None
    scrapedRawData = None
    scrapedRawReviewsData = None
    siteHeaders = None

    def __init__(self):
        print('Initalized Houzz Engine')
        pass

    def scrapeURL(self, url):
        returnArr = []

        self.siteUrl = url

        if config.get('scraper_mode') == 'online':
            headersArr = {}

            userAgent = UserAgent()
            userAgentList = userAgent.getRandom()
            headersArr.update(userAgentList)
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

    def scrapeReviews(self, siteUrl, reviewUrl):
        headersArr = {}

        userAgent = UserAgent()
        userAgentList = userAgent.getRandom()
        headersArr.update(userAgentList)
        headersArr.update({
            'referer': siteUrl,
            'x-requested-with': 'XMLHttpRequest',
        })

        scrapedRawData = Network.fetch(reviewUrl, headersArr)
        if(scrapedRawData['code'] == 200):
            self.scrapedRawReviewsData = scrapedRawData['body']
            print()

    def processRawData(self):
        jsonStr = self.extractJSON()
        jsonStr = fixLocalBusinessJSON(jsonStr)

        return {
            "id": jsonStr['@id'],
            "name": jsonStr['name'],
            "telephone": jsonStr['telephone'],
            "address": jsonStr['address'],
            "reviews": self.fetchReviews(self.generateReviewUrl(), int(jsonStr['aggregateRating']['reviewCount'])),
            "rating": {
                "aggregate": jsonStr['aggregateRating']['ratingValue'],
                "total": int(jsonStr['aggregateRating']['reviewCount']),
            },
        }

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\">(.*?)</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE | re.DOTALL)

        if len(matches) > 0:
            result = json.loads(matches[0].strip())

        return result[0]

    def generateReviewUrl(self):
        result = None

        userId = None
        professionalId = None

        pattern = r"UserProfileStore\":{\"prereqs\":.*?,\"data\":{\"user\":{\"id\":.*?,\"userId\":(.*?),\"userName\""
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            userId = matches[0].strip()

        pattern = r"professional\":{\"id\":(.*?),\"proType"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)
        if len(matches) > 0:
            professionalId = matches[0].strip()

        if userId is not None and professionalId is not None:
            result = f'https://www.houzz.com/j/ajax/profileReviewsAjax?userId={userId}&proId={professionalId}&fromItem=ITEM_NUMBER&itemsPerPage=45'

        return result

    def extractCSRF(self, cookieStr):
        result = None

        pattern = r"_csrf=(.*?);"
        matches = re.findall(pattern, cookieStr, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0].strip()

        return result

    def fetchReviews(self, reviewBaseUrl, totalReviews):
        result = []

        self.siteHeaders.update({
            'referer': self.siteUrl,
            'x-requested-with': 'XMLHttpRequest',
        })

        reviewFormatter = ReviewFormatter('houzz')
        for i in range(math.ceil(int(totalReviews/45))+1):
            reviewUrl = reviewBaseUrl.replace("ITEM_NUMBER", str(i))
            scrapedRawData = Network.fetch(reviewUrl, self.siteHeaders)
            if(scrapedRawData['code'] == 200):
                reviewsRawData = json.loads(scrapedRawData['body'])
                if 'ctx' in reviewsRawData:
                    if 'data' in reviewsRawData['ctx']:
                        if 'stores' in reviewsRawData['ctx']['data']:
                            if 'data' in reviewsRawData['ctx']['data']['stores']:
                                if 'ProfessionalReviewsStore' in reviewsRawData['ctx']['data']['stores']['data']:
                                    if len(reviewsRawData['ctx']['data']['stores']['data']['ProfessionalReviewsStore']['data']) > 0:
                                        for reviewId in reviewsRawData['ctx']['data']['stores']['data']['ProfessionalReviewsStore']['data']:
                                            review = reviewsRawData['ctx']['data']['stores']['data']['ProfessionalReviewsStore']['data'][reviewId]
                                            reviewerId = review['userId']
                                            userInfoArr = reviewsRawData['ctx']['data']['stores']['data']['UserStore']['data'][str(reviewerId)]
                                            review['user_info'] = userInfoArr
                                            formattedReview = reviewFormatter.format(review)
                                            result.append(formattedReview)

                sleep(randrange(1, 3))

        return result

