from requests.sessions import extract_cookies_to_jar
from reviews.common.useragents import UserAgent
from typing import Pattern
import requests
import sys
import re
import os
import json
import math
import time
import wget
import traceback

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


class Houzz(IScraper):

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
        return 'Not yet implemented'

    def scrapeImages(self, url, imageSavePath):
        PATH = f"{config.get('project_physical_root_path')}chromedriver"
        options = Options()
        options.add_argument('--no-sandbox')
        options.headless = config.get('chrome_headless_mode')

        urlsList = [url]  # future provision for multiple cli urls

        for url in urlsList:
            browser = webdriver.Chrome(PATH, options=options)

            try:
                originalUrl = url
                browser.get(originalUrl)
                time.sleep(5)
                val = input("Continue:")

                websiteName = None
                soup = BeautifulSoup(browser.page_source, 'lxml')
                websiteNameElement = soup.find('meta', attrs={'name': 'author'})
                websiteName = websiteNameElement['content'].strip()

                projects = soup.findAll('a', attrs={'data-testid': 'image-card-link'})
                if projects is not None:
                    for project in projects:
                        browser1 = webdriver.Chrome(PATH, options=options)
                        browser1.get(project['href'])
                        time.sleep(5)

                        imageArr = []
                        soup = BeautifulSoup(browser1.page_source, 'lxml')
                        projectNameElement = soup.find('h1', attrs={'class': 'header-1'})
                        if projectNameElement is not None:
                            projectName = projectNameElement.text.strip()
                            projectNamePath = f"{imageSavePath}/{websiteName}/{projectName}"
                            Path(projectNamePath).mkdir(parents=True, exist_ok=True)

                            images = soup.findAll('source')
                            if images is not None:
                                for image in images:
                                    imageUrl = image['srcset'].replace('w378', 'w1024').replace('h378', 'h1024')
                                    try:
                                        image_filename = wget.download(imageUrl, out=projectNamePath)
                                    except Exception as e:
                                        pass
                        browser1.quit()
                browser.quit()
            except Exception as e:
                tb = traceback.format_exc()
                print(tb)
                error = e
                print(error)
                # browser.quit()
                # browser1.quit()
                pass

    def scrapeReviews(self, url):
        returnArr = []

        self.siteUrl = url

        if config.get('scraper_mode') == 'online':
            headersArr = {}

            userAgent = UserAgent()
            userAgentList = userAgent.getRandom()
            headersArr.update(userAgentList)
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
            "id": jsonStr['@id'],
            "name": jsonStr['name'],
            "telephone": jsonStr['telephone'],
            "address": jsonStr['address'],
            "reviews": self.fetchReviews(self.generateReviewUrl(), int(jsonStr['aggregateRating']['reviewCount'])),
            "rating": {
                "aggregate": jsonStr['aggregateRating']['ratingValue'],
                "total": int(jsonStr['aggregateRating']['reviewCount']),
            },
        }

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\">(.*?)</script>"
        matches = re.findall(pattern, self.scrapedRawData, re.MULTILINE | re.DOTALL)

        if len(matches) > 0:
            result = json.loads(matches[0].strip())

        return result[0]

    def generateReviewUrl(self):
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
            result = f'https://www.houzz.com/j/ajax/profileReviewsAjax?userId={userId}&proId={professionalId}&fromItem=ITEM_NUMBER&itemsPerPage=45'

        return result

    def fetchReviews(self, reviewBaseUrl, totalReviews):
        result = []

        self.siteHeaders.update({
            'referer': self.siteUrl,
            'x-requested-with': 'XMLHttpRequest',
        })

        reviewFormatter = ReviewFormatter(self.platformName)
        for i in range(math.ceil(int(totalReviews/45))+1):
            reviewUrl = reviewBaseUrl.replace("ITEM_NUMBER", str(i))
            scrapedRawData = Network.fetch(Network.GET, self.siteHeaders, reviewUrl)
            if(scrapedRawData['code'] == 200):
                reviewsRawData = json.loads(scrapedRawData['body'])
                if 'ctx' in reviewsRawData:
                    if 'data' in reviewsRawData['ctx']:
                        if 'stores' in reviewsRawData['ctx']['data']:
                            if 'data' in reviewsRawData['ctx']['data']['stores']:
                                if 'ProfessionalReviewsStore' in reviewsRawData['ctx']['data']['stores']['data']:
                                    if len(reviewsRawData['ctx']['data']['stores']['data']['ProfessionalReviewsStore']['data']) > 0:
                                        for reviewId in reviewsRawData['ctx']['data']['stores']['data']['ProfessionalReviewsStore']['data']:
                                            review = reviewsRawData['ctx']['data']['stores']['data']['ProfessionalReviewsStore']['data'][reviewId]
                                            reviewerId = review['userId']
                                            userInfoArr = reviewsRawData['ctx']['data']['stores']['data']['UserStore']['data'][str(reviewerId)]
                                            review['user_info'] = userInfoArr
                                            formattedReview = reviewFormatter.format(review)
                                            result.append(formattedReview)

                sleep(randrange(1, 3))

        return result

