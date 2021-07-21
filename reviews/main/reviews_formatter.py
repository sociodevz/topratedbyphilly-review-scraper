import dateparser
from datetime import datetime
from reviews.common.functions import convertStringDate2Date

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
            error = e
            pass

        return result

    def _getTemplate(self):
        result = reviewTemplate = {
            "id": 0,
            "user": {
                "id": None,
                "name": None,
                "level": None,
                "reviews": {
                    "total": 0
                },
            },
            "review": {
                "rating": None,
                "text": None,
            },
            "date": None,
            "misc": {},
            "dump": {}
        }

        return result

    def _formatGooglemapsReview(self):
        result = self._getTemplate()

        result["id"] = self.reviewObj["review_id"]
        result["user"]["id"] = self.reviewObj["user_id"]
        result["user"]["name"] = self.reviewObj["name"]
        result["user"]["level"] = self.reviewObj["level"]
        result["user"]["reviews"]["total"] = self.reviewObj["total_reviews"]

        result["review"]["rating"] = self.reviewObj["rating"]
        result["review"]["text"] = self.reviewObj["review"]
        result["date"] = convertStringDate2Date(self.reviewObj["date"])

        return result

    def _formatBbbReview(self):
        result = self._getTemplate()

        try:
            result["id"] = self.reviewObj["id"]
            result["user"]["id"] = 0
            result["user"]["name"] = self.reviewObj["displayName"]
            result["user"]["level"] = None
            result["user"]["reviews"]["total"] = -1

            result["review"]["rating"] = self.reviewObj["reviewStarRating"]
            if self.reviewObj['hasExtendedText'] is True:
                result["review"]["text"] = self.reviewObj["extendedText"]["text"]
            else:
                result["review"]["text"] = self.reviewObj["text"]
            result["date"] = dateparser.parse(f"{self.reviewObj['date']['year']}-{self.reviewObj['date']['month']}-{self.reviewObj['date']['day']}").isoformat()

            result["dump"] = self.reviewObj
        except Exception as e:
            error = e
            pass

        return result

    def _formatYelpReview(self):
        result = self._getTemplate()

        result["id"] = self.reviewObj["id"]
        result["user"]["id"] = self.reviewObj["userId"]
        result["user"]["name"] = self.reviewObj["user"]["markupDisplayName"]
        result["user"]["level"] = None
        result["user"]["reviews"]["total"] = self.reviewObj["user"]["reviewCount"]

        result["review"]["rating"] = self.reviewObj["rating"]
        result["review"]["text"] = self.reviewObj["comment"]["text"]
        result["date"] = dateparser.parse(self.reviewObj['localizedDate']).isoformat()

        result["dump"] = self.reviewObj

        return result

    def _formatHomeadvisorReview(self):
        result = self._getTemplate()

        result["id"] = self.reviewObj["ratingID"]
        result["user"]["id"] = self.reviewObj["consumerID"]
        result["user"]["name"] = self.reviewObj["consumerName"]
        result["user"]["level"] = None
        result["user"]["reviews"]["total"] = None

        result["review"]["rating"] = self.reviewObj["consumerOverallScore"]
        result["review"]["text"] = self.reviewObj["comment"]
        result["date"] = datetime.fromtimestamp((self.reviewObj['createDate']/1000)).isoformat()

        result["misc"] = {
            "user": {
                "city": self.reviewObj["consumerCity"],
                "state": self.reviewObj["consumerState"],
                "zip": self.reviewObj["consumerZip"]
            }
        }
        result["dump"] = self.reviewObj

        return result

    def _formatHouzzreview(self):
        result = self._getTemplate()

        result["id"] = self.reviewObj["reviewId"]
        result["user"]["id"] = self.reviewObj["userId"]
        result["user"]["name"] = self.reviewObj["user_info"]["displayName"]
        result["user"]["level"] = None
        result["user"]["reviews"]["total"] = None

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
        result["user"]["level"] = None
        result["user"]["reviews"]["total"] = None

        result["review"]["rating"] = int(self.reviewObj["reviewRating"]["ratingValue"])
        result["review"]["text"] = self.reviewObj["reviewBody"]
        result["date"] = dateparser.parse(self.reviewObj['datePublished']).isoformat()

        result["misc"] = {
            "review": {
                "headline": self.reviewObj["headline"]
            }
        }

        result["dump"] = self.reviewObj

        return result


    def _formatBuildzoomReview(self):
        result = self._getTemplate()

        result["id"] = self.reviewObj["id"]
        result["user"]["id"] = 0
        result["user"]["name"] = self.reviewObj["author"]["name"]
        result["user"]["level"] = None
        result["user"]["reviews"]["total"] = None

        result["review"]["rating"] = int(self.reviewObj["reviewRating"]["ratingValue"])
        result["review"]["text"] = self.reviewObj["reviewBody"]
        result["date"] = dateparser.parse(self.reviewObj['datePublished']).isoformat()

        result["misc"] = {
            "review": {
                "response": self.reviewObj["reviewResponse"]
            }
        }

        result["dump"] = self.reviewObj

        return result


    def _formatAngiReview(self):
        result = self._getTemplate()

        result["id"] = self.reviewObj["id"]
        result["user"]["id"] = 0
        result["user"]["name"] = 'Anonymous'
        result["user"]["level"] = None
        result["user"]["reviews"]["total"] = None

        result["review"]["rating"] = int(self.reviewObj["ratings"][0]["starRating"])
        result["review"]["text"] = self.reviewObj["reviewText"]
        result["date"] = dateparser.parse(self.reviewObj['reportDate']).isoformat()

        businessResponse = None
        if 'retort' in self.reviewObj:
            businessResponse = self.reviewObj['retort']['text']

        result["misc"] = {
            "review": {
                "response": businessResponse
            }
        }

        result["dump"] = self.reviewObj

        return result

    def _formatGafReview(self):
        result = self._getTemplate()

        try:
            result["id"] = self.reviewObj["id"]
            result["user"]["id"] = 0
            result["user"]["name"] = self.reviewObj['author']['name']
            result["user"]["level"] = None
            result["user"]["reviews"]["total"] = None

            result["review"]["rating"] = self.reviewObj["reviewRating"]["ratingValue"]
            result["review"]["text"] = self.reviewObj["reviewBody"]
            result["date"] = dateparser.parse(self.reviewObj['datePublished']).isoformat()

            businessResponse = None
            if 'retort' in self.reviewObj:
                businessResponse = self.reviewObj['retort']['text']

            result["misc"] = {
                "review": {
                    "response": businessResponse
                }
            }

            result["dump"] = self.reviewObj
        except Exception as e:
            error = e
            pass

        return result
