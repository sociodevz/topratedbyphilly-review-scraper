import dateparser
import pytz
from datetime import datetime
from reviews.common.functions import convertStringDate2Date
from reviews.common.logger import logger


class ReviewFormatter:
    platform = None
    reviewObj = None

    def __init__(self, platform):
        self.platform = platform
        pass

    def format(self, reviewObj):
        try:
            self.reviewObj = reviewObj
            funcName = f"self._format{self.platform}Review"
            result = eval(funcName + "()")
        except Exception as e:
            logger.exception('Exception')
            pass

        return result

    def _getTemplate(self):
        result = reviewTemplate = {
            "id": 0,
            "user": {
                "id": None,
                "name": None,
            },
            "review": {
                "rating": None,
                "text": None,
            },
            "date": None,
            "misc": {
                "user": {
                    "pic": None,
                    "level": None,
                    "city": None,
                    "state": None,
                    "zip": None,
                    "reviews": {
                        "total": -1
                    }
                },
                "review": {
                    "headline": None,
                    "business_response": {
                        "date": None,
                        "text": None,
                    }
                },
            },
            "dump": {}
        }

        return result

    def _formatGooglemapsReview(self):
        result = self._getTemplate()

        try:
            result["id"] = self.reviewObj["review_id"]
            result["user"]["id"] = self.reviewObj["user_id"]
            result["user"]["name"] = self.reviewObj["name"]
            result["review"]["rating"] = self.reviewObj["rating"]
            result["review"]["text"] = self.reviewObj["review"]
            result["date"] = convertStringDate2Date(self.reviewObj["date"])

            result["misc"]["user"]["pic"] = self.reviewObj["profile_image"]
            result["misc"]["user"]["level"] = self.reviewObj["level"]
            result["misc"]["user"]["reviews"]["total"] = self.reviewObj["total_reviews"]

            if self.reviewObj["review_response_date"] is not None:
                result["misc"]["review"]["business_response"]["date"] = convertStringDate2Date(self.reviewObj["review_response_date"])
                result["misc"]["review"]["business_response"]["text"] = self.reviewObj["review_response"]

        except Exception as e:
            logger.exception('Exception')
            pass

        return result

    def _formatBbbReview(self):
        result = self._getTemplate()

        try:
            result["id"] = self.reviewObj["id"]
            result["user"]["id"] = 0
            result["user"]["name"] = self.reviewObj["displayName"]

            result["review"]["rating"] = self.reviewObj["reviewStarRating"]
            if self.reviewObj['hasExtendedText'] is True:
                if type(self.reviewObj['extendedText']) is list:
                    for response in self.reviewObj['extendedText']:
                        if response['isCustomer'] is True:
                            result["review"]["text"] = response["text"]
                        elif response['isBusiness'] is True:
                            result["misc"]["review"]["business_response"]["text"] = response["text"]
                else:
                    result["review"]["text"] = self.reviewObj["extendedText"]["text"]
            else:
                result["review"]["text"] = self.reviewObj["text"]
            result["date"] = dateparser.parse(f"{self.reviewObj['date']['year']}-{self.reviewObj['date']['month']}-{self.reviewObj['date']['day']}").isoformat()

            result["dump"] = self.reviewObj
        except Exception as e:
            logger.exception('Exception')
            pass

        return result

    def _formatYelpReview(self):
        result = self._getTemplate()

        result["id"] = self.reviewObj["id"]
        result["user"]["id"] = self.reviewObj["userId"]
        result["user"]["name"] = self.reviewObj["user"]["markupDisplayName"]
        result["misc"]["user"]["reviews"]["total"] = self.reviewObj["user"]["reviewCount"]

        result["review"]["rating"] = self.reviewObj["rating"]
        result["review"]["text"] = self.reviewObj["comment"]["text"]
        result["date"] = dateparser.parse(self.reviewObj['localizedDate']).isoformat()

        if type(self.reviewObj['businessOwnerReplies']) is list:
            for response in self.reviewObj['businessOwnerReplies']:
                result["misc"]["review"]["business_response"]["text"] = response["comment"]

        result["dump"] = self.reviewObj

        return result

    def _formatHomeadvisorReview(self):
        result = self._getTemplate()

        result["id"] = self.reviewObj["ratingID"]
        result["user"]["id"] = self.reviewObj["consumerID"]
        result["user"]["name"] = self.reviewObj["consumerName"]

        result["review"]["rating"] = self.reviewObj["consumerOverallScore"]
        result["review"]["text"] = self.reviewObj["comment"]
        result["date"] = datetime.fromtimestamp((self.reviewObj['createDate']/1000)).isoformat()

        result["misc"]["user"]["city"] = self.reviewObj["consumerCity"]
        result["misc"]["user"]["state"] = self.reviewObj["consumerState"]
        result["misc"]["user"]["zip"] = self.reviewObj["consumerZip"]

        result["dump"] = self.reviewObj

        return result

    def _formatHouzzreview(self):
        result = self._getTemplate()

        result["id"] = self.reviewObj["reviewId"]
        result["user"]["id"] = self.reviewObj["userId"]
        result["user"]["name"] = self.reviewObj["user_info"]["displayName"]

        result["review"]["rating"] = self.reviewObj["rating"]
        result["review"]["text"] = self.reviewObj["body"]
        result["date"] = datetime.fromtimestamp((self.reviewObj['created'])).isoformat()
        result["dump"] = self.reviewObj

        return result

    def _formatTrustpilotReview(self):
        result = self._getTemplate()

        result["id"] = 0
        result["user"]["id"] = 0
        result["user"]["name"] = self.reviewObj["author"]["name"]

        result["review"]["rating"] = int(self.reviewObj["reviewRating"]["ratingValue"])
        result["review"]["text"] = self.reviewObj["reviewBody"]
        result["date"] = dateparser.parse(self.reviewObj['datePublished']).isoformat()

        result["misc"]["review"]["headline"] = self.reviewObj["headline"]

        result["dump"] = self.reviewObj

        return result


    def _formatBuildzoomReview(self):
        result = self._getTemplate()

        result["id"] = self.reviewObj["id"]
        result["user"]["id"] = 0
        result["user"]["name"] = self.reviewObj["author"]["name"]

        result["review"]["rating"] = int(self.reviewObj["reviewRating"]["ratingValue"])
        result["review"]["text"] = self.reviewObj["reviewBody"]
        result["date"] = dateparser.parse(self.reviewObj['datePublished']).isoformat()

        result["misc"]["review"]["business_response"]["text"] = self.reviewObj["reviewResponse"]

        result["dump"] = self.reviewObj

        return result


    def _formatAngiReview(self):
        result = self._getTemplate()

        result["id"] = self.reviewObj["id"]
        result["user"]["id"] = 0
        result["user"]["name"] = 'Anonymous'

        result["review"]["rating"] = int(self.reviewObj["ratings"][0]["starRating"])
        result["review"]["text"] = self.reviewObj["reviewText"]
        result["date"] = dateparser.parse(self.reviewObj['reportDate']).isoformat()

        businessResponse = None
        if 'retort' in self.reviewObj:
            businessResponse = self.reviewObj['retort']['text']
            result["misc"]["review"]["business_response"]["text"] = businessResponse

        result["dump"] = self.reviewObj

        return result

    def _formatGafReview(self):
        result = self._getTemplate()

        try:
            result["id"] = self.reviewObj["id"]
            result["user"]["id"] = 0
            result["user"]["name"] = self.reviewObj['author']['name']

            result["review"]["rating"] = self.reviewObj["reviewRating"]["ratingValue"]
            result["review"]["text"] = self.reviewObj["reviewBody"]
            result["date"] = dateparser.parse(self.reviewObj['datePublished']).isoformat()

            businessResponse = None
            if 'retort' in self.reviewObj:
                businessResponse = self.reviewObj['retort']['text']
                result["misc"]["review"]["business_response"]["text"] = businessResponse

            result["dump"] = self.reviewObj
        except Exception as e:
            logger.exception('Exception')
            pass

        return result

    def _formatBestpickreportsReview(self):
        result = self._getTemplate()

        try:
            result["id"] = self.reviewObj["id"]
            result["user"]["id"] = 0
            result["user"]["name"] = self.reviewObj['author']['name']

            result["review"]["rating"] = self.reviewObj["reviewRating"]["ratingValue"]
            result["review"]["text"] = self.reviewObj["reviewBody"]
            result["date"] = dateparser.parse(self.reviewObj['datePublished']).isoformat()

            result["dump"] = self.reviewObj
        except Exception as e:
            logger.exception('Exception')
            pass

        return result

    def _formatFacebookReview(self):
        result = self._getTemplate()

        tz = pytz.timezone('UTC')

        try:
            result["id"] = self.reviewObj["review_id"]
            result["user"]["id"] = self.reviewObj["user_id"]
            result["user"]["name"] = self.reviewObj["name"]
            result["review"]["rating"] = self.reviewObj["rating"]
            result["review"]["text"] = self.reviewObj["review"]
            result["date"] = datetime.fromtimestamp(self.reviewObj["date"], tz).isoformat()

            result["misc"]["user"]["pic"] = self.reviewObj["profile_image"]
            result["misc"]["user"]["level"] = self.reviewObj["level"]
            result["misc"]["user"]["reviews"]["total"] = self.reviewObj["total_reviews"]

            if self.reviewObj["review_response_date"] is not None:
                result["misc"]["review"]["business_response"]["date"] = datetime.fromtimestamp(self.reviewObj["review_response_date"], tz).isoformat()
                result["misc"]["review"]["business_response"]["text"] = self.reviewObj["review_response"]

        except Exception as e:
            logger.exception('Exception')
            pass

        return result

    def _formatThumbtackReview(self):
        result = self._getTemplate()

        tz = pytz.timezone('UTC')

        try:
            result["user"]["name"] = self.reviewObj["attribution"]
            result["review"]["rating"] = self.reviewObj["rating"]["rating"]
            if len(self.reviewObj["text"]["segments"]) > 0:
                result["review"]["text"] = ''
            for segment in self.reviewObj["text"]["segments"]:
                result["review"]["text"] += segment["text"]

            datetimeObj = datetime.strptime(self.reviewObj['labels'][0]['text'].replace(',', ''), '%b %d %Y')
            result["date"] = datetimeObj.isoformat()

            if 'response' in self.reviewObj:
                if self.reviewObj['response'] is not None:
                    result["misc"]["review"]["business_response"]["text"] = self.reviewObj["response"]["text"]

            result["dump"] = self.reviewObj
        except Exception as e:
            logger.exception('Exception')
            pass

        return result
