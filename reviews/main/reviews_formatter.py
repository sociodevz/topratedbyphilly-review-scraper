from datetime import datetime

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
        result["date"] = reviewObj["date"]

        return result

    def _formatBbbReview(self, reviewObj):
        result = self._getTemplate()

        result["id"] = reviewObj["id"]
        result["user"]["id"] = 0
        result["user"]["name"] = reviewObj["displayName"]
        result["user"]["level"] = None
        result["user"]["reviews"]["total"] = -1

        result["review"]["rating"] = reviewObj["reviewStarRating"]
        if len(reviewObj["extendedText"]) > 0:
            result["review"]["text"] = reviewObj["extendedText"][0]["text"]
        result["date"] = f"{reviewObj['date']['year']}-{reviewObj['date']['month']}-{reviewObj['date']['day']}"

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
        result["date"] = reviewObj['localizedDate']

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
