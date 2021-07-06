from typing import Pattern
import requests
import sys
import re
import os
import json
from reviews.common.network import Network
from reviews.common.config import config


class Yelp:

    scrapedRawData = ''

    def __init__(self):
        print('Initalized Yelp Engine')
        pass

    def scrapeURL(self, url):
        returnArr = []

        if config.get('scraper_mode') == 'online':
            headersArr = {}
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
        returnArr.append(result)

        return returnArr

    def processRawData(self):
        jsonStr = self.extractJSON()

        return {
            "id": self.extractId(),
            "name": jsonStr['name'],
            "telephone": jsonStr['telephone'],
            "address": jsonStr['address'],
            "reviews": jsonStr['review'],
            "rating": {
                "aggregate": jsonStr['aggregateRating']['ratingValue'],
                "total": jsonStr['aggregateRating']['reviewCount'],
            },
            "review_url": self.generateReviewUrl(self.extractId())
        }

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\">({\"@context\":\"https://schema.org\",\"@type\":\"LocalBusiness\".*?)</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0]

        return json.loads(result)

    def extractId(self):
        result = None
        pattern = r"meta.*?name=\"yelp-biz-id\" content=\"(.*?)\""
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0]

        return result

    def extractName(self):
        result = None
        pattern = r"meta name=\"yelp-biz-id\" content=\"(.*?)\""
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0]

        return result

    def generateReviewUrl(self, businessId):
        return f"https://www.yelp.com/biz/{businessId}/review_feed?rl=en&q=&sort_by=relevance_desc"

