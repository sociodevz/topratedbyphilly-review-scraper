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
from reviews.common.logger import logger
from reviews.main.scraper_interface import IScraper


class Gaf(IScraper):

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
        self.siteUrl = jsonStr['url']
        self.extractId()

        return {
            "id": self.siteId,
            "name": jsonStr['name'],
            "telephone": jsonStr['telephone'],
            "address": jsonStr['address'],
            "reviews": self.fetchReviews(jsonStr['aggregateRating']['reviewCount']),
            "rating": {
                "aggregate": jsonStr['aggregateRating']['ratingValue'],
                "total": jsonStr['aggregateRating']['reviewCount'],
            },
        }

    def extractJSON(self):
        result = None
        pattern = r"<script type=application/ld\+json>(.*?)</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.DOTALL)

        if len(matches) > 0:
            result = json.loads(matches[0].strip())

        return result

    def extractId(self):
        try:
            self.siteId = int(self.siteUrl.replace('.htm', '').split('-')[-1])
        except Exception as e:
            pass

    def fetchReviews(self, totalReviews):
        result = []

        try:
            reviewFormatter = ReviewFormatter(self.platformName)

            soup = BeautifulSoup(self.scrapedRawData, 'lxml')
            if soup is not None:
                reviewsObj = soup.find_all("blockquote", attrs={"class": "customer-reviews-full-listing__inner"})
                for reviewObj in reviewsObj:
                    review = {}
                    review['id'] = 0
                    review['author'] = {"name": ""}
                    review['reviewRating'] = {"ratingValue": 0}
                    review['reviewBody'] = None
                    review['datePublished'] = None
                    review['reviewResponse'] = None

                    reviewPublishedObj = reviewObj.find("time", attrs={"class", "customer-reviews-full-listing__time"})
                    if reviewPublishedObj is not None:
                        review['datePublished'] = reviewPublishedObj['datetime']

                    reviewRatingObj = reviewObj.find("div", attrs={"class", "customer-reviews-full-listing__stars"})
                    if reviewRatingObj is not None:
                        review['reviewRating']['ratingValue'] = reviewRatingObj['data-score']

                    reviewTextObj = reviewObj.find("span", attrs={"class", "customer-reviews-full-listing__quote"})
                    if reviewTextObj is not None:
                        review['reviewBody'] = reviewTextObj.text.strip('"')

                    reviewAuthorObj = reviewObj.find("p", attrs={"class", "customer-reviews-full-listing__author"})
                    if reviewAuthorObj is not None:
                        reviewerName = reviewAuthorObj.text.strip('-')
                        reviewerName = reviewerName.strip()
                        reviewerName = reviewerName.replace('X.X,', 'Anonymous')
                        review['author']['name'] = reviewerName

                    formattedReview = reviewFormatter.format(review)
                    result.append(formattedReview)
        except Exception as e:
            logger.exception('Exception')
            pass

        return result
