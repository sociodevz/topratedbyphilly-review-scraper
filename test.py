import os
import pathlib
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


#url = "https://www.topratedlocal.com/philadelphia-pa-usa/window-installation-near-me"
#scrapeTopRatedDirectory(url, 'windows-installation')

#url = "https://www.yelp.com/search?find_desc=Windows%20and%20Doors&find_loc=Philadelphia%2C%20PA"
#scrapeYelpDirectory(url, 'windowsdoors')
