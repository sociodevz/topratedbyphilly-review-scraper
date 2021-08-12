import requests
import sys
import json
import math
import re
import os
from random import randint, random, randrange
from time import sleep
from reviews.common.network import Network
from reviews.common.config import config
from reviews.main.reviews_formatter import ReviewFormatter
from reviews.common.functions import *
from reviews.common.logger import logger
from bs4 import BeautifulSoup


class Topratedlocal:

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

        return returnArr

    def scrapeDirectory(self, url, category):
        resultArr = Network.fetch(Network.GET, url)

        if resultArr['code'] == 200:
            bodyHtml = resultArr['body']

            if bodyHtml != '':
                companyNameArr = []
                companyUrlArr = []
                companyRatingArr = []
                companyDetailsArr = []

                soup = BeautifulSoup(bodyHtml, 'lxml')
                mainWrapperDiv = soup.find('div', attrs={'id': 'w0'})
                if mainWrapperDiv is not None:
                    companyNameList = mainWrapperDiv.find_all('a', attrs={'class': 'listing__heading'})
                    if companyNameList is not None:
                        for cntr, companyNameObj in enumerate(companyNameList):
                            companyNameArr.append(companyNameObj.text.strip('.').split('.')[-1].strip())
                            companyUrlArr.append("https://www.topratedlocal.com" + str(companyNameObj['href']))

                    companyRatingList = mainWrapperDiv.find_all('span', attrs={'class': 'pill-section'})
                    if companyRatingList is not None:
                        for companyRatingObj in companyRatingList:
                            value = companyRatingObj.text.strip()
                            try:
                                float(value)
                                companyRatingArr.append(float(value))
                            except ValueError:
                                pass

                    children1 = mainWrapperDiv.find_all('div', attrs={'class': 'u-bottom5'})
                    if children1 is not None:
                        for child in children1:
                            parentObj = child.find_parent('div')
                            if parentObj is not None:
                                regex = (r"Of ([0-9]*) ratings?/.*?on\n"
                                        r"              ([0-9]*) verified review sites?, this business has an average rating of\n"
                                        r"        ([0-9.]*) stars\.\n"
                                        r"    This earns them a Rating Score™ of ([0-9.]*) which ranks them #([0-9]*) in the.*?area\.")
                                matches = re.findall(regex, bodyHtml, re.DOTALL | re.MULTILINE | re.IGNORECASE)
                                if len(matches) > 0:
                                    for match in matches:
                                        companyDetailsArr.append(match)

                    fields = ['name', 'url', 'rating', 'total_ratings', 'verified_sites', 'average_rating', 'rating_score']
                    rows = []

                    for (name, url, rating, detailedRating) in zip(companyNameArr, companyUrlArr, companyRatingArr, companyDetailsArr):
                        rows.append([name, url, rating, detailedRating[0], detailedRating[1], detailedRating[2], detailedRating[3]])

                    writeCSV(f"tmp/topratedlocal_{category}.csv", fields, rows)

