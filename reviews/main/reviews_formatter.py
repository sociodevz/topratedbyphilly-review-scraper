import dateparser
from datetime import datetime
from reviews.common.functions import convertStringDate2Date

class ReviewFormatter:
    platform = None

    def __init__(self, platform):
        self.platform = platform
        pass

    def format(self, reviewObj):
        if self.platform == "googlemaps":
            result = self._formatGoogleMapsReview(reviewObj)
        elif self.platform == "bbb":
            result = self._formatBbbReview(reviewObj)
        elif self.platform == "yelp":
            result = self._formatYelpReview(reviewObj)
        elif self.platform == "homeadvisor":
            result = self._formatHomeAdvisorReview(reviewObj)
        elif self.platform == "houzz":
            result = self._formatHouzzReview(reviewObj)
        elif self.platform == "trustpilot":
            result = self._formatTrustPilotReview(reviewObj)


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

    def _formatGoogleMapsReview(self, reviewObj):
        result = self._getTemplate()

        result["id"] = reviewObj["review_id"]
        result["user"]["id"] = reviewObj["user_id"]
        result["user"]["name"] = reviewObj["name"]
        result["user"]["level"] = reviewObj["level"]
        result["user"]["reviews"]["total"] = reviewObj["total_reviews"]

        result["review"]["rating"] = reviewObj["rating"]
        result["review"]["text"] = reviewObj["review"]
        result["date"] = convertStringDate2Date(reviewObj["date"])

        return result

    def _formatBbbReview(self, reviewObj):
        result = self._getTemplate()

        try:
            result["id"] = reviewObj["id"]
            result["user"]["id"] = 0
            result["user"]["name"] = reviewObj["displayName"]
            result["user"]["level"] = None
            result["user"]["reviews"]["total"] = -1

            result["review"]["rating"] = reviewObj["reviewStarRating"]
            if reviewObj['hasExtendedText'] is True:
                result["review"]["text"] = reviewObj["extendedText"]["text"]
            else:
                result["review"]["text"] = reviewObj["text"]
            result["date"] = dateparser.parse(f"{reviewObj['date']['year']}-{reviewObj['date']['month']}-{reviewObj['date']['day']}").isoformat()
        except Exception as e:
            error = e
            pass

        return result

    def _formatYelpReview(self, reviewObj):
        result = self._getTemplate()

        result["id"] = reviewObj["id"]
        result["user"]["id"] = reviewObj["userId"]
        result["user"]["name"] = reviewObj["user"]["markupDisplayName"]
        result["user"]["level"] = None
        result["user"]["reviews"]["total"] = reviewObj["user"]["reviewCount"]

        result["review"]["rating"] = reviewObj["rating"]
        result["review"]["text"] = reviewObj["comment"]["text"]
        result["date"] = dateparser.parse(reviewObj['localizedDate']).isoformat()

        result["dump"] = reviewObj

        return result

    def _formatHomeAdvisorReview(self, reviewObj):
        result = self._getTemplate()

        result["id"] = reviewObj["ratingID"]
        result["user"]["id"] = reviewObj["consumerID"]
        result["user"]["name"] = reviewObj["consumerName"]
        result["user"]["level"] = None
        result["user"]["reviews"]["total"] = None

        result["review"]["rating"] = reviewObj["consumerOverallScore"]
        result["review"]["text"] = reviewObj["comment"]
        result["date"] = datetime.fromtimestamp((reviewObj['createDate']/1000)).isoformat()

        result["misc"] = {
            "user": {
                "city": reviewObj["consumerCity"],
                "state": reviewObj["consumerState"],
                "zip": reviewObj["consumerZip"]
            }
        }
        result["dump"] = reviewObj

        return result

    def _formatHouzzReview(self, reviewObj):
        result = self._getTemplate()

        result["id"] = reviewObj["reviewId"]
        result["user"]["id"] = reviewObj["userId"]
        result["user"]["name"] = reviewObj["user_info"]["displayName"]
        result["user"]["level"] = None
        result["user"]["reviews"]["total"] = None

        result["review"]["rating"] = reviewObj["rating"]
        result["review"]["text"] = reviewObj["body"]
        result["date"] = datetime.fromtimestamp((reviewObj['created'])).isoformat()
        result["dump"] = reviewObj

        return result

    def _formatTrustPilotReview(self, reviewObj):
        result = self._getTemplate()

        result["id"] = 0
        result["user"]["id"] = 0
        result["user"]["name"] = reviewObj["author"]["name"]
        result["user"]["level"] = None
        result["user"]["reviews"]["total"] = None

        result["review"]["rating"] = int(reviewObj["reviewRating"]["ratingValue"])
        result["review"]["text"] = reviewObj["reviewBody"]
        result["date"] = dateparser.parse(reviewObj['datePublished']).isoformat()

        result["misc"] = {
            "review": {
                "headline": reviewObj["headline"]
            }
        }

        result["dump"] = reviewObj

        return result
