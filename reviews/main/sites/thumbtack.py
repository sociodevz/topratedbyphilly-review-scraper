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
from reviews.common.logger import logger


class Thumbtack:

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

        self.siteId = self.extractId()

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
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = json.loads(matches[0].strip())

        return result[0]

    def extractName(self):
        result = None
        pattern = r"\"businessName\":\"(.*?)\","
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0]

        return result

    def extractId(self):
        result = None
        pattern = r"\\\"servicePK\\\":\\\"(.*?)\\\""
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = int(matches[0])

        return result

    def extractCategoryId(self):
        result = 'null'
        pattern = r"\\\"categoryPK\\\":\\\"(.*?)\\\""
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = int(matches[0])

        return result

    def extractProjectId(self):
        result = 'null'
        pattern = r"\\\"projectPk\\\":\\\"(.*?)\\\""
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = int(matches[0])

        return result

    def extractQuestionId(self):
        result = 'null'
        pattern = r"\\\"projectPk\\\":\\\"(.*?)\\\""
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = int(matches[0])

        return result

    def extractZipCode(self):
        result = 'null'
        pattern = r"\\\"zipCode\\\":\\\"(.*?)\\\""
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = int(matches[0])

        return result

    def extractProlistRequestId(self):
        result = 'null'
        pattern = r"\\\"proListRequestPk\\\":\\\"(.*?)\\\""
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = int(matches[0])

        return result

    def extractRelevantServicesCategories(self):
        result = 'null'
        pattern = r"\"relevantServiceCategoryPks\\\":(.*?]),"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0]

        return result

    def extractTextAnswers(self):
        result = 'null'
        pattern = r"\"textAnswers\\\":(.*?]),"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0]

        return result

    def extractQueryType(self):
        result = 'null'
        pattern = r"\"searchQuery\\\":(.*?),"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0]

        return result

    def extractReviewPk(self):
        result = 'null'
        pattern = r"\"reviewPk\\\":(.*?),"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0]

        return result

    def generateReviewUrl(self):
        return f"https://app.thumbtack.com/graphql"

    def fetchReviews(self, reviewBaseUrl, totalReviews):
        result = []

        maxResultPerPage = 5
        pageOffSet = 0

        self.siteHeaders.update({
                'authority': 'app.thumbtack.com',
                'origin': 'https://www.thumbtack.com',
                'referer': 'https://www.thumbtack.com',
                'x-requested-with': 'XMLHttpRequest',
                'content-type': 'application/json',
            })

        reviewFormatter = ReviewFormatter(self.platformName)
        for i in range(math.ceil(int(totalReviews/maxResultPerPage))+1):
            reviewUrl = reviewBaseUrl
            pageOffSet = i * maxResultPerPage

            payloadArr = data = '{"operationName":"ServicePageReviews","variables":{"reviewsPageToken":"{\\"Input\\":{\\"servicePK\\":\\"' + str(self.siteId) + '\\",\\"supportedSections\\":[\\"HEADER\\",\\"BUSINESS_INFO\\",\\"SECONDARY_CTAS_V2\\",\\"QUESTIONS\\",\\"SPECIALTIES\\",\\"REVIEWS\\",\\"MEDIA\\",\\"PAST_PROJECTS\\",\\"ACTION_CARD_V2_PRECONTACT\\",\\"ACTION_CARD_V2_POSTCONTACT\\",\\"CREDENTIALS\\",\\"SAFETY_MEASURES\\",\\"BREADCRUMBS\\",\\"INTERNAL_LINKS\\"],\\"categoryPK\\":\\"' + str(self.extractCategoryId()) + '\\",\\"projectPk\\":null,\\"keywordPk\\":null,\\"isSponsored\\":null,\\"searchFormAnswers\\":[{\\"questionID\\":null,\\"dateAnswers\\":null,\\"dateAndTimeAnswers\\":null,\\"textAnswers\\":null,\\"selectedAnswers\\":null,\\"selectedWithTextAnswers\\":null,\\"imageUploadAnswers\\":null}],\\"servicePageToken\\":null,\\"requestPK\\":null,\\"quotePK\\":null,\\"searchQuery\\":\\"Bathroom Remodel\\",\\"source\\":null,\\"zipCode\\":null,\\"proListRequestPk\\":null,\\"relevantServiceCategoryPks\\":null,\\"supportedIntroTypes\\":[\\"availability\\",\\"availability_with_instant_book\\",\\"availability_with_request_to_book\\",\\"call\\",\\"contact\\",\\"estimation\\",\\"instant_consult\\",\\"phone_consultation\\",\\"service_call\\"],\\"supportedMediaTypes\\":[\\"IMAGE\\",\\"PROJECT\\",\\"VIDEO\\",\\"REVIEW\\"],\\"queryType\\":null,\\"reviewPk\\":null,\\"instantBookSlotsInput\\":null},\\"Offset\\":\\"' + str(pageOffSet) + '\\"}"},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"621f284bbe86ebc6cc9159dcb64dfb79345faa649cc71042537d92c5a4900319"}}}'

            scrapedRawData = Network.fetch(Network.POST, reviewUrl, self.siteHeaders, payloadArr)
            if(scrapedRawData['code'] == 200):
                reviewsRawData = json.loads(scrapedRawData['body'])
                if 'data' in reviewsRawData:
                    if 'servicePageReviews' in reviewsRawData['data']:
                        if 'items' in reviewsRawData['data']['servicePageReviews']:
                            reviews = reviewsRawData['data']['servicePageReviews']['items']
                            if len(reviews) > 0:
                                for review in reviews:
                                    formattedReview = reviewFormatter.format(review['review'])
                                    result.append(formattedReview)
                sleep(randrange(1, 3))

        return result
