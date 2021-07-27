import requests
import sys
import brotli
from reviews.common.useragents import UserAgent
from reviews.common.config import config


class Network:

    POST = "POST"
    GET = "GET"

    def fetch(url, headersArr):
        returnArr = {"code": 0}
        try:
            if headersArr is None or len(headersArr) == 0:
                headersArr = {}
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

    def sessionFetch(method, url, payloadArr=None, headersArr=None, sessionDataArr=None):
        returnArr = {"code": 0}
        try:
            if headersArr is None or len(headersArr) == 0:
                headersArr = {}
                useragent = UserAgent()
                headersArr.update(useragent.getRandom())

            session = requests.session()

            proxies = None
            if config.get('proxy_enabled') is True:
                proxies = {'https': config.get('proxy_url_ip')}

            if sessionDataArr is not None:
                session.cookies = sessionDataArr

            if method == 'GET':
                response = session.get(url, headers=headersArr, proxies=proxies, data=payloadArr)
            elif method == 'POST':
                response = session.post(url, headers=headersArr, proxies=proxies, data=payloadArr)

            returnArr = {"code": response.status_code, "headers": {"requested": headersArr, "received": response.headers}, "cookies": response.cookies, "body": response.text}
        except Exception as e:
            tb = sys.exc_info()[2]
            print(e.with_traceback(tb))

        return returnArr
