import requests
import sys
import json
import math
import re
import os
import time
from random import randint, random, randrange
from time import sleep
from reviews.common.network import Network
from reviews.common.config import config
from reviews.main.reviews_formatter import ReviewFormatter
from reviews.common.functions import *
from reviews.common.logger import logger
from reviews.common.useragents import UserAgent
from reviews.main.scraper_interface import IScraper


class Bbb(IScraper):

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
        url = "https://www.bbb.org/search?find_country=USA&find_latlng=39.989654%2C-75.148976&find_loc=Philadelphia%2C%20PA&find_text=Plumber&page=1&sort=Relevance&touched=1"
        userAgent = UserAgent()
        headersArr = userAgent.getRandom()

        headersArr['referer'] = 'https://www.bbb.org'
        headersArr['authority'] = 'www.bbb.org'
        scrape = True

        while scrape is True:
            scrape = False

            # we need to add api so that we get json
            url = url.replace('https://www.bbb.org/search', 'https://www.bbb.org/api/search')
            headersArr['path'] = url.replace('https://www.bbb.org', '')

            resultArr = Network.fetch(Network.GET, url, headersArr)

            if resultArr['code'] == 200:
                jsonStr = resultArr['body']
                jsonArr = json.loads(jsonStr)

                if len(jsonArr) > 0:
                    companyNameArr = []
                    companyUrlArr = []
                    companyRatingArr = []
                    companyDetailsArr = []

                    try:
                        for result in jsonArr['results']:
                            businessName = result['businessName'].strip()
                            companyNameArr.append(result['businessName'].strip().replace('<em>', '').replace('</em>', ''))
                            companyUrlArr.append(result['reportUrl'].strip())
                            companyRatingArr.append(result['rating'])
                            companyDetailsArr.append(result['score'])

                        fields = ['name', 'url', 'rating', 'rating_score']
                        rows = []

                        for (name, landingUrl, rating, totalRatings) in zip(companyNameArr, companyUrlArr, companyRatingArr, companyDetailsArr):
                            rows.append([name, landingUrl, rating, totalRatings])

                        writeCSV(csvFileNamePath, fields, rows)

                        # lets try and extract next page url
                        currentPageNum = jsonArr['page']
                        totalPages = jsonArr['totalPages']
                        if currentPageNum < totalPages:
                            headersArr['referer'] = url.replace('api/', '')
                            scrape = True

                            regex = r"&page=(.*?)&"
                            nextPageNumber = currentPageNum + 1
                            subst = f"&page={nextPageNumber}&"
                            url = nextUrl = re.sub(regex, subst, url, 0, re.MULTILINE)
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
        jsonStr = self.extractJSON()
        jsonStr = fixLocalBusinessJSON(jsonStr)

        return {
            "id": self.extractBusinessId(),
            "name": jsonStr['name'],
            "telephone": jsonStr['telephone'],
            "address": jsonStr['address'],
            "reviews": self.fetchReviews(self.generateReviewUrl(), self.extractTotalReviews()),
            "rating": {
                "aggregate": self.extractAggregateReviewRating(),
                "total": self.extractTotalReviews(),
            },
        }

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\">.*?({\"@context\":\"https://schema\.org\",\"@type\":\"LocalBusiness\".*?)</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.DOTALL | re.MULTILINE)

        if len(matches) > 0:
            result = matches[0].strip().strip(';')

        return json.loads(result)

    def extractBusinessId(self):
        result = None

        try:
            result = int(self.siteUrl.split('-')[-1])
        except Exception as e:
            pass

        return result

    def extractBBBId(self):
        result = None

        try:
            result = self.siteUrl.split('-')[-2]
        except Exception as e:
            pass

        return result

    def extractAggregateReviewRating(self):
        result = 0

        pattern = r"</div><span class=\"MuiTypography-root.*?<strong>(.*?)</strong>/5"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = float(matches[0].strip())

        return result

    def extractTotalReviews(self):
        result = 0

        pattern = r"Average of (.*?) Customer Reviews"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = int(matches[0].strip())

        return result

    def generateReviewUrl(self):

        return f"https://www.bbb.org/api/businessprofile/customerreviews?page=PAGEID&pageSize=10&businessId={self.extractBusinessId()}&bbbId={self.extractBBBId()}&sort=reviewDate%20desc"

    def generateSiteCustomerReviewsUrl(self):

        return f"{self.siteUrl}/customer-reviews"

    def fetchReviews(self, reviewBaseUrl, totalReviews):
        result = []

        if self.siteHeaders is None:
            from reviews.common.useragents import UserAgent
            useragent = UserAgent()
            self.siteHeaders = useragent.getRandom()
            self.siteHeaders['referer'] = self.generateReviewUrl

        reviewFormatter = ReviewFormatter(self.platformName)
        for i in range(math.ceil(int(totalReviews/10))+1):
            reviewUrl = reviewBaseUrl.replace('PAGEID', str(i+1))
            scrapedRawData = Network.fetch(Network.GET, reviewUrl, self.siteHeaders)
            if(scrapedRawData['code'] == 200):
                reviewsRawData = json.loads(scrapedRawData['body'])
                if 'items' in reviewsRawData:
                    if len(reviewsRawData['items']) > 0:
                        for review in reviewsRawData['items']:
                            formattedReview = reviewFormatter.format(review)
                            result.append(formattedReview)
                sleep(randrange(1, 3))

        return result

