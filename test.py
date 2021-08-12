import os
import pathlib
import traceback
from bs4.element import SoupStrainer
from reviews.common.useragents import UserAgent
from typing import Iterable
import requests
import re
import itertools
import csv
import json
import html
import time
import datetime
import math
import wget
from pathlib import Path
from hashlib import sha256
from http.cookiejar import MozillaCookieJar
from reviews.common.config import config
from reviews.common.network import Network
from bs4 import BeautifulSoup
from csv import writer
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

def scrapeYelpProjectImages():
    PATH = f"{config.get('project_physical_root_path')}chromedriver"
    options = Options()
    options.add_argument('--no-sandbox')
    options.headless = config.get('chrome_headless_mode')
    browser = webdriver.Chrome(PATH, options=options)

    urlsList = [
        'https://www.yelp.com/biz_photos/green-pest-solutions-philadelphia',
        'https://www.yelp.com/biz_photos/aptive-environmental-bensalem',
        'https://www.yelp.com/biz_photos/orkin-bensalem-3',
        'https://www.yelp.com/biz_photos/dynamite-pest-control-philadelphia',
        'https://www.yelp.com/biz_photos/city-and-suburbs-pest-control-company-philadelphia-6',
        'https://www.yelp.com/biz_photos/prodigy-pest-solutions-ridley-park-2',
        'https://www.yelp.com/biz_photos/harpoon-pest-solutions-philadelphia',
        'https://www.yelp.com/biz_photos/evans-pest-control-philadelphia-3',
        'https://www.yelp.com/biz_photos/township-pest-control-warrington',
        'https://www.yelp.com/biz_photos/live-by-the-brush-morrisville',
        'https://www.yelp.com/biz_photos/angelos-cleaning-phoenixville-3',
        'https://www.yelp.com/biz_photos/kc-carpet-and-upholstery-cleaners-philadelphia-2',
        'https://www.yelp.com/biz_photos/thomas-carpet-cleaners-newtown-square',
        'https://www.yelp.com/biz_photos/neo-carpet-cleaning-philadelphia',
        'https://www.yelp.com/biz_photos/zakian-rug-cleaning-philadelphia',
        'https://www.yelp.com/biz_photos/a1-sparkles-cleaning-bridgeport-2',
        'https://www.yelp.com/biz_photos/barnes-and-young-carpet-cleaning-philadelphia',
        'https://www.yelp.com/biz_photos/eds-cleaning-service-philadelphia-2',
    ]

    for url in urlsList:

        try:
            if url.find('biz_photos') == -1:
                url = url.replace('https://www.yelp.com/biz/', 'https://www.yelp.com/biz_photos/')

            nextPageExists = True
            browser.get(url)
            time.sleep(5)
            cntr = 1
            while nextPageExists is True:
                nextPageExists = False
                # val = input("Continue:")

                websiteName = None
                soup = BeautifulSoup(browser.page_source, 'lxml')
                titleElement = soup.find('title')
                websiteName = titleElement.text.replace('Photos for ', '').replace(' - Yelp', '').strip()

                projectName = 'All'
                projectNamePath = f"tmp/images/yelp/{websiteName}/{projectName}"
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
                        nextPageExists = True
                except Exception as e:
                    pass
        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            error = e
            print(error)
            #browser.quit()
            pass


scrapeYelpProjectImages()


def scrapeHouzzProjectImages():
    PATH = f"{config.get('project_physical_root_path')}chromedriver"
    options = Options()
    options.add_argument('--no-sandbox')
    options.headless = config.get('chrome_headless_mode')

    urlsList = [
        'https://www.houzz.com/pro/service5750/martella-electric',
        'https://www.houzz.com/pro/gen3electric/generation-3-electric-inc',
        'https://www.houzz.com/pro/debbie8614/jdv-electric',
        'https://www.houzz.com/pro/webuser-865513104/thomas-edison-electric',
        'https://www.houzz.com/pro/kbelectricpa/kb-electric-llc',
        'https://www.houzz.com/pro/allstarelectrical10/all-star-electrical-services-llc',
        'https://www.houzz.com/pro/kowallelectric/kowall-electric',
        'https://www.houzz.com/pro/giannonehvac/joseph-giannone-plumbing-heating-air-conditioning',
        'https://www.houzz.com/pro/info596258/boyle-energy',
        'https://www.houzz.com/pro/jhowy73/air-done-right',
        'https://www.houzz.com/pro/livebythebrush/live-by-the-brush-llc-professional-carpet-cleaners',
        'https://www.houzz.com/pro/webuser-208720602/kc-carpet-cleaning-upholstery-cleaning'
    ]

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
                        projectNamePath = f"tmp/images/{websiteName}/{projectName}"
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
            browser.quit()
            browser1.quit()
            pass




exit()
def writeCSV(fileNamePath, fields, rows):
    try:
        append = False
        file = Path(fileNamePath)
        if file.is_file():
            append = True

        with open(fileNamePath, 'a') as f:
            write = csv.writer(f)
            if append is False:
                write.writerow(fields)
            write.writerows(rows)
    except Exception as e:
        error = e
        pass

