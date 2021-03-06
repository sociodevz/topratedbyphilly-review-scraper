import os
import pathlib
import csv
from datetime import date, timedelta
from pathlib import Path
from csv import writer
from reviews.common.config import config


def convertStringDate2Date(dateStr):
    result = None

    currentDate = date.today().isoformat()
    dateStrArr = dateStr.split(' ')
    dateValue = dateStrArr[0]
    timeStr = dateStrArr[1]

    if dateValue == 'a':
        dateValue = 1
    else:
        dateValue = int(dateValue)

    if timeStr == 'hour' or timeStr == 'hours':
        result = (date.today()-timedelta(hours=dateValue)).isoformat()
    elif timeStr == 'day' or timeStr == 'days':
        result = (date.today()-timedelta(days=dateValue)).isoformat()
    elif timeStr == 'week' or timeStr == 'weeks':
        result = (date.today()-timedelta(weeks=dateValue)).isoformat()
        pass
    elif timeStr == 'month' or timeStr == 'months':
        result = (date.today()-timedelta(days=30*dateValue)).isoformat()
        pass
    elif timeStr == 'year' or timeStr == 'years':
        result = (date.today()-timedelta(days=365*dateValue)).isoformat()
        pass

    return result


def fixLocalBusinessJSON(jsonObj):

    fields = ['name', 'telephone', 'address']
    for field in fields:
        if field not in jsonObj:
            jsonObj[field] = None

    if 'aggregateRating' not in jsonObj:
        jsonObj['aggregateRating'] = {
            'ratingValue': 0,
            'reviewCount': 0,
            'ratingCount': 0,
        }
    else:
        if 'ratingValue' not in jsonObj['aggregateRating']:
            jsonObj['aggregateRating']['ratingValue'] = 0
        if 'reviewCount' not in jsonObj['aggregateRating']:
            jsonObj['aggregateRating']['reviewCount'] = 0
        if 'ratingCount' not in jsonObj['aggregateRating']:
            jsonObj['aggregateRating']['ratingCount'] = 0

    return jsonObj


def reviewsCleanup(self, reviewJSON):
    result = reviewJSON

    result = result.replace(',"@type":"Person"', '')
    result = result.replace(',"@type":"Review"', '')
    result = result.replace(',"@type":"Rating"', '')
    result = result.replace(',"@type":"Thing"', '')
    result = result.replace(',"@type":"PostalAddress"', '')

    return result


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


def getOfflineFile(url):
    result = None

    try:
        filePath = config.get('project_physical_root_path') + 'reviews/main/sites'
        file = open(f"{filePath}/sample_data/{url}")
        result = file.read()
    except FileNotFoundError as e:
        pass

    return result

