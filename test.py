import os
import pathlib
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

def scrapeGoogleDirectory(headersArr, refererUrl, url, category):
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


userAgent = UserAgent()
headersArr = userAgent.getRandom()

#url = "https://www.topratedlocal.com/philadelphia-pa-usa/window-installation-near-me"
#scrapeTopRatedDirectory(headersArr, 'https://www.topratedlocal.com', url, 'windows-installation')

#url = "https://www.yelp.com/search?find_desc=Windows%20and%20Doors&find_loc=Philadelphia%2C%20PA"
#scrapeYelpDirectory(headersArr, 'https://www.yelp.com', url, 'windowsdoors')

#url = "https://www.buildzoom.com/philadelphia-pa/windows-and-doors"
#scrapeBuildzoomDirectory(headersArr, 'https://www.buildzoom.com/', url, 'windows-and-doors')

#url = "https://www.bbb.org/api/search?find_country=USA&find_latlng=39.989654%2C-75.148976&find_loc=Philadelphia%2C%20PA&find_text=windows%20and%20doors&page=1&sort=Distance"
#scrapeBBBDirectory(headersArr, 'https://www.bbb.org', url, 'windows-doors')

url = "https://www.google.com/search?tbm=lcl&q=windows+and+doors+replacement+companies+in+philadelphia&spell=1&sa=X&ved=2ahUKEwiUsIfJ3ZTyAhXRyIsBHe4JDsoQBSgAegQIAxAm&biw=1366&bih=657&dpr=1#rlfi=hd:;si:;mv:[[40.1328331,-74.9924552],[39.902724299999996,-75.18228760000001]];tbs:lrf:!1m4!1u3!2m2!3m1!1e1!1m4!1u2!2m2!2m1!1e1!2m1!1e2!2m1!1e3!3sIAE,lf:1,lf_ui:14"
scrapeGoogleDirectory(headersArr, 'https://www.google.com/', url, 'windows-doors')
