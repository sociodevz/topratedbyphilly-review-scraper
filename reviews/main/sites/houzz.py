from requests.sessions import extract_cookies_to_jar
from reviews.common.useragents import UserAgent
from typing import Pattern
import requests
import sys
import re
import os
import json
from reviews.common.network import Network
from reviews.common.config import config


class Houzz:
    scrapedRawData = ''
    scrapedRawReviewsData = ''

    def __init__(self):
        print('Initalized Houzz Engine')
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

        result = self.processRawData()

        headersArr.update({
            'referer': url,
            'x-requested-with': 'XMLHttpRequest',
        })
        paginationResultArr = Network.fetch(result['review_url'], headersArr)
        print(result['review_url'])
        print(paginationResultArr['body'])
        exit()
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

        return {
            "id": jsonStr['@id'],
            "name": jsonStr['name'],
            "telephone": jsonStr['telephone'],
            "address": jsonStr['address'],
            "reviews": [],
            "rating": {
                "aggregate": jsonStr['aggregateRating']['ratingValue'],
                "total": jsonStr['aggregateRating']['reviewCount'],
            },
            "review_url": self.extractNextPageUrl()
        }

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\">(.*?)</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE | re.DOTALL)

        if len(matches) > 0:
            result = json.loads(matches[0].strip())

        return result[0]

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

    def extractCSRF(self, cookieStr):
        result = None

        pattern = r"_csrf=(.*?);"
        matches = re.findall(pattern, cookieStr, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0].strip()

        return result

