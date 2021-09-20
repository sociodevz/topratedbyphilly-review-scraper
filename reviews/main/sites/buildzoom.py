from typing import Pattern
import requests
import sys
import re
import os
import json
import math
import pickle
import time
from random import randint, random, randrange
from time import sleep
from bs4 import BeautifulSoup
from reviews.common.network import Network
from reviews.common.config import config
from reviews.main.reviews_formatter import ReviewFormatter
from reviews.common.functions import *
from reviews.common.logger import logger
from reviews.common.useragents import UserAgent
from reviews.main.scraper_interface import IScraper


class Buildzoom(IScraper):

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

    def scrapeListings(self, url, csvFileNamePath):
        userAgent = UserAgent()
        headersArr = userAgent.getRandom()

        headersArr['referer'] = 'https://www.buildzoom.com/'
        headersArr['authority'] = 'www.buildzoom.com'

        scrape = True

        while scrape is True:
            scrape = False
            headersArr['path'] = url.replace('https://www.buildzoom.com', '')
            resultArr = Network.fetch(Network.GET, headersArr, url)

            if resultArr['code'] == 200:
                bodyHtml = resultArr['body']

                if bodyHtml != '':
                    companyNameArr = []
                    companyUrlArr = []
                    companyRatingArr = []
                    companyDetailsArr = []

                    try:
                        soup = BeautifulSoup(bodyHtml, 'lxml')
                        mainWrapperDiv = soup.find('div', attrs={'class': 'search-result-contractors'})
                        if mainWrapperDiv is not None:
                            companyMainDivList = mainWrapperDiv.find_all('div', attrs={'class': 'search-result-contractor-secondary'})
                            if companyMainDivList is not None:
                                for companyMainDiv in companyMainDivList:
                                    companyNameList = companyMainDiv.find_all('div', attrs={'itemprop': 'name'})
                                    if companyNameList is not None:
                                        for companyName in companyNameList:
                                            companyNameArr.append(companyName.text.strip())

                                    companyUrlList = companyMainDiv.find_all('a', attrs={'itemprop': 'url'})
                                    if companyUrlList is not None:
                                        for companyUrl in companyUrlList:
                                            companyUrlArr.append('https://www.buildzoom.com' + companyUrl['href'].strip())

                                    companyRating = 0
                                    companyRatingList = companyMainDiv.find_all('span', attrs={'itemprop': 'ratingValue'})
                                    if companyRatingList is not None and len(companyRatingList) > 0:
                                        for companyRating in companyRatingList:
                                            companyRating = companyRating.text.strip()
                                    else:
                                        companyRatingListOuter = companyMainDiv.find('div', attrs={'class': 'contractor-reviews'})
                                        if companyRatingListOuter is not None:
                                            spanRatingObj = companyRatingListOuter.find('span', attrs={'class': 'hidden'})
                                            if spanRatingObj is not None:
                                                companyRating = spanRatingObj.text.strip()

                                    companyRatingArr.append(companyRating)

                                    companyReviewsCount = 0
                                    companyRatingCountList = companyMainDiv.find_all('span', attrs={'itemprop': 'reviewCount'})
                                    if companyRatingCountList is not None and len(companyRatingCountList) > 0:
                                        for companyRatingCount in companyRatingCountList:
                                            companyReviewsCount = companyRatingCount.text.strip()
                                    else:
                                        companyReviewsListOuter = companyMainDiv.find('div', attrs={'class': 'contractor-reviews'})
                                        if companyReviewsListOuter is not None:
                                            aHrefObj = companyReviewsListOuter.find('a')
                                            if aHrefObj is not None:
                                                spanReviewCountObj = aHrefObj.find('span')
                                                if spanReviewCountObj is not None:
                                                    companyReviewsCount = spanReviewCountObj.text.strip()

                                    companyDetailsArr.append(companyReviewsCount)

                                fields = ['name', 'url', 'rating', 'total_ratings']
                                rows = []

                                for (name, landingUrl, rating, totalRatings) in zip(companyNameArr, companyUrlArr, companyRatingArr, companyDetailsArr):
                                    rows.append([name, landingUrl, rating, totalRatings])

                                writeCSV(csvFileNamePath, fields, rows)

                                # lets try and extract next page url
                                nextPageUrlElement = soup.find('a', attrs={'rel': 'next'})
                                if nextPageUrlElement is not None:
                                    scrape = True
                                    headersArr['referer'] = url
                                    url = nextUrl = 'https://www.buildzoom.com' + nextPageUrlElement['href']
                                    time.sleep(3)
                    except Exception as e:
                        error = e
                        print(e)
                        pass

    def scrapeImages(self, url, imageSavePath):
        return 'Not yet implemented'

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
                        result['telephone'] = contactInnerObj.text.strip()

        except Exception as e:
            logger.exception('Exception')
            pass

        return result

    def fetchReviews(self, totalReviews):
        result = []

        try:
            reviewFormatter = ReviewFormatter(self.platformName)

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
            logger.exception('Exception')
            pass

        return result
