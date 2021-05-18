import requests
from reviews.common.useragents import UserAgent


class Network:
    def fetch(url, headersArr):
        returnArr = {}
        try:
            useragent = UserAgent()
            headersArr.update(useragent.getRandom())
            response = requests.get(url, headers=headersArr)
            returnArr = {"code": response.status_code, "headers": response.headers, "body": response.content}
        except Exception as e:
            print(e)

        return returnArr
