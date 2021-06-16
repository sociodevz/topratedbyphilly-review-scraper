from requests.sessions import extract_cookies_to_jar
from reviews.common.useragents import UserAgent
from typing import List, Pattern
import requests
import sys
import re
import os
import json
from reviews.common.network import Network
from reviews.common.config import config


class Homeadvisor:
    scrapedRawData = ''
    scrapedRawReviewsData = ''

    def __init__(self):
        print('Initalized Homeadvisor Engine')
        pass

    def scrapeURL(self, url):
        returnArr = []

        if config.get('scraper_mode') == 'online':
            headersArr = {}

            userAgent = UserAgent()
            userAgentList = userAgent.getRandom()
            headersArr.update(userAgentList)
            scrapedRawData = Network.fetch(url, headersArr)

            if(scrapedRawData['code'] == 200):
                self.scrapedRawData = scrapedRawData['body']
        elif config.get('scraper_mode') == 'offline':
            filePath = os.path.realpath(__file__)
            currentFileName = os.path.basename(__file__)
            filePath = filePath.replace(currentFileName, '')
            file = open(f"{filePath}/sample_data/{url}")
            self.scrapedRawData = file.read()

        if self.scrapedRawData is not None:
            result = self.processRawData()
            returnArr.append(result)

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
        jsonStr = self.extractJSON()['@graph'][1]

        return {
            "id": self.extractId(jsonStr['@id']),
            "name": jsonStr['name'],
            "telephone": jsonStr['telephone'],
            "address": jsonStr['address'],
            "reviews": jsonStr['review'],
            "rating": {
                "aggregate": jsonStr['aggregateRating']['ratingValue'],
                "total": jsonStr['aggregateRating']['reviewCount'],
            },
            "review_url": self.extractNextPageUrl()
        }

    def extractId(self, dataStr):
        result = None

        pattern = r"rated\..*?\.(.*?)\.html"
        matches = re.findall(pattern, dataStr, re.MULTILINE)

        if len(matches) > 0:
            result = int(matches[0].strip())

        return result

    def extractName(self):
        result = None

        pattern = r"\"companyName\":\"(.*?)\","
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0].strip()

        return result

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\">(.*?)</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE | re.DOTALL)

        if len(matches) > 0:
            result = self.reviewsCleanup(matches[0].strip())
            result = json.loads(result)

        return result

    def extractNextPageUrl(self):
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
            result = f'https://www.houzz.com/j/ajax/profileReviewsAjax?userId={userId}&proId={professionalId}&fromItem=1&itemsPerPage=45'

        return result

    def reviewsCleanup(self, reviewJSON):
        result = reviewJSON

        result = result.replace(',"@type":"Person"', '')
        result = result.replace(',"@type":"Review"', '')
        result = result.replace(',"@type":"Rating"', '')
        result = result.replace(',"@type":"Thing"', '')
        result = result.replace(',"@type":"PostalAddress"', '')

        return result

