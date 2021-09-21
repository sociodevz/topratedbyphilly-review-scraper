from typing import Pattern
import requests
import sys
import re
import os
import json
import math
import datetime
import html
import time
import traceback
import wget
from random import randint, random, randrange
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

from reviews.common.network import Network
from reviews.common.config import config
from reviews.main.reviews_formatter import ReviewFormatter
from reviews.common.functions import *
from reviews.common.logger import logger
from reviews.main.scraper_interface import IScraper


class Yelp(IScraper):

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
        scrape = True

        while scrape is True:
            scrape = False

            resultArr = Network.fetch(Network.GET, None, url)

            if resultArr['code'] == 200:
                bodyHtml = resultArr['body']

                if bodyHtml != '':
                    companyNameArr = []
                    companyUrlArr = []
                    companyRatingArr = []
                    companyDetailsArr = []

                soup = BeautifulSoup(bodyHtml, 'lxml')

                jsonRawStr = None
                jsonElementList = soup.find_all('script', attrs={'type': 'application/json', 'data-hypernova-key': re.compile('yelpfrontend.*')})
                if jsonElementList is not None:
                    for jsonElement in jsonElementList:
                        jsonRawStr = jsonElement.contents[0]

                if jsonRawStr is not None:
                    regex = r"--(.*)--"
                    matches = re.findall(regex, jsonRawStr, re.MULTILINE | re.IGNORECASE)
                    if len(matches) > 0:
                        jsonStr = html.unescape(matches[0])
                        try:
                            jsonArr = json.loads(jsonStr)
                            if 'legacyProps' in jsonArr:
                                if 'searchAppProps' in jsonArr['legacyProps']:
                                    if 'searchPageProps' in jsonArr['legacyProps']['searchAppProps']:
                                        if 'mainContentComponentsListProps' in jsonArr['legacyProps']['searchAppProps']['searchPageProps']:
                                            businessesList = jsonArr['legacyProps']['searchAppProps']['searchPageProps']['mainContentComponentsListProps']
                                            for business in businessesList:
                                                if 'bizId' in business:
                                                    if business['searchResultBusiness']['isAd'] is False:
                                                        companyNameArr.append(business['searchResultBusiness']['name'])
                                                        companyUrlArr.append('https://www.yelp.com' + business['searchResultBusiness']['businessUrl'])
                                                        companyRatingArr.append(business['searchResultBusiness']['rating'])
                                                        companyDetailsArr.append(business['searchResultBusiness']['reviewCount'])

                            fields = ['name', 'url', 'rating', 'total_ratings']
                            rows = []

                            for (name, url, rating, totalRatings) in zip(companyNameArr, companyUrlArr, companyRatingArr, companyDetailsArr):
                                rows.append([name, url, rating, totalRatings])

                            ts = datetime.datetime.now().timestamp()
                            writeCSV(csvFileNamePath, fields, rows)

                            # lets try and extract next page url
                            nextPageUrlElement = soup.find('a', attrs={'class': 'next-link'})
                            if nextPageUrlElement is not None:
                                url = nextPageUrlElement['href']
                                time.sleep(2)
                                scrape = True
                        except Exception as e:
                            error = e
                            pass

    def scrapeImages(self, url, imageSavePath):
        PATH = f"{config.get('project_physical_root_path')}chromedriver"
        options = Options()
        options.add_argument('--no-sandbox')
        options.headless = config.get('chrome_headless_mode')
        browser = webdriver.Chrome(PATH, options=options)

        urlsList = [url]  # future provision for multiple urls via cli

        for url in urlsList:

            try:
                if url.find('biz_photos') == -1:
                    url = url.replace('https://www.yelp.com/biz/', 'https://www.yelp.com/biz_photos/')

                scrape = True
                browser.get(url)
                time.sleep(5)
                cntr = 1
                while scrape is True:
                    scrape = False
                    # val = input("Continue:")

                    websiteName = None
                    soup = BeautifulSoup(browser.page_source, 'lxml')
                    titleElement = soup.find('title')
                    websiteName = titleElement.text.replace('Photos for ', '').replace(' - Yelp', '').strip()

                    projectName = 'All'
                    projectNamePath = f"{imageSavePath}/{websiteName}/{projectName}"
                    Path(projectNamePath).mkdir(parents=True, exist_ok=True)
                    images = soup.findAll('img', attrs={'class': 'photo-box-img'})
                    if images is not None:
                        for image in images:
                            timestamp = str(time.time()).replace('.', '')
                            imageUrl = re.sub(r"bphoto/(.*?)/(.*)\.(.*)", "bphoto/\\1/o.\\3", image['src'])
                            try:
                                fileNamePath = f"{projectNamePath}/{cntr}.jpg"
                                image_filename = wget.download(imageUrl, out=fileNamePath)
                                cntr += 1
                            except Exception as e:
                                pass

                    try:
                        element = browser.find_element_by_class_name("next")
                        if element is not None:
                            ActionChains(browser).move_to_element(element).click(element).perform()
                            time.sleep(5)
                            scrape = True
                    except Exception as e:
                        pass
            except Exception as e:
                tb = traceback.format_exc()
                print(tb)
                error = e
                print(error)
                #browser.quit()
                pass

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
        if type(jsonStr) is not dict:
            return []

        jsonStr = fixLocalBusinessJSON(jsonStr)

        return {
            "id": self.extractId(),
            "name": jsonStr['name'],
            "telephone": jsonStr['telephone'],
            "address": jsonStr['address'],
            "reviews": self.fetchReviews(self.generateReviewUrl(self.extractId()), jsonStr['aggregateRating']['reviewCount']),
            "rating": {
                "aggregate": jsonStr['aggregateRating']['ratingValue'],
                "total": jsonStr['aggregateRating']['reviewCount'],
            },
        }

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\">({\"@context\":\"https://schema.org\",\"@type\":\"LocalBusiness\".*?)</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE)

        if len(matches) > 0:
            result = json.loads(matches[0])

        return result

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

    def fetchReviews(self, reviewBaseUrl, totalReviews):
        result = []

        reviewFormatter = ReviewFormatter(self.platformName)
        for i in range(math.ceil(int(totalReviews/10))+1):
            if i < 1:
                appendPage = ''
            else:
                appendPage = f"&start={i*10}"

            reviewUrl = f"{reviewBaseUrl}{appendPage}"
            scrapedRawData = Network.fetch(Network.GET, self.siteHeaders, reviewUrl)
            if(scrapedRawData['code'] == 200):
                reviewsRawData = json.loads(scrapedRawData['body'])
                if 'reviews' in reviewsRawData:
                    if len(reviewsRawData['reviews']) > 0:
                        for review in reviewsRawData['reviews']:
                            formattedReview = reviewFormatter.format(review)
                            result.append(formattedReview)
                sleep(randrange(1, 3))

        return result
