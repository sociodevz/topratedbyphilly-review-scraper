from typing import List, Pattern
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
from reviews.common.logger import logger
from reviews.main.scraper_interface import IScraper
#from reviews.main.review_object import Review


class Angi(IScraper):

    platformName = None
    siteUrl = None
    scrapedRawData = None
    siteHeaders = None
    siteId = None

    def __init__(self):
        self.platformName = self.__class__.__name__
        print(f'Initalized {self.platformName} Engine')
        logger.info(f'Initalized {self.platformName} Engine')
        pass

    def scrapeReviews(self, url):
        returnArr = []

        self.siteUrl = url

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
            reviewFormatter = ReviewFormatter(self.platformName)
            #reviews: List[Review]

            self.siteHeaders['authority'] = 'www.angi.com'
            soup = BeautifulSoup(self.scrapedRawData, 'lxml')
            if soup is not None:
                reviewCategoriesObj = soup.find_all("span", id=lambda x: x and x.startswith('review-filter-pill-'))
                if len(reviewCategoriesObj) > 0:
                    for reviewFilterCategory in reviewCategoriesObj:
                        categoryReviewCount = int(reviewFilterCategory['data-count'])
                        categoryFilterId = int(reviewFilterCategory['data-key'])

                        limitPerPage = 10
                        for i in range(math.ceil(int(categoryReviewCount/limitPerPage))+1):
                            offset = i * limitPerPage
                            categoryReviewUrl = reviewBaseUrl.replace('OFFSET_NUMBER', str(offset)).replace('CATEGORY_ID', str(categoryFilterId))

                            scrapedRawData = Network.fetch(Network.GET, self.siteHeaders, categoryReviewUrl)
                            if(scrapedRawData['code'] == 200):
                                reviewsRawData = json.loads(scrapedRawData['body'])
                                if 'reviews' in reviewsRawData:
                                    if len(reviewsRawData['reviews']) > 0:
                                        for review in reviewsRawData['reviews']:
                                            formattedReview = reviewFormatter.format(review)
                                            result.append(formattedReview)
                                sleep(randrange(1, 3))
                else:
                    scrape = True

                    while scrape is True:
                        scrape = False
                        reviewsDivObject = soup.findAll('div', attrs={'class': 'review-card'})
                        if reviewsDivObject is not None:
                            for reviewDiv in reviewsDivObject:
                                reviewObj = {
                                    'id': 0,
                                    'ratings': [
                                        {
                                            'ratingType': 'Overall',
                                            'startRating': 0
                                        },
                                    ],
                                    'reviewText': None,
                                    'reportDate': None,
                                    'retort': {
                                        'text': None
                                    }

                                }

                                ratingSpanObj = reviewDiv.find('span', attrs={'class': 'rating-number'})
                                if ratingSpanObj is not None:
                                    reviewObj["ratings"][0]["starRating"] = float(ratingSpanObj.text.strip())

                                reviewPDate = reviewDiv.find('p', attrs={'class': 'review-card__report-date'})
                                if reviewPDate is not None:
                                    reviewObj['reportDate'] = reviewPDate.text.strip()

                                reviewDivText = reviewDiv.find('div', attrs={'class': 'review-card__review-text'})
                                if reviewDivText is not None:
                                    reviewObj["reviewText"] = reviewDivText.text.strip()

                                reviewDivBusinessResponse = reviewDiv.find('div', attrs={'class': 'review-card__service-provider-response'})
                                if reviewDivBusinessResponse is not None:
                                    reviewObj['retort']['text'] = reviewDivBusinessResponse.text.replace('Service Provider Response','').strip()

                                formattedReview = reviewFormatter.format(reviewObj)
                                result.append(formattedReview)

                        sleep(randrange(1, 3))
                        nextPageUrl = self._getNextPageUrl(soup)
                        if nextPageUrl is not False:
                            scrapedRawData = Network.fetch(Network.GET, self.siteHeaders, nextPageUrl)
                            if(scrapedRawData['code'] == 200):
                                soup = BeautifulSoup(scrapedRawData['body'], 'lxml')
                                if soup is None:
                                    return result
                                else:
                                    scrape = True
        except Exception as e:
            logger.exception('Exception')
            pass

        return result

    def _getNextPageUrl(self, soup: BeautifulSoup):
        result = False

        if soup is not None:
            nextPageLinkObject = soup.find("a", attrs={'title': 'Next page of reviews'})
            if nextPageLinkObject is not None:
                result = f"https://www.angi.com{nextPageLinkObject['href']}"

        return result

    def scrapeListings(self, url, csvFileNamePath):
        pass

    def scrapeImages(self, url, imageSavePath):
        pass

