import requests
from reviews.common.useragents import UserAgent
from reviews.common.config import config


class Network:
    def fetch(url, headersArr):
        returnArr = {}
        try:
            if len(headersArr) == 0:
                useragent = UserAgent()
                headersArr.update(useragent.getRandom())

            if config.get('proxy_enabled') is True:
                proxies = {'https': config.get('proxy_url_ip')}
                response = requests.get(url, headers=headersArr, proxies=proxies)
            else:
                response = requests.get(url, headers=headersArr)
            returnArr = {"code": response.status_code, "headers": response.headers, "body": response.content.decode()}
        except Exception as e:
            print(e)

        return returnArr
