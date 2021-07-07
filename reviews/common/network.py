import requests
import sys
import brotli
from reviews.common.useragents import UserAgent
from reviews.common.config import config


class Network:
    def fetch(url, headersArr):
        returnArr = {"code": 0}
        try:
            if len(headersArr) == 0:
                useragent = UserAgent()
                headersArr.update(useragent.getRandom())

            if config.get('proxy_enabled') is True:
                proxies = {'https': config.get('proxy_url_ip')}
                response = requests.get(url, headers=headersArr, proxies=proxies)
            else:
                response = requests.get(url, headers=headersArr)

            returnArr = {"code": response.status_code, "headers": {"requested": headersArr, "received": response.headers}, "body": response.text}
        except Exception as e:
            tb = sys.exc_info()[2]
            print(e.with_traceback(tb))

        return returnArr
