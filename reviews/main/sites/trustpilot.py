from typing import Pattern
import requests
import sys
import re
import os
import json
from reviews.common.network import Network
from reviews.common.config import config


class Trustpilot:

    scrapedRawData = ''

    def __init__(self):
        print('Initalized TrustPilot Engine')
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
            "id": jsonStr['@id'],
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

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\" data-business-unit-json-ld>\n(.*?)\n.*</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = json.loads(matches[0].strip())

        return result[0]

    def extractNextPageUrl(self):
        result = None
        pattern = r"<link rel=\"next\" href=\"(https://www.trustpilot.com/review/.*?)\" />"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = matches[0].strip()

        return result

