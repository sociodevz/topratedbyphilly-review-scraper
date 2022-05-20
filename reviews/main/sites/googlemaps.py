import math
import requests
import sys
import re
import os
import time
import traceback
import logging
import datetime

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
from reviews.main.reviews_formatter import ReviewFormatter
from reviews.common.logger import logger
from reviews.common.functions import *
from reviews.main.scraper_interface import IScraper


class Googlemaps(IScraper):

    platformName = None
    siteUrl = None
    scrapedRawData = None
    siteHeaders = None
    siteId = None

    location_data = {}

    def __init__(self, debug=False):
        self.platformName = self.__class__.__name__
        logger.info(f'Initalized {self.platformName} Engine')

        self.PATH = f"{config.get('project_physical_root_path')}chromedriver"
        self.options = Options()
        self.options.add_argument('--no-sandbox')
        if config.get('proxy_enabled') is True:
            self.options.add_argument('--proxy-server=%s' % config.get('proxy_url_ip'))
        self.options.headless = config.get('chrome_headless_mode')
        self.browser = webdriver.Chrome(self.PATH, options=self.options)
        #self.browserReviews = webdriver.Chrome(self.PATH, options=self.options)

        self.location_data = {
            "id": None,
            "name": None,
            "telephone": None,
            "address": None,
            "website": None,
            "time": {"monday": None, "tuesday": None, "wednesday": None, "thursday": None, "friday": None, "saturday": None, "sunday": None},
            "popular_times": {"monday": [], "tuesday": [], "Wednesday": [], "thursday": [], "friday": [], "saturday": [], "sunday": []},
            "reviews": [],
            "rating": {
                "aggregate": None,
                "total": None,
            },
        }

    def __del__(self):
        logger.info(f'Terminating {self.platformName} Engine\nScraping: {self.siteUrl}')

    def clickOpenCloseTime(self):
        if(len(list(self.browser.find_elements_by_class_name("LJKBpe-Tswv1b-hour-text"))) != 0):
            element = self.browser.find_element_by_class_name("LJKBpe-Tswv1b-hour-text")
            self.browser.implicitly_wait(5)
            ActionChains(self.browser).move_to_element(element).click(element).perform()

    def clickAllReviewsButton(self):
        try:
            element = self.browser.find_element_by_css_selector("[aria-label$='reviews']")
            self.browser.implicitly_wait(5)
            ActionChains(self.browser).move_to_element(element).click(element).perform()
            time.sleep(5)
        except Exception as e:
            logger.exception('Exception')
            pass

    def expandAllReviews(self):
        try:
            reviews = self.browser.find_elements_by_css_selector("[jsaction='pane.review.expandReview']")
            for expandReview in reviews:
                expandReview.click()
        except Exception as e:
            logger.exception('Exception')
            pass

    def getLocationData(self):

        avg_rating = 0
        total_reviews = 0
        name = None
        address = None
        phone_number = None
        website = None

        try:
            soup = BeautifulSoup(self.browser.page_source, 'lxml')
            if soup is not None:
                nameObjectOutter = soup.find('h1', attrs={'class': re.compile('fontHeadlineLarge')})
                if nameObjectOutter is not None:
                    nameSpanObject = nameObjectOutter.findChild('span')
                    if nameSpanObject is not None:
                        name = nameSpanObject.text.strip()
        except Exception as e:
            logger.exception('Exception')
            pass

        try:
            avg_rating = self.browser.find_element_by_class_name("section-star-array").get_attribute("aria-label")
        except Exception as e:
            logger.exception('Exception')
            try:
                avg_rating = self.browser.find_element_by_css_selector("span[jsan='0.aria-hidden']").text
            except Exception as e:
                logger.exception('Exception')
                pass

        try:
            total_reviews = int(self.browser.find_element_by_css_selector("[aria-label$='reviews']").text.replace(' reviews', '').replace(',', ''))
        except Exception as e:
            logger.exception('Exception')
            pass

        try:
            address = self.browser.find_element_by_css_selector("[data-item-id='address']")
            address = address.text
        except Exception as e:
            logger.exception('Exception')
            pass

        try:
            phone_number = self.browser.find_element_by_css_selector("[data-tooltip='Copy phone number']")
            phone_number = phone_number.text
        except Exception as e:
            logger.exception('Exception')
            pass

        try:
            website = self.browser.find_element_by_css_selector("[data-item-id='authority']")
            website = website.text
        except Exception as e:
            logger.exception('Exception')
            pass

        try:
            self.location_data = {
                "id": 0,
                "name": name,
                "telephone": phone_number,
                "address": address,
                "website": website,
                "reviews": [],
                "rating": {
                    "aggregate": float(re.findall(r'\d+(?:\.\d+)?', str(avg_rating).replace('stars', '').strip())[0]),
                    "total": total_reviews,
                },
            }
        except Exception as e:
            logger.exception('Exception')
            pass

    def getReviewElements(self):
        reviewElements = 0
        try:
            reviewElements = self.browser.find_elements_by_css_selector("div[jsaction='mouseover:pane.review.in;mouseout:pane.review.out']")
        except Exception as e:
            logger.exception('Exception')
            pass

        return reviewElements

    def _scrollReviewDiv(self):
        try:
            all_reviews = self.browser.find_elements_by_css_selector("div[data-review-id]")
            # we are dividing below length /2 because above selector returns 2 divs for each review
            while (len(all_reviews)/2) < self.location_data["rating"]['total']:
                self.browser.execute_script('arguments[0].scrollIntoView(true);', all_reviews[-1])
                WebDriverWait(self.browser, 5, 0.25).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class$="activityIndicator"]')))
                all_reviews = self.browser.find_elements_by_css_selector("div[data-review-id]")
        except Exception as e:
            logger.exception('Exception')

    def loadAllReviews(self):
        try:
            self.clickAllReviewsButton()
            totalReviewsCount = self.location_data["rating"]['total']
            self._scrollReviewDiv()
        except Exception as e:
            logger.exception('Exception')
            pass

    def getLocationOpenCloseTime(self):

        try:
            openCloseTimesString = self.browser.find_element_by_css_selector("div[aria-label$='Hide open hours for the week']").get_attribute("aria-label")
            # 1st explode by ; for days split
            # 2nd explode by , for day and time split

            if openCloseTimesString != '':
                daysSplitArr = openCloseTimesString.split(';')
                for dayTimeCombined in daysSplitArr:
                    dayTimeArr = dayTimeCombined.split(',')
                    dayNameArr = dayTimeArr[0].strip().split(' ')
                    dayName = dayNameArr[0].lower().strip()
                    dayHoursArr = dayTimeArr[1].strip().split('.')
                    dayHour = dayHoursArr[0].strip()
                    self.location_data["time"][dayName] = dayHour

        except Exception as e:
            logger.exception('Exception')
            pass

    def getPopularTimes(self):
        try:
            a = self.browser.find_elements_by_class_name("section-popular-times-graph")
            dic = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
            days = {"Sunday": [], "Monday": [], "Tuesday": [], "Wednesday": [], "Thursday": [], "Friday": [], "Saturday": []}
            count = 0

            for i in a:
                b = i.find_elements_by_class_name("section-popular-times-bar")
                for j in b:
                    x = j.get_attribute("aria-label")
                    l[dic[count]].append(x)
                count = count + 1

            for i, j in days.items():
                self.location_data["popular_times"][i] = j
        except Exception as e:
            logger.exception('Exception')
            pass

    def getReviewsData(self):
        try:
            soup = BeautifulSoup(self.browser.page_source, 'lxml')
            reviewsObj = soup.find_all('div', attrs={"jsaction": "mouseover:pane.review.in;mouseout:pane.review.out"})
            if reviewsObj is not None:
                reviewFormatter = ReviewFormatter(self.platformName)
                for review in reviewsObj:
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

                    # review Id
                    finaReview['review_id'] = review['data-review-id']

                    # reviewer Name
                    reviewerDetailsObj = review.find("a", attrs={"aria-label": re.compile('^ Photo of ')})
                    reviewerName = reviewerDetailsObj['aria-label'].replace('Photo of ', '').strip()
                    finaReview['name'] = reviewerName

                    # reviewer Id
                    reviewerProfileUrl = reviewerDetailsObj['href'].strip()
                    reviewerId = reviewerProfileUrl.split('/')[-2]
                    finaReview['user_id'] = int(reviewerId)

                    # reviewer profilePic
                    reviewerImageUrl = reviewerDetailsObj.find("img")
                    if reviewerImageUrl is not None:
                        finaReview['profile_image'] = reviewerImageUrl['src']

                    # reviewer level & total reviews
                    reviewerDetailsOuterObj = review.find("a", attrs={"href": re.compile('^https://www.google.com/maps/contrib/'), "aria-label": None})
                    if reviewerDetailsOuterObj is not None:
                        divsObj = reviewerDetailsOuterObj.findChildren("div")
                        if len(divsObj) > 0:
                            for cntr, div in enumerate(divsObj[-1]):
                                for child in div:
                                    if cntr == 0:
                                        finaReview['level'] = child.strip().replace(' reviews', '').replace(' review', '').replace('\u30fb19', '')
                                    elif cntr == 1:
                                        totalReviewsText = child.replace('\u30fb19', '')
                                        totalReviewsText = child.replace('・', '')
                                        totalReviewsText = totalReviewsText.replace(' reviews', '')
                                        totalReviewsText = totalReviewsText.replace(' review', '')
                                        totalReviewsText = totalReviewsText.replace('・', '')
                                        totalReviewsText = totalReviewsText.replace('·', '')

                                        totalReviewsText = int(totalReviewsText.strip())
                                        finaReview['total_reviews'] = totalReviewsText

                    # reviewer rating
                    reviewerRatingObj = review.find("span", attrs={"aria-label": re.compile('.*star.*')})
                    if reviewerRatingObj is not None:
                        finaReview['rating'] = float(reviewerRatingObj['aria-label'].replace(' stars', ' ').replace(' star', ' ').strip())

                        # reviewer Date
                        reviewerRatingParentObj = reviewerRatingObj.find_parent("div")
                        if reviewerRatingParentObj is not None:
                            spansObj = reviewerRatingParentObj.findChildren("span", attrs={"class": re.compile('rsqaWe')}, recursive=False)
                            if spansObj is not None:
                                for cntr, spanObj in enumerate(spansObj):
                                    finaReview['date'] = spanObj.text.strip()

                    # reviewer review text
                    reviewTextOuterObj = review.find("div", attrs={"jsinstance": '*0'})
                    if reviewTextOuterObj is not None:
                        spansObj = reviewTextOuterObj.findChildren("span")
                        for cntr, spanObj in enumerate(spansObj[-1]):
                            finaReview['review'] = spanObj.strip()

                    # business reply if any
                    businessReplyOuterObj = review.find("div", attrs={"class": re.compile('.*-header')})
                    if businessReplyOuterObj is not None:
                        spansObj = businessReplyOuterObj.findChildren("span", recursive=False)
                        for cntr, spanObj in enumerate(spansObj):
                            if cntr == 1:
                                finaReview['review_response_date'] = spanObj.text.strip()

                        # business reply date if any
                        businessReplyParentDiv = businessReplyOuterObj.find_parent("div")
                        if businessReplyParentDiv is not None:
                            businessReplyTextObj = businessReplyParentDiv.find("div", attrs={"class", re.compile('.*-text')})
                            if businessReplyTextObj is not None:
                                finaReview['review_response'] = businessReplyTextObj.text.strip()

                    formattedReview = reviewFormatter.format(finaReview)
                    self.location_data["reviews"].append(formattedReview)
                    self.location_data["reviews_extracted"] = len(self.location_data["reviews"])

        except Exception as e:
            logger.exception('Exception')
            pass

    def __filter_string(self, str):
        strOut = str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        return strOut

    def scrapeGoogleLocalDirectory(headersArr, refererUrl, url, category):
        path = f"{config.get('project_physical_root_path')}chromedriver"
        options = Options()
        options.add_argument('--no-sandbox')
        options.headless = config.get('chrome_headless_mode')
        browser = webdriver.Chrome(path, options=options)
        try:
            browser.get(url)
            time.sleep(5)
            bodyHtml = str(browser.page_source).encode('utf8').decode('unicode_escape')
            bodyHtml = bodyHtml.replace("\\u0026","&").replace("\\u003d","=").replace("\\n",'\n')
            browser.quit()
            # with open('tmp/googledirectory.html') as file:
            #         resultArr = {
            #             'code': 200,
            #             'body': file.read()
            #         }
            # bodyHtml = resultArr['body']

            soup = BeautifulSoup(bodyHtml, 'lxml')
            if soup is not None:
                # save memory quit browser
                companyNameArr = []
                companyUrlArr = []
                companyRatingArr = []
                companyDetailsArr = []

                regex = r'\["(https://www.google.com/localservices/provider\?cid=.*?)",null,null,"(.*?)\\nPlumber\\nStar rating: (.*?)"'
                matches = re.findall(regex, bodyHtml)
                if len(matches) > 0:
                    for match in matches:
                        companyNameArr.append(match[1])
                        companyUrlArr.append(match[0])
                        companyRatingArr.append(match[2])

                reviewCountOuterList = soup.findAll('div', attrs={'class': 'zFYXkc'})
                if reviewCountOuterList is not None:
                    for reviewCountOuterObj in reviewCountOuterList:
                        reviewCountList = reviewCountOuterObj.findAll('span', attrs={'class': 'rBK1zb'})
                        if reviewCountList is not None:
                            for reviewCountObj in reviewCountList:
                                reviewCountSpanList = reviewCountObj.findAll('span')
                                for reviewCountSpanObj in reviewCountSpanList:
                                    value = reviewCountSpanObj.text.strip()
                                    try:
                                        int(value)
                                        companyDetailsArr.append(float(value))
                                        continue
                                    except ValueError:
                                        pass

                fields = ['name', 'url', 'rating', 'total_ratings']
                rows = []

                for (name, landingUrl, rating, totalRatings) in zip(companyNameArr, companyUrlArr, companyRatingArr, companyDetailsArr):
                    rows.append([name, landingUrl, rating, totalRatings])

                ts = datetime.datetime.now().timestamp()
                writeCSV(f"tmp/googlelocal_{category}.csv", fields, rows)

        except Exception as e:
            print(e)
            browser.quit()

    def scrapeGoogleDirectory(headersArr, refererUrl, url, category, skipToPageNum=None):
        newDataAvailable = True
        path = f"{config.get('project_physical_root_path')}chromedriver"
        options = Options()
        options.add_argument('--no-sandbox')
        options.headless = config.get('chrome_headless_mode')
        browser = webdriver.Chrome(path, options=options)

        browser.get(url)
        time.sleep(10)
        if skipToPageNum is not None:
            if skipToPageNum > 10:
                loopsNeeded = math.floor(skipToPageNum / 10)
                for i in range(1, loopsNeeded+1):
                    nextPageUrlElement = browser.find_element_by_css_selector("[aria-label='Page " + str(i * 10) + "']")
                    if nextPageUrlElement is not None:
                        ActionChains(browser).move_to_element(nextPageUrlElement).click(nextPageUrlElement).perform()
                        time.sleep(5)

            nextPageUrlElement = browser.find_element_by_css_selector("[aria-label='Page " + str(skipToPageNum) + "']")
            if nextPageUrlElement is not None:
                ActionChains(browser).move_to_element(nextPageUrlElement).click(nextPageUrlElement).perform()
                time.sleep(5)

        def startScraping(skipToPage=None):
            global newDataAvailable
            try:
                newDataAvailable = False
                bodyHtml = str(browser.page_source).encode('utf8').decode('unicode_escape')
                bodyHtml = bodyHtml.replace("\\u0026", "&").replace("\\u003d", "=").replace("\\n", '\n')

                soup = BeautifulSoup(bodyHtml, 'lxml')
                if soup is not None:
                    # save memory quit browser
                    companyNameArr = []
                    companyUrlArr = []
                    companyRatingArr = []
                    companyDetailsArr = []

                    #need to find all company links
                    companyLinkElementList = browser.find_elements_by_class_name("rllt__link")
                    if companyLinkElementList is not None:
                        for companyLinkElement in companyLinkElementList:
                            ActionChains(browser).move_to_element(companyLinkElement).click(companyLinkElement).perform()
                            time.sleep(5)

                            bodyHtml = str(browser.page_source).encode('utf8').decode('unicode_escape')
                            bodyHtml = bodyHtml.replace("\\u0026", "&").replace("\\u003d", "=").replace("\\n", '\n')
                            soup = BeautifulSoup(bodyHtml, 'lxml', parse_only=SoupStrainer('div', attrs={'class': 'kp-header'}))
                            if soup is not None:
                                companyNameElement = soup.find('h2', attrs={'data-attrid': 'title'})
                                if companyNameElement is not None:
                                    companyNameSpan = companyNameElement.find('span')
                                    if companyNameSpan is not None:
                                        companyNameArr.append(companyNameSpan.text.strip())
                                    else:
                                        companyNameArr.append(companyNameElement.text.strip())

                                companyWebsite = 'NA'
                                companyUrlElement = soup.find('a', attrs={'class': 'ab_button'})
                                if companyUrlElement is not None:
                                    companyWebsite = companyUrlElement['href'].strip()
                                companyUrlArr.append(companyWebsite)

                                companyRatedText = 0
                                companyTotalReviewsText = 0
                                companyDetailsElement = soup.find('div', attrs={'data-attrid': 'kc:/local:lu attribute list'})
                                if companyDetailsElement is not None:
                                    companyRatingSpan = companyDetailsElement.find('span', attrs={'aria-hidden': 'true'})
                                    if companyRatingSpan is not None:
                                        companyRatedText = float(companyRatingSpan.text.strip())

                                    companyReviewCountWrapper = companyDetailsElement.find('a')
                                    if companyReviewCountWrapper is not None:
                                        companyReviewCountSpan = companyReviewCountWrapper.find('span')
                                        if companyReviewCountSpan is not None:
                                            companyTotalReviewsText = int(companyReviewCountSpan.text.replace('reviews', '').replace('review', '').replace('Google', '').replace(',', '').strip())

                                companyRatingArr.append(companyRatedText)
                                companyDetailsArr.append(companyTotalReviewsText)

                    fields = ['name', 'url', 'rating', 'total_ratings']
                    rows = []

                    for (name, landingUrl, rating, totalRatings) in zip(companyNameArr, companyUrlArr, companyRatingArr, companyDetailsArr):
                        rows.append([name, landingUrl, rating, totalRatings])

                    ts = datetime.datetime.now().timestamp()
                    writeCSV(f"tmp/googlesearch_{category}.csv", fields, rows)

                # find pagination
                nextPageUrlElement = browser.find_element_by_id('pnnext')
                if nextPageUrlElement is not None:
                    ActionChains(browser).move_to_element(nextPageUrlElement).click(nextPageUrlElement).perform()
                    time.sleep(5)
                    newDataAvailable = True
            except Exception as e:
                print(e)
                #browser.quit()

        while newDataAvailable is True:
            startScraping()

    def scrapeReviews(self, url):
        try:
            self.siteUrl = url

            logger.info(f'Scraping: {self.siteUrl}')
            self.browser.get(self.siteUrl)
            #self.browser.get('file:///var/www/html/topratedbyphilly/scraper/tmp/' + self.siteUrl)
            time.sleep(10)
        except Exception as e:
            logger.exception('Exception')
            self.browser.quit()

        self.clickOpenCloseTime()
        self.getLocationOpenCloseTime()
        time.sleep(2)
        self.getLocationData()
        self.getPopularTimes()
        if self.location_data['rating']['total'] > 0:
            self.loadAllReviews()
            self.expandAllReviews()
            self.getReviewsData()
        self.browser.quit()

        return(self.location_data)

    def scrapeListings(self, url):
        pass

    def scrapeImages(self, url, imageSavePath):
        pass
