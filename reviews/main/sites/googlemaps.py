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

from reviews.common.config import config


class Googlemaps:

    location_data = {}

    def __init__(self, debug=False):
        self.PATH = f"{config.get('project_physical_root_path')}chromedriver"
        self.options = Options()
        #self.options.add_argument("--headless")
        self.driver = webdriver.Chrome(self.PATH, options=self.options)

        self.location_data["rating"] = "NA"
        self.location_data["reviews_count"] = "NA"
        self.location_data["location"] = "NA"
        self.location_data["contact"] = "NA"
        self.location_data["website"] = "NA"
        self.location_data["Time"] = {"Monday": "NA", "Tuesday": "NA", "Wednesday": "NA", "Thursday": "NA", "Friday": "NA", "Saturday": "NA", "Sunday": "NA"}
        self.location_data["Reviews"] = []
        self.location_data["Popular Times"] = {"Monday": [], "Tuesday": [], "Wednesday": [], "Thursday": [], "Friday": [], "Saturday": [], "Sunday": []}

    def clickOpenCloseTime(self):
        if(len(list(self.driver.find_elements_by_class_name("LJKBpe-Tswv1b-hour-text")))!=0):
            element = self.driver.find_element_by_class_name("LJKBpe-Tswv1b-hour-text")
            self.driver.implicitly_wait(5)
            ActionChains(self.driver).move_to_element(element).click(element).perform()

    def clickAllReviewsButton(self):

        try:
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "allxGeDnJMl__button")))

            element = self.driver.find_element_by_class_name("allxGeDnJMl__button")
            element.click()
        except:
            self.driver.quit()
            return False

        return True

    def getLocationData(self):

        try:
            avg_rating = self.driver.find_element_by_class_name("section-star-array").get_attribute("aria-label")
            #total_reviews = self.driver.find_element_by_class_name("section-rating-term")
            #address = self.driver.find_element_by_css_selector("[data-item-id='address']")
            #phone_number = self.driver.find_element_by_css_selector("[data-tooltip='Copy phone number']")
            #website = self.driver.find_element_by_css_selector("[data-item-id='authority']")
        except:
            pass
        try:
            self.location_data["rating"] = str(avg_rating).replace('stars','').strip()
            reviewCount = len(driver.find_elements_by_xpath("//div[@class='section-review ripple-container']"))
            while reviewCount <500: #<=== change this number based on your requirement
                # load the reviews
                self.driver.find_element_by_xpath("//div[contains(@class,'section-loading-spinner')]").location_once_scrolled_into_view
                # wait for loading the reviews
                WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.XPATH,"//div[@class='section-loading-overlay-spinner'][@style='display:none']")))
                # get the reviewsCount
                reviewCount = len(self.driver.find_elements_by_xpath("//div[@class='section-review ripple-container']"))

            self.location_data["reviews_count"] = total_reviews.text[1:-1]
            self.location_data["location"] = address.text
            self.location_data["contact"] = phone_number.text
            self.location_data["website"] = website.text
        except Exception as e:
            print(e)
            pass


    def getLocationOpenCloseTime(self):

        try:
            days = self.driver.find_elements_by_class_name("lo7U087hsMA__row-header")
            times = self.driver.find_elements_by_class_name("lo7U087hsMA__row-interval")

            day = [a.text for a in days]
            open_close_time = [a.text for a in times]

            for i, j in zip(day, open_close_time):
                self.location_data["Time"][i] = j

        except:
            pass

    def getPopularTimes(self):
        try:
            a = self.driver.find_elements_by_class_name("section-popular-times-graph")
            dic = {0:"Sunday", 1:"Monday", 2:"Tuesday", 3:"Wednesday", 4:"Thursday", 5:"Friday", 6:"Saturday"}
            l = {"Sunday":[], "Monday":[], "Tuesday":[], "Wednesday":[], "Thursday":[], "Friday":[], "Saturday":[]}
            count = 0

            for i in a:
                b = i.find_elements_by_class_name("section-popular-times-bar")
                for j in b:
                    x = j.get_attribute("aria-label")
                    l[dic[count]].append(x)
                count = count + 1

            for i, j in l.items():
                self.location_data["Popular Times"][i] = j
        except:
            pass

    def scrollThePage(self):
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "section-layout-root")))

            pause_time = 2
            max_count = 5
            x = 0

            while(x<max_count):
                scrollable_div = self.driver.find_element_by_css_selector('div.section-layout.section-scrollbox.scrollable-y.scrollable-show')
                try:
                    self.driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                except:
                    pass
                time.sleep(pause_time)
                x=x+1
        except:
            self.driver.quit()

    def expandAllReviews(self):
        try:
            element = self.driver.find_elements_by_class_name("section-expand-review")
            for i in element:
                i.click()
        except:
            pass

    def getReviewsData(self):
        try:
            review_names = self.driver.find_elements_by_class_name("section-review-title")
            review_text = self.driver.find_elements_by_class_name("section-review-review-content")
            review_dates = self.driver.find_elements_by_css_selector("[class='section-review-publish-date']")
            review_stars = self.driver.find_elements_by_css_selector("[class='section-review-stars']")

            review_stars_final = []

            for i in review_stars:
                review_stars_final.append(i.get_attribute("aria-label"))

            review_names_list = [a.text for a in review_names]
            review_text_list = [a.text for a in review_text]
            review_dates_list = [a.text for a in review_dates]
            review_stars_list = [a for a in review_stars_final]

            for (a,b,c,d) in zip(review_names_list, review_text_list, review_dates_list, review_stars_list):
                self.location_data["Reviews"].append({"name":a, "review":b, "date":c, "rating":d})

        except Exception as e:
            pass

    def scrapeURL(self, url):
        try:
            self.driver.get(url)
        except Exception as e:
            print(e)
            self.driver.quit()
        time.sleep(2)

        self.clickOpenCloseTime()
        self.getLocationData()
        self.getLocationOpenCloseTime()
        self.getPopularTimes()
        self.clickAllReviewsButton()
        time.sleep(5)
        self.scrollThePage()
        self.expandAllReviews()
        self.getReviewsData()
        self.driver.quit()

        return(self.location_data)
