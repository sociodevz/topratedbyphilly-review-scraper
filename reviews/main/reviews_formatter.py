

class ReviewFormatter:
    platform = None
    reviewTemplate = {
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
        "platform_specific": {}
    }

    def __init__(self, platform):
        self.platform = platform
        pass

    def format(self, reviewObj):
        if self.platform == "googlemaps":
            result = self._formatGoogleMapsReviews(reviewObj)
        elif self.platform == "bbb":
            result = self._formatBbbReviews(reviewObj)


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
            "platform_specific": {}
        }

        return result

    def _formatGoogleMapsReviews(self, reviewObj):
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

    def _formatBbbReviews(self, reviewObj):
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
