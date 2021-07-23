import requests
import sys
import re
import os
import time
import traceback
import logging
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


class Googlemaps:

    platformName = None
    siteUrl = None
    scrapedRawData = None
    siteHeaders = None
    siteId = None

    location_data = {}

    def __init__(self, debug=False):
        self.platformName = self.__class__.__name__
        print(f'Initalized {self.platformName} Engine')

        self.PATH = f"{config.get('project_physical_root_path')}chromedriver"
        self.options = Options()
        self.options.add_argument('--no-sandbox')
        self.options.headless = True
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
            pass

    def expandAllReviews(self):
        try:
            reviews = self.browser.find_elements_by_css_selector("[jsaction='pane.review.expandReview']")
            for expandReview in reviews:
                expandReview.click()
        except Exception as e:
            pass

    def getLocationData(self):

        avg_rating = 0
        total_reviews = 0
        address = None
        phone_number = None
        website = None

        try:
            avg_rating = self.browser.find_element_by_class_name("section-star-array").get_attribute("aria-label")
        except Exception as e:
            avg_rating = self.browser.find_element_by_css_selector("ol[aria-label$='stars']").get_attribute("aria-label")
            pass

        try:
            total_reviews = int(self.browser.find_element_by_css_selector("[aria-label$='reviews']").text.replace(' reviews', '').replace(',', ''))
        except Exception as e:
            pass

        try:
            address = self.browser.find_element_by_css_selector("[data-item-id='address']")
        except Exception as e:
            pass

        try:
            phone_number = self.browser.find_element_by_css_selector("[data-tooltip='Copy phone number']")
        except Exception as e:
            pass

        try:
            website = self.browser.find_element_by_css_selector("[data-item-id='authority']")
        except Exception as e:
            pass

        try:
            self.location_data = {
                "id": 0,
                "name": None,
                "telephone": phone_number.text,
                "address": address.text,
                "website": website.text,
                "reviews": [],
                "rating": {
                    "aggregate": float(str(avg_rating).replace('stars', '').strip()),
                    "total": total_reviews,
                },
            }
        except Exception as e:
            print(e)
            pass

    def getReviewElements(self):
        reviewElements = 0
        try:
            reviewElements = self.browser.find_elements_by_css_selector("div[jsaction='mouseover:pane.review.in;mouseout:pane.review.out']")
        except Exception as e:
            print(e)
            pass

        return reviewElements

    def _scrollReviewDiv(self):
        scrollable_div = self.browser.find_element_by_css_selector('div.section-layout.section-scrollbox')
        self.browser.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
        time.sleep(4)

    def loadAllReviews(self):
        try:
            self.clickAllReviewsButton()
            totalReviewsCount = self.location_data["rating"]['total']

            retryCntr = 0
            lastLoadedReviewCount = 0

            currentlyLoadedReviews = self.getReviewElements()
            lastLoadedReviewCount = currentlyLoadedReviewsCnt = len(list(currentlyLoadedReviews))
            while len(list(currentlyLoadedReviews)) < totalReviewsCount:

                if retryCntr < 3:
                    lastLoadedReviewElement = currentlyLoadedReviews[-1]
                    #self.browser.execute_script('arguments[0].scrollIntoView(true)', lastLoadedReviewElement)
                    #time.sleep(2)
                    self._scrollReviewDiv()

                    currentlyLoadedReviews = self.getReviewElements()
                    currentlyLoadedReviewsCnt = len(list(currentlyLoadedReviews))

                    if currentlyLoadedReviewsCnt <= lastLoadedReviewCount:
                        retryCntr += 1
                    else:
                        lastLoadedReviewCount = currentlyLoadedReviewsCnt
                else:
                    break

        except Exception as e:
            print(e)
            pass

    def getLocationOpenCloseTime(self):

        try:
            openCloseTimesString = self.browser.find_element_by_css_selector("div[aria-label$='Hide open hours for the week']").get_attribute("aria-label")
            #1st explode by ; for days split
            #2nd explode by , for day and time split

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
            pass

    def getPopularTimes(self):
        try:
            a = self.browser.find_elements_by_class_name("section-popular-times-graph")
            dic = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
            l = {"Sunday": [], "Monday": [], "Tuesday": [], "Wednesday": [], "Thursday": [], "Friday": [], "Saturday": []}
            count = 0

            for i in a:
                b = i.find_elements_by_class_name("section-popular-times-bar")
                for j in b:
                    x = j.get_attribute("aria-label")
                    l[dic[count]].append(x)
                count = count + 1

            for i, j in l.items():
                self.location_data["popular_times"][i] = j
        except Exception as e:
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

                    #review Id
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
                    reviewerImageUrl = review.find("img")
                    if reviewerImageUrl is not None:
                        finaReview['profile_image'] = reviewerImageUrl['src']

                    # reviewer level & total reviews
                    reviewerDetailsOuterObj = review.find("a", attrs={"href": re.compile('^https://www.google.com/maps/contrib/')})
                    if reviewerDetailsOuterObj is not None:
                        reviewerDetailsInnerObj = review.find("div", attrs={"class": re.compile('.*VdSJob')})
                        spansObj = reviewerDetailsInnerObj.findChildren("span", recursive=False)
                        spansArr = ["level", "total_reviews"]
                        for cntr, spanObj in enumerate(spansObj):
                            if cntr == 0:
                                finaReview['level'] = spanObj.text.strip().replace(' reviews', '').replace(' review', '').replace('\u30fb19', '')
                            elif cntr == 1:
                                totalReviewsText = spanObj.text.replace('\u30fb19', '')
                                totalReviewsText = spanObj.text.replace('・', '')
                                totalReviewsText = totalReviewsText.replace(' reviews', '')
                                totalReviewsText = totalReviewsText.replace(' review', '')
                                totalReviewsText = int(totalReviewsText.strip())
                                finaReview['total_reviews'] = totalReviewsText

                    # reviewer rating
                    reviewerRatingObj = review.find("span", attrs={"aria-label": re.compile('.*stars.*')})
                    if reviewerRatingObj is not None:
                        finaReview['rating'] = float(reviewerRatingObj['aria-label'].replace(' stars', ' ').replace(' star', ' ').strip())

                        # reviewer Date
                        reviewerRatingParentObj = reviewerRatingObj.find_parent("div")
                        if reviewerRatingParentObj is not None:
                            spansObj = reviewerRatingParentObj.findChildren("span", attrs={"class": re.compile('.*-date')}, recursive=False)
                            if spansObj is not None:
                                for cntr, spanObj in enumerate(spansObj):
                                    finaReview['date'] = spanObj.text.strip()

                    # reviewer review text
                    reviewTextOuterObj = review.find("div", attrs={"jsinstance": '*0'})
                    if reviewTextOuterObj is not None:
                        spansObj = reviewTextOuterObj.findChildren("span", attrs={"class": re.compile('.*-text')}, recursive=False)
                        for cntr, spanObj in enumerate(spansObj):
                            finaReview['review'] = spanObj.text.strip()

                    #business reply if any
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
            error = e
            pass

    def getReviewsDataOld(self):
        try:
            reviews = self.getReviewElements()
            if(len(list(reviews)) != 0):
                previousReviewText = None

                reviewFormatter = ReviewFormatter(self.platformName)
                for review in reviews:
                    reviewText = review.text
                    if reviewText not in ['Like', 'Share', 'More', ''] and len(reviewText) > 5:
                        if reviewText != previousReviewText:
                            previousReviewText = reviewText
                            reviewDetailsArr = reviewText.splitlines()

                            if len(reviewDetailsArr) > 0:
                                reviewerLevelReviewsSplitArr = reviewDetailsArr[1].split('・')
                                reviewerLevel = None
                                reviewerTotalReviews = 0
                                if len(reviewerLevelReviewsSplitArr) > 1:
                                    reviewerLevel = reviewerLevelReviewsSplitArr[0]
                                    reviewerTotalReviewsStr = reviewerLevelReviewsSplitArr[1]
                                else:
                                    reviewerTotalReviewsStr = reviewerLevelReviewsSplitArr[0]

                                reviewerTotalReviews = int(reviewerTotalReviewsStr.split(' ')[0])

                                finaReview = {}
                                finaReview['review_id'] = 0
                                finaReview['user_id'] = 0
                                finaReview['name'] = reviewDetailsArr[0]
                                finaReview['level'] = reviewerLevel
                                finaReview['total_reviews'] = reviewerTotalReviews
                                finaReview["date"] = None
                                finaReview['review'] = None
                                finaReview['reviewResponse'] = None

                                if len(reviewDetailsArr) == 3:
                                    dateDetectionArr = reviewDetailsArr[2].split(' ')
                                    if dateDetectionArr[2] == 'ago':
                                        finaReview['date'] = reviewDetailsArr[2]
                                else:
                                    finaReview['review'] = reviewDetailsArr[3]

                                html_content = review.get_attribute('innerHTML')
                                self.browserReviews.get("data:text/html;charset=utf-8,{html_content}".format(html_content=html_content))

                                try:
                                    reviewerUrl = self.browserReviews.find_element_by_css_selector("a[aria-label^=' Photo of']").get_attribute("href").strip()
                                    reviewerUrl = reviewerUrl.replace('https://www.google.com/maps/contrib/', '')
                                    finaReview['user_id'] = int(reviewerUrl.split('/')[0])
                                except Exception as e:
                                    pass

                                try:
                                    reviewId = self.browserReviews.find_element_by_css_selector("button[aria-label^=' Review actions']").get_attribute("data-review-id").strip()
                                    finaReview['review_id'] = reviewId
                                except Exception as e:
                                    pass

                                reviewRating = 0
                                try:
                                    reviewRatingStr = self.browserReviews.find_element_by_css_selector("span[aria-label$='stars ']").get_attribute("aria-label").strip()
                                    reviewRatingArr = reviewRatingStr.split(' ')
                                    reviewRating = int(reviewRatingArr[0].strip())

                                except Exception as e:
                                    reviewRatingStr = self.browserReviews.find_element_by_css_selector("span[aria-label$='star ']").get_attribute("aria-label").strip()
                                    reviewRatingArr = reviewRatingStr.split(' ')
                                    reviewRating = int(reviewRatingArr[0].strip())
                                    pass

                                try:
                                    reviewDate = self.browserReviews.find_element_by_css_selector("span[class$='-date']").text.strip()
                                    finaReview['date'] = reviewDate
                                except Exception as e:
                                    pass

                                finaReview['rating'] = reviewRating

                                formattedReview = reviewFormatter.format(finaReview)
                                self.location_data["reviews"].append(formattedReview)
                                self.location_data["reviews_extracted"] = len(self.location_data["reviews"])
                self.browser.quit()
        except Exception as e:
            print(e)
            pass

    def __filter_string(self, str):
        strOut = str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        return strOut

    def scrapeURL(self, url):
        try:
            self.browser.get(url)
            time.sleep(5)
        except Exception as e:
            print(e)
            self.browser.quit()

        self.clickOpenCloseTime()
        self.getLocationOpenCloseTime()
        time.sleep(2)
        self.getLocationData()
        self.getPopularTimes()
        self.loadAllReviews()
        self.expandAllReviews()
        self.getReviewsData()
        self.browser.quit()

        return(self.location_data)
