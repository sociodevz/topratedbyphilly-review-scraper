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


class Judysbook(IScraper):

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
            scrapedRawData = Network.fetch(Network.GET, url, headersArr)
            if(scrapedRawData['code'] == 200):
                self.siteHeaders = scrapedRawData['headers']['requested']
                self.siteHeaders['referer'] = self.siteUrl

                self.scrapedRawData = scrapedRawData['body']
        elif config.get('scraper_mode') == 'offline':
            self.scrapedRawData = getOfflineFile(self.siteUrl)

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
            "reviews": self.fetchReviews(jsonStr['aggregateRating']['reviewCount']),
            "rating": {
                "aggregate": self.extractAggregateRating(),
                "total": self.extractTotalRatings(),
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
            soup = BeautifulSoup(self.scrapedRawData, 'lxml')
            siteIdDiv = soup.find('div', attrs={'id': 'bizIdLablel'})
            if siteIdDiv is not None:
                siteId = int(siteIdDiv.text.replace('id:', '').strip())
                self.siteId = siteId
        except Exception as e:
            logger.exception('Exception')
            pass

    def extractAggregateRating(self):
        result = 0

        try:
            soup = BeautifulSoup(self.scrapedRawData, 'lxml')
            ratingValueDiv = soup.find('span', attrs={'itemprop': 'ratingValue'})
            if ratingValueDiv is not None:
                rating = float(ratingValueDiv.text.strip())
                result = rating
        except Exception as e:
            logger.exception('Exception')
            pass

        return result

    def extractTotalRatings(self):
        result = 0

        try:
            soup = BeautifulSoup(self.scrapedRawData, 'lxml')
            ratingCountDiv = soup.find('span', attrs={'itemprop': 'ratingCount'})
            if ratingCountDiv is not None:
                rating = float(ratingCountDiv.text.strip())
                result = rating
        except Exception as e:
            logger.exception('Exception')
            pass

        return result

    def fetchReviews(self, totalReviews):
        result = []

        try:
            reviewFormatter = ReviewFormatter(self.platformName)
            #reviews: List[Review]

            if config.get('scraper_mode') == 'online':
                self.siteHeaders['authority'] = 'www.judysbook.com'

            soup = BeautifulSoup(self.scrapedRawData, 'lxml')
            if soup is not None:
                scrape = True

                while scrape is True:
                    scrape = False
                    reviewsDivObject = soup.findAll('div', attrs={'class': 'reviewItemWrapper'})
                    if reviewsDivObject is not None:
                        for reviewDiv in reviewsDivObject:
                            reviewObj = {
                                'review_id': 0,
                                'user_id': 0,
                                'name': None,
                                'rating': 0,
                                'headline': None,
                                'review': None,
                                'date': None,
                                'review_response_date': None
                            }

                            reviewTitleDiv = reviewDiv.find('a', attrs={'id': re.compile('hplReviewTitle')})
                            if reviewTitleDiv is not None:
                                reviewUrl = reviewTitleDiv['href']
                                reviewUrlArr = reviewUrl.split('/')
                                if type(reviewUrlArr) is list:
                                    if len(reviewUrlArr) > 0:
                                        reviewObj['review_id'] = reviewUrlArr[-1]
                                        reviewObj['user_id'] = reviewUrlArr[1]

                                reviewTitleSpan = reviewTitleDiv.findChild('span')
                                if reviewTitleSpan is not None:
                                    reviewObj['headline'] = reviewTitleSpan.text.strip()

                            reviewPublishedDateSpan = reviewDiv.find('span', attrs={'class': 'date'})
                            if reviewPublishedDateSpan is not None:
                                reviewObj['date'] = reviewPublishedDateSpan.text.strip()

                            reviewContentDiv = reviewDiv.find('div', attrs={'class': 'reviewContent'})
                            if reviewContentDiv is not None:
                                reviewObj['review'] = reviewContentDiv.text.strip().replace('\n                        more','')

                            reviewAuthorATag = reviewDiv.find('a', attrs={'id': 'hplAuthor'})
                            if reviewAuthorATag is not None:
                                reviewAuthorSpan = reviewAuthorATag.findChild('span')
                                if reviewAuthorSpan is not None:
                                    pattern = r"by (.*?) at"
                                    matches = re.findall(pattern, reviewAuthorSpan.text.strip(), re.MULTILINE)
                                    if len(matches) > 0:
                                        reviewObj['name'] = matches[0].strip()

                            reviewRatingOuterDiv = reviewDiv.find('div', attrs={'class': 'authorInfo'})
                            if reviewRatingOuterDiv is not None:
                                reviewRatingInputTags = reviewDiv.findChildren('input')
                                if reviewRatingInputTags is not None:
                                    if len(reviewRatingInputTags) > 0:
                                        for reviewRatingInputTag in reviewRatingInputTags:
                                            try:
                                                reviewObj['rating'] = float(reviewRatingInputTag['value'].strip())
                                                break
                                            except KeyError as e:
                                                pass

                            formattedReview = reviewFormatter.format(reviewObj)
                            result.append(formattedReview)

                    sleep(randrange(1, 3))
                    nextPageUrl = self._getNextPageUrl(soup)
                    if nextPageUrl is not False:
                        scrapedRawData = Network.fetch(Network.GET, nextPageUrl, self.siteHeaders)
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
            nextPageLinkObjects = soup.findAll("a", attrs={'class': 'PagerHyperlinkStyle'})
            if nextPageLinkObjects is not None:
                if type(nextPageLinkObjects) is list:
                    if len(nextPageLinkObjects) > 0:
                        nextPageLinkObject = nextPageLinkObjects[-1]
                        if nextPageLinkObject.text == ' Next 1> ':
                            result = f"https://www.judysbook.com/{nextPageLinkObject['href']}"
                            logger.info(f'Next Page Url: {result}')

        return result

    def scrapeListings(self, url):
        pass

    def scrapeImages(self, url, imageSavePath):
        pass
