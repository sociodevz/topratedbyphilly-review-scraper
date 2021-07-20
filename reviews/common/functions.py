from datetime import date, timedelta


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

    if timeStr == 'day' or timeStr == 'days':
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
    if 'aggregateRating' not in jsonObj:
        jsonObj['aggregateRating'] = {
            'ratingValue': 0,
            'reviewCount': 0
        }

    return jsonObj


def reviewsCleanup(self, reviewJSON):
    result = reviewJSON

    result = result.replace(',"@type":"Person"', '')
    result = result.replace(',"@type":"Review"', '')
    result = result.replace(',"@type":"Rating"', '')
    result = result.replace(',"@type":"Thing"', '')
    result = result.replace(',"@type":"PostalAddress"', '')

    return result
