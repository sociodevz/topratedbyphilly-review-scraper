import requests
import sys
import re
import os
import time
import traceback
import logging
import json
from urllib.parse import urlparse, urlsplit, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup

from reviews.common.config import config
from reviews.common.functions import fixLocalBusinessJSON
from reviews.main.reviews_formatter import ReviewFormatter

from reviews.common.logger import logger


class Facebook:

    platformName = None
    siteUrl = None
    scrapedRawData = None
    siteHeaders = None
    siteId = None

    location_data = {}

    def __init__(self, debug=False):

        self.platformName = self.__class__.__name__
        print(f'Initalized {self.platformName} Engine')
        logger.info(f'Initalized {self.platformName} Engine')

        self.PATH = f"{config.get('project_physical_root_path')}chromedriver"
        self.options = Options()
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--lang=en-US')
        # self.options.add_argument('--proxy-server=u1.p.webshare.io:10000')
        self.options.headless = config.get('chrome_headless_mode')
        self.browser = webdriver.Chrome(self.PATH, options=self.options)

        self.location_data = {
            "id": None,
            "name": None,
            "telephone": None,
            "address": None,
            "website": None,
            "reviews": [],
            "rating": {
                "aggregate": 0,
                "total": 0,
            },
        }

    def extractJSON(self):
        result = None
        pattern = r"<script type=\"application/ld\+json\".*?>(.*?)</script>"
        matches = re.findall(pattern, self.browser.page_source,  re.UNICODE | re.MULTILINE)

        if len(matches) > 0:
            result = []
            for jsonData in matches:
                result.append(json.loads(jsonData))

        return result

    def extractCompanyPageName(self):
        result = None
        try:
            siteUrlArr = self.location_data['id'].split('/')
            result = siteUrlArr[-2]  # we want 2nd last, because last element = ''
        except Exception as e:
            logger.exception('Exception')
            pass

        return result

    def forceEnglish(self):
        try:
            pageName = self.extractCompanyPageName()
            script = f'require("IntlUtils").setCookieLocale("en_US", "en_US", "https://en-us.facebook.com/{pageName}/reviews/?locale2=en_US", "www_list_selector_more", null); return false;'
            self.browser.execute_script(script)
        except Exception as e:
            logger.exception('Exception')
            pass

    def clickAllReviewsButton(self):
        try:
            element = self.browser.find_element_by_css_selector("[aria-label$='reviews']")
            self.browser.implicitly_wait(5)
            ActionChains(self.browser).move_to_element(element).click(element).perform()
            time.sleep(5)
        except Exception as e:
            logger.exception('Exception')
            pass

    def closeLoginBlockerDialog(self):
        try:
            element = self.browser.find_element_by_css_selector("a[id='expanding_cta_close_button'")
            if element is not None:
                element.click()
        except Exception as e:
            logger.exception('Exception')
            pass

    def expandAllReviews(self):
        try:
            readMoreElements = self.browser.find_elements_by_css_selector("a[class='see_more_link']")
            for readMoreElement in readMoreElements:
                readMoreElement.click()
        except Exception as e:
            logger.exception('Exception')
            pass

    def loadMoreComments(self):
        try:
            loadMoreCommentsElements = self.browser.find_elements_by_css_selector('a[data-ft=\'{"tn":"Q"}\']')
            for loadMoreElement in loadMoreCommentsElements:
                loadMoreElement.click()
        except Exception as e:
            logger.exception('Exception')
            pass

    def getLocationData(self):

        jsonStrs = self.extractJSON()
        jsonStr = jsonStrs[0]
        jsonStr = fixLocalBusinessJSON(jsonStr)

        try:
            self.location_data = {
                "id": jsonStr['@id'],
                "name": jsonStr['name'],
                "telephone": jsonStr['telephone'],
                "address": jsonStr['address'],
                "website": None,
                "reviews": [],
                "rating": {
                    "aggregate": jsonStr['aggregateRating']['ratingValue'],
                    "total": jsonStr['aggregateRating']['ratingCount'],
                },
            }
        except Exception as e:
            logger.exception('Exception')
            pass

    def getReviewElements(self, countOnly):
        reviewElements = None
        try:
            soup = BeautifulSoup(self.browser.page_source, 'lxml')
            reviewElementsOuter = soup.find("div", attrs={"id": "recommendations_tab_main_feed"})
            if reviewElementsOuter is not None:
                reviewElementsInner = reviewElementsOuter.findChildren("div", recursive=False)
                if countOnly is True:
                    # -1 because it has an empty starting div id = own_review_container
                    reviewElements = len(reviewElementsInner) - 1
                else:
                    reviewElements = reviewElementsInner
        except Exception as e:
            logger.exception('Exception')
            pass

        return reviewElements

    def _scrollReviewDiv(self):
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(4)

    def loadAllReviews(self):
        try:
            totalReviewsCount = self.location_data["rating"]['total']

            retryCntr = 0
            lastLoadedReviewCount = 0

            currentlyLoadedReviewsCnt = self.getReviewElements(True)
            lastLoadedReviewCount = currentlyLoadedReviewsCnt
            while currentlyLoadedReviewsCnt < totalReviewsCount:

                if retryCntr < 3:
                    self._scrollReviewDiv()

                    currentlyLoadedReviewsCnt = self.getReviewElements(True)

                    if currentlyLoadedReviewsCnt <= lastLoadedReviewCount:
                        retryCntr += 1
                    else:
                        lastLoadedReviewCount = currentlyLoadedReviewsCnt
                else:
                    break

        except Exception as e:
            logger.exception('Exception')
            pass

    def getReviewsData(self):
        try:
            soup = BeautifulSoup(self.browser.page_source, 'lxml')
            reviewsObj = soup.find_all('div', attrs={"class": "userContentWrapper"})
            if reviewsObj is not None:
                reviewFormatter = ReviewFormatter(self.platformName)
                for cntr, review in enumerate(reviewsObj):
                    finaReview = {}
                    finaReview['review_id'] = 0
                    finaReview['user_id'] = 0
                    finaReview['name'] = None
                    finaReview['level'] = None
                    finaReview['total_reviews'] = 0
                    finaReview['profile_image'] = None
                    finaReview["date"] = None
                    finaReview['review'] = None
                    finaReview['rating'] = 0
                    finaReview['review_response'] = None
                    finaReview['review_response_date'] = None

                    try:
                        if review['id'] == 'own_review_container':
                            continue
                    except Exception as e:
                        #logger.exception('Exception')
                        pass

                    # Name
                    userDetailsObj = review.find(attrs={"data-ft": '{"tn":"m"}'})
                    if userDetailsObj is not None:
                        finaReview['name'] = userDetailsObj['title'].strip()

                        # Profile Pic
                        userProfilePicObj = userDetailsObj.find("img")
                        if userProfilePicObj is not None:
                            finaReview['profile_image'] = userProfilePicObj['src']

                    # Rating
                    userRatingOuterObj = review.find(attrs={"data-ft": '{"tn":"C"}'})
                    if userRatingOuterObj is not None:
                        userRatingInnerObj = userRatingOuterObj.find("span")
                        if userRatingInnerObj is not None:
                            if userRatingInnerObj.text.find("doesn't") != -1:
                                finaReview['rating'] = 0
                            elif userRatingInnerObj.text.find("recommends") != -1:
                                finaReview['rating'] = 1

                    # Published time
                    reviewPublishedTimeOuterObj = review.find("div", attrs={"data-testid": "story-subtitle"})
                    if reviewPublishedTimeOuterObj is not None:
                        reviewPublishedTimeInnerObj = reviewPublishedTimeOuterObj.find("abbr")
                        if reviewPublishedTimeInnerObj is not None:
                            finaReview['date'] = int(reviewPublishedTimeInnerObj['data-utime'])

                    # review TExt
                    reviewTextOuterObj = review.find("div", attrs={"data-testid": "post_message"})
                    if reviewTextOuterObj is not None:
                        reviewTextInnerObj = reviewTextOuterObj.find_all("p")
                        if reviewTextInnerObj is not None:
                            finaReview['review'] = ''
                            for reviewTextObj in reviewTextInnerObj:
                                if reviewTextObj is not None:
                                    finaReview['review'] += reviewTextObj.text.strip()

                    # business Reply Text
                    businessReplyMainObj = review.find("div", attrs={"aria-label": "Comment"})
                    if businessReplyMainObj is not None:
                        businessReplyOuterObj = businessReplyMainObj.find("div", attrs={"data-ft": '{"tn":"K"}'})
                        if businessReplyOuterObj is not None:
                            businessReplyInnerObj = businessReplyOuterObj.find("span")
                            if businessReplyInnerObj is not None:
                                finaReview['review_response'] = businessReplyInnerObj.text.strip()

                        # business Reply Date
                        businessReplyDateObj = businessReplyMainObj.find("abbr", attrs={"class": "livetimestamp"})
                        if businessReplyDateObj is not None:
                            finaReview['review_response_date'] = int(businessReplyDateObj['data-utime'])

                    formattedReview = reviewFormatter.format(finaReview)
                    self.location_data["reviews"].append(formattedReview)
                    self.location_data["reviews_extracted"] = len(self.location_data["reviews"])

        except Exception as e:
            logger.exception('Exception')
            pass

    def __filter_string(self, str):
        strOut = str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        return strOut

    def _cleanupUrl(self, url):
        result = url

        try:
            url_parse = urlparse(url)
            query = url_parse.query
            baseUrl = url.replace(query, '')
            baseUrl = baseUrl.strip('/')
            if len(query) > 0:
                baseUrl = baseUrl.strip('?')

            if baseUrl.find('reviews') == -1:
                baseUrl += '/reviews/'

            baseUrl += '?locale2=en_US'
            result = baseUrl
        except Exception as e:
            logger.exception('Exception')
            pass

        return result

    def scrapeURL(self, url):
        try:
            self.siteUrl = self._cleanupUrl(url)

            if config.get('scraper_mode') == 'online':
                self.browser.get(self.siteUrl)
                time.sleep(5)
            elif config.get('scraper_mode') == 'offline':
                filePath = os.path.realpath(__file__)
                currentFileName = os.path.basename(__file__)
                filePath = filePath.replace(currentFileName, '')
                fileNamePath = f"{filePath}/sample_data/{url}"
                self.browser.get(f"file://{fileNamePath}")

        except Exception as e:
            logger.exception('Exception')
            self.browser.quit()
            return False

        self.getLocationData()
        self.forceEnglish()
        if self.location_data['rating']['total'] > 0:
            self.loadAllReviews()
            self.closeLoginBlockerDialog()
            self.expandAllReviews()
            self.loadMoreComments()
            self.getReviewsData()
        self.browser.quit()

        return(self.location_data)