def scrapeTopRatedDirectory(url, category):

    resultArr = Network.fetch(Network.GET, url)
    # with open('tmp/topratedlocal.html') as file:
    #     resultArr = {
    #         'code': 200,
    #         'body': file.read()
    #     }

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



def scrapeYelpDirectory(url, category):

    resultArr = Network.fetch(Network.GET, url)
    # with open('tmp/yelpdirectory.html') as file:
    #     resultArr = {
    #         'code': 200,
    #         'body': file.read()
    #     }

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
                    writeCSV(f"tmp/yelp_{category}.csv", fields, rows)

                    #lets try and extract next page url
                    nextPageUrlElement = soup.find('a', attrs={'class': 'next-link'})
                    if nextPageUrlElement is not None:
                        url = nextPageUrlElement['href']
                        time.sleep(2)
                        scrapeYelpDirectory(url, category)

                except Exception as e:
                    error = e
                    pass

def scrapeBuildzoomDirectory(headersArr, refererUrl, url, category):
    headersArr['referer'] = refererUrl
    headersArr['authority'] = 'www.buildzoom.com'
    headersArr['path'] = url.replace('https://www.buildzoom.com', '')
    resultArr = Network.fetch(Network.GET, url, headersArr)
    # with open('tmp/yelpdirectory.html') as file:
    #     resultArr = {
    #         'code': 200,
    #         'body': file.read()
    #     }

    if resultArr['code'] == 200:
        bodyHtml = resultArr['body']

        if bodyHtml != '':
            companyNameArr = []
            companyUrlArr = []
            companyRatingArr = []
            companyDetailsArr = []

            try:
                soup = BeautifulSoup(bodyHtml, 'lxml')
                mainWrapperDiv = soup.find('div', attrs={'class': 'search-result-contractors'})
                if mainWrapperDiv is not None:
                    companyMainDivList = mainWrapperDiv.find_all('div', attrs={'class': 'search-result-contractor-secondary'})
                    if companyMainDivList is not None:
                        for companyMainDiv in companyMainDivList:
                            companyNameList = companyMainDiv.find_all('div', attrs={'itemprop': 'name'})
                            if companyNameList is not None:
                                for companyName in companyNameList:
                                    companyNameArr.append(companyName.text.strip())

                            companyUrlList = companyMainDiv.find_all('a', attrs={'itemprop': 'url'})
                            if companyUrlList is not None:
                                for companyUrl in companyUrlList:
                                    companyUrlArr.append('https://www.buildzoom.com' + companyUrl['href'].strip())

                            companyRating = 0
                            companyRatingList = companyMainDiv.find_all('span', attrs={'itemprop': 'ratingValue'})
                            if companyRatingList is not None and len(companyRatingList) > 0:
                                for companyRating in companyRatingList:
                                    companyRating = companyRating.text.strip()
                            else:
                                companyRatingListOuter = companyMainDiv.find('div', attrs={'class': 'contractor-reviews'})
                                if companyRatingListOuter is not None:
                                    spanRatingObj = companyRatingListOuter.find('span', attrs={'class': 'hidden'})
                                    if spanRatingObj is not None:
                                        companyRating = spanRatingObj.text.strip()

                            companyRatingArr.append(companyRating)

                            companyReviewsCount = 0
                            companyRatingCountList = companyMainDiv.find_all('span', attrs={'itemprop': 'reviewCount'})
                            if companyRatingCountList is not None and len(companyRatingCountList) > 0:
                                for companyRatingCount in companyRatingCountList:
                                    companyReviewsCount = companyRatingCount.text.strip()
                            else:
                                companyReviewsListOuter = companyMainDiv.find('div', attrs={'class': 'contractor-reviews'})
                                if companyReviewsListOuter is not None:
                                    aHrefObj = companyReviewsListOuter.find('a')
                                    if aHrefObj is not None:
                                        spanReviewCountObj = aHrefObj.find('span')
                                        if spanReviewCountObj is not None:
                                            companyReviewsCount = spanReviewCountObj.text.strip()

                            companyDetailsArr.append(companyReviewsCount)

                        fields = ['name', 'url', 'rating', 'total_ratings']
                        rows = []

                        for (name, landingUrl, rating, totalRatings) in zip(companyNameArr, companyUrlArr, companyRatingArr, companyDetailsArr):
                            rows.append([name, landingUrl, rating, totalRatings])

                        ts = datetime.datetime.now().timestamp()
                        writeCSV(f"tmp/buildzoom_{category}.csv", fields, rows)

                        #lets try and extract next page url
                        nextPageUrlElement = soup.find('a', attrs={'rel': 'next'})
                        if nextPageUrlElement is not None:
                            nextUrl = 'https://www.buildzoom.com' + nextPageUrlElement['href']
                            time.sleep(3)
                            scrapeBuildzoomDirectory(headersArr, url, nextUrl, category)
            except Exception as e:
                error = e
                print(e)
                pass

