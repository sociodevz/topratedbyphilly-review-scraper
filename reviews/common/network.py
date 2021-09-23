import requests
import sys
import brotli
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from reviews.common.useragents import UserAgent
from reviews.common.config import config
from reviews.common.logger import logger


class Network:

    POST = "POST"
    GET = "GET"

    def fetch(method, headersArr, url, payloadArr=None, sessionDataArr=None):
        returnArr = {"code": 0}
        try:
            if headersArr is None or len(headersArr) == 0:
                headersArr = {}
                useragent = UserAgent()
                headersArr.update(useragent.getRandom())

            session = Network._retry_session(retries=5)

            proxies = None
            if config.get('proxy_enabled') is True:
                proxies = {'https': config.get('proxy_url_ip')}

            if sessionDataArr is not None:
                session.cookies = sessionDataArr

            if method == 'GET':
                retryCntr = 0
                retry = True
                while retry is True:
                    retry = False
                    response = session.get(url, headers=headersArr, proxies=proxies, data=payloadArr)
                    if response.status_code == 503:
                        if retryCntr < 2:
                            retry = True
                        retryCntr += 1
            elif method == 'POST':
                response = session.post(url, headers=headersArr, proxies=proxies, data=payloadArr)

            returnArr = {"code": response.status_code, "headers": {"requested": headersArr, "received": response.headers}, "cookies": response.cookies, "body": response.text}
            debugArr = {"code": response.status_code, "url": url}
            logger.info(f'Network Response: {debugArr}')
        except Exception as e:
            tb = sys.exc_info()[2]
            logger.exception(f'Network Error')

        return returnArr

    def _retry_session(retries, session=None, backoff_factor=0.3):
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            method_whitelist=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session



