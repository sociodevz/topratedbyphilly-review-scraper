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


class Buildzoom:

    siteUrl = None
    scrapedRawData = None
    siteHeaders = None

    def __init__(self):
        print('Initalized Buildzoom Engine')
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

        return {
            "id": jsonStr['id'],
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
        result = {
            'id': 0,
            'name': None,
            'telephone': None,
            'address': None,
            'aggregateRating': {
                'ratingValue': 0,
                'reviewCount': 0,
            },
        }

        try:
            soup = BeautifulSoup(self.scrapedRawData, 'lxml')
            if soup is not None:
                mainSection = soup.find(attrs={"id": "main"})
                companyDetailsJSON = mainSection['ng-init'].replace('init(', '')
                companyDetailsJSON = companyDetailsJSON.replace("})", '}')
                companyDetailsJSON = companyDetailsJSON.lstrip("'")
                companyDetailsArr = json.loads(companyDetailsJSON)
                result['id'] = companyDetailsArr['id']
                result['name'] = companyDetailsArr['business_name']

                ratingSection = soup.find_all(attrs={"class": "contractor-review-stars"})
                for tag in ratingSection:
                    subTag = tag.find("meta", attrs={"itemprop": "ratingValue"})
                    result['aggregateRating']['ratingValue'] = int(subTag['content'])

                    subTag = tag.find("span", attrs={"class": "contractor-rating-review-count"})
                    result['aggregateRating']['reviewCount'] = int(subTag.text)

                contactOuterObj = soup.find("div", attrs={"itemprop": "telephone"})
                if contactOuterObj is not None:
                    contactInnerObj = contactOuterObj.find("a")
                    if contactInnerObj is not None:
                        result['telephone'] = contactInnerObj.text

        except Exception as e:
            error = e
            pass

        return result

    def fetchReviews(self, totalReviews):
        result = []

        try:
            reviewFormatter = ReviewFormatter('buildzoom')

            soup = BeautifulSoup(self.scrapedRawData, 'lxml')
            if soup is not None:
                reviews = soup.find_all("li", attrs={"class": "review"})
                for review in reviews:
                    reviewObj = {}
                    reviewObj["id"] = int(review['data-review-id'])

                    # reviewer
                    reviewerNameOuterObj = review.find("span", attrs={"itemprop": "author"})
                    reviewerNameInnerObj = reviewerNameOuterObj.find("span", attrs={"itemprop": "name"})
                    reviewerName = "Anonymous"
                    if reviewerNameInnerObj is not None:
                        reviewerName = reviewerNameInnerObj.text
                    reviewObj["author"] = {"name": reviewerName}

                    # published date
                    reviewDateOuterObj = review.find("div", attrs={"class": "review-date"})
                    reviewDateInnerObj = reviewDateOuterObj.find("meta", attrs={"itemprop": "datePublished"})
                    reviewObj['datePublished'] = reviewDateInnerObj['content']

                    # main review block
                    userReviewOuterObj = review.find("div", attrs={"class": "userreview"})

                    # job type
                    # reviewHeadlineObj = review.find("div", attrs={"class": "header-subject"})
                    # reviewObj["headline"] = reviewHeadlineObj.text

                    # rating
                    userRatingInnerObj = userReviewOuterObj.find("meta", attrs={"itemprop": "ratingValue"})
                    reviewObj["reviewRating"] = {"ratingValue": userRatingInnerObj['content']}

                    # actual review text
                    reviewBodyOuterObj = review.find("span", attrs={"itemprop": "reviewBody"})
                    reviewBodyInnerObj = reviewBodyOuterObj.find("p")
                    reviewObj["reviewBody"] = reviewBodyInnerObj.text

                    # actual review text
                    reviewBodyOuterObj = review.find("span", attrs={"itemprop": "reviewBody"})
                    reviewBodyInnerObj = reviewBodyOuterObj.find("p")
                    reviewObj["reviewBody"] = reviewBodyInnerObj.text

                    # owner response
                    reviewObj["reviewResponse"] = None
                    businessResponseObj = review.find("div", attrs={"class": "review-response-content"})
                    if businessResponseObj is not None:
                        reviewObj["reviewResponse"] = businessResponseObj.text.strip()

                    formattedReview = reviewFormatter.format(reviewObj)
                    result.append(formattedReview)
        except Exception as e:
            error = e
            pass

        return result
