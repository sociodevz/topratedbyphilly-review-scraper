from typing import Pattern
import requests
import sys
import re
import os
import json
import math
import pickle
import traceback
from random import randint, random, randrange
from time import sleep
from bs4 import BeautifulSoup
from reviews.common.network import Network
from reviews.common.config import config
from reviews.main.reviews_formatter import ReviewFormatter
from reviews.common.functions import *
from reviews.common.logger import logger
from reviews.main.scraper_interface import IScraper


class Bestpickreports(IScraper):

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
        #self.siteUrl = jsonStr['url']
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
        result = fixLocalBusinessJSON({})

        try:
            soup = BeautifulSoup(self.scrapedRawData, 'lxml')

            companyNameObj = soup.find("div", attrs={"class": "company-name"})
            if companyNameObj is not None:
                result['name'] = companyNameObj.text.strip()

            companyTelObj = soup.find("div", attrs={"itemprop": "telephone"})
            if companyTelObj is not None:
                result['telephone'] = companyTelObj.text.strip()

            companyAddressOutterObj = soup.find("div", attrs={"itemprop": "address"})
            if companyAddressOutterObj is not None:
                companyAddressInnerObj = companyAddressOutterObj.find_all("span")
                if len(companyAddressInnerObj) > 0:
                    result['address'] = {}
                    for companyAddressDetailObj in companyAddressInnerObj:
                        result['address'][companyAddressDetailObj['itemprop']] = companyAddressDetailObj.text.strip()

            companyRatingOutterObj = soup.find("div", attrs={"class": "company-rating-text"})
            if companyRatingOutterObj is not None:
                companyRatingValueObj = companyRatingOutterObj.find("span", attrs={"itemprop": "ratingValue"})
                if companyRatingValueObj is not None:
                    result['aggregateRating']['ratingValue'] = float(companyRatingValueObj.text)

                companyReviewCountObj = companyRatingOutterObj.find("span", attrs={"itemprop": "reviewCount"})
                if companyReviewCountObj is not None:
                    result['aggregateRating']['reviewCount'] = int(companyReviewCountObj.text)

        except Exception as e:
            logger.exception('Exception')
            print(e)

        return result

    def extractId(self):
        result = None
        pattern = r"\/Contractor\/GetTestimonials\?contractorId=(.*?)&categoryId"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = int(matches[0])

        return result

    def generateReviewUrl(self):
        result = None

        pattern = r"var link = \"(\/Contractor\/GetTestimonials\?contractorId=(.*?)&categoryId=(.*?)&areaId=(.*?))\";"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            contactorSpecificUrl = matches[0][0]
            result = f"https://www.bestpickreports.com{contactorSpecificUrl}&page=PAGE_NUMBER&rating=5&ratingSort=&dateStart=&dateEnd=&dateSort=desc"

        return result

    def fetchReviews(self, reviewBaseUrl, totalReviews):
        result = []

        try:

            self.siteHeaders.update({
                'referer': self.siteUrl,
                'x-requested-with': 'XMLHttpRequest',
            })

            reviewFormatter = ReviewFormatter(self.platformName)
            limitPerPage = 100
            for i in range(math.ceil(int(totalReviews/limitPerPage))+1):
                reviewUrl = reviewBaseUrl.replace('PAGE_NUMBER', str(i))

                scrapedRawData = Network.fetch(Network.GET, self.siteHeaders, reviewUrl)
                if(scrapedRawData['code'] == 200):
                    reviewsRawData = scrapedRawData['body']
                    soup = BeautifulSoup(reviewsRawData, 'lxml')
                    reviewsObj = soup.find_all("div", attrs={"itemprop": "review"})
                    if reviewsObj is not None:
                        for reviewObj in reviewsObj:
                            review = {}
                            review['id'] = 0
                            review['author'] = {"name": ""}
                            review['reviewRating'] = {"ratingValue": 0}
                            review['reviewBody'] = None
                            review['datePublished'] = None
                            review['reviewResponse'] = None

                            reviewDateObj = reviewObj.find("meta", attrs={"itemprop": "datePublished"})
                            if reviewDateObj is not None:
                                review['datePublished'] = reviewDateObj['content']

                            reviewAuthorObj = reviewObj.find("span", attrs={"itemprop": "author"})
                            if reviewAuthorObj is not None:
                                review['author']['name'] = reviewAuthorObj.text.strip()

                            reviewRatingObj = reviewObj.find("meta", attrs={"itemprop": "ratingValue"})
                            if reviewRatingObj is not None:
                                review['reviewRating']['ratingValue'] = reviewRatingObj['content']

                            reviewTextObj = reviewObj.find("p", attrs={"itemprop": "reviewBody"})
                            if reviewTextObj is not None:
                                review['reviewBody'] = reviewTextObj.text.strip()

                            formattedReview = reviewFormatter.format(review)
                            result.append(formattedReview)
                    sleep(randrange(1, 3))
        except Exception as e:
            logger.exception('Exception')
            pass

        return result

    def scrapeListings(self, url):
        pass

    def scrapeImages(self, url, imageSavePath):
        pass