def scrapeBBBDirectory(headersArr, refererUrl, url, category):
    headersArr['referer'] = refererUrl
    headersArr['authority'] = 'www.bbb.org'
    headersArr['path'] = url.replace('https://www.bbb.org', '')
    resultArr = Network.fetch(Network.GET, url, headersArr)
    # with open('tmp/yelpdirectory.html') as file:
    #     resultArr = {
    #         'code': 200,
    #         'body': file.read()
    #     }

    if resultArr['code'] == 200:
        jsonStr = resultArr['body']
        jsonArr = json.loads(jsonStr)

        if len(jsonArr) > 0:
            companyNameArr = []
            companyUrlArr = []
            companyRatingArr = []
            companyDetailsArr = []

            try:
                for result in jsonArr['results']:
                    businessName = result['businessName'].strip()
                    companyNameArr.append(result['businessName'].strip().replace('<em>', '').replace('</em>', ''))
                    companyUrlArr.append(result['reportUrl'].strip())
                    companyRatingArr.append(result['rating'])
                    companyDetailsArr.append(result['score'])

                fields = ['name', 'url', 'rating', 'rating_score']
                rows = []

                for (name, landingUrl, rating, totalRatings) in zip(companyNameArr, companyUrlArr, companyRatingArr, companyDetailsArr):
                    rows.append([name, landingUrl, rating, totalRatings])

                ts = datetime.datetime.now().timestamp()
                writeCSV(f"tmp/bbb_{category}.csv", fields, rows)

                #lets try and extract next page url
                currentPageNum = jsonArr['page']
                totalPages = jsonArr['totalPages']
                if currentPageNum < totalPages:
                    regex = r"&page=(.*?)&"
                    nextPageNumber = currentPageNum + 1
                    subst = f"&page={nextPageNumber}&"
                    nextUrl = re.sub(regex, subst, url, 0, re.MULTILINE)
                    time.sleep(3)
                    scrapeBBBDirectory(headersArr, url.replace('api/', ''), nextUrl, category)
            except Exception as e:
                error = e
                print(e)
                pass


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
            bodyHtml = bodyHtml.replace("\\u0026","&").replace("\\u003d","=").replace("\\n",'\n')

            # with open('tmp/google1.html') as file:
            #     resultArr = {
            #         'code': 200,
            #         'body': file.read()
            #     }
            # bodyHtml = resultArr['body']

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
                        bodyHtml = bodyHtml.replace("\\u0026","&").replace("\\u003d","=").replace("\\n",'\n')
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


userAgent = UserAgent()
headersArr = userAgent.getRandom()

#url = "https://www.topratedlocal.com/philadelphia-pa-usa/window-installation-near-me"
#scrapeTopRatedDirectory(headersArr, 'https://www.topratedlocal.com', url, 'windows-installation')

#url = "https://www.yelp.com/search?find_desc=Windows%20and%20Doors&find_loc=Philadelphia%2C%20PA"
#scrapeYelpDirectory(headersArr, 'https://www.yelp.com', url, 'windowsdoors')

url = "https://www.buildzoom.com/philadelphia-pa/windows-and-doors"
scrapeBuildzoomDirectory(headersArr, 'https://www.buildzoom.com/', url, 'windows-and-doors')

#url = "https://www.bbb.org/api/search?find_country=USA&find_latlng=39.989654%2C-75.148976&find_loc=Philadelphia%2C%20PA&find_text=windows%20and%20doors&page=1&sort=Distance"
scrapeBBBDirectory(headersArr, 'https://www.bbb.org', url, 'windows-doors')

#url = "https://www.google.com/search?tbm=lcl&q=windows+and+doors+replacement+companies+in+philadelphia&spell=1&sa=X&ved=2ahUKEwiUsIfJ3ZTyAhXRyIsBHe4JDsoQBSgAegQIAxAm&biw=1366&bih=657&dpr=1#rlfi=hd:;si:;mv:[[40.1328331,-74.9924552],[39.902724299999996,-75.18228760000001]];tbs:lrf:!1m4!1u3!2m2!3m1!1e1!1m4!1u2!2m2!2m1!1e1!2m1!1e2!2m1!1e3!3sIAE,lf:1,lf_ui:14"
#scrapeGoogleLocalDirectory(headersArr, 'https://www.google.com/', url, 'windows-doors')

url = "https://www.google.com/search?tbm=lcl&q=windows+and+doors+replacement+companies+in+philadelphia&spell=1&sa=X&ved=2ahUKEwiUsIfJ3ZTyAhXRyIsBHe4JDsoQBSgAegQIAxAm&biw=1366&bih=657&dpr=1#rlfi=hd:;si:;mv:[[40.1328331,-74.9924552],[39.902724299999996,-75.18228760000001]];tbs:lrf:!1m4!1u3!2m2!3m1!1e1!1m4!1u2!2m2!2m1!1e1!2m1!1e2!2m1!1e3!3sIAE,lf:1,lf_ui:14"
scrapeGoogleDirectory(headersArr, 'https://www.google.com/', url, 'windows-door', None)
