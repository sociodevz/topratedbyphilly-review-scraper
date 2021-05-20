import random
from collections import OrderedDict


class UserAgent:
    headersList = [
        # Firefox 77 Mac
        {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "accept-Language": "en-US,en;q=0.5",
            "referer": "https://www.google.com/",
            "dnt": "1",
            "connection": "keep-alive",
            "upgrade-insecure-requests": "1"
        },
        # Firefox 77 Windows
        {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "accept-Language": "en-US,en;q=0.5",
            "accept-Encoding": "gzip, deflate",
            "referer": "https://www.google.com/",
            "dnt": "1",
            "connection": "keep-alive",
            "upgrade-insecure-requests": "1"
        },
        # Chrome 83 Mac
        {
            "connection": "keep-alive",
            "dnt": "1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-dest": "document",
            "referer": "https://www.google.com/",
            "accept-Encoding": "gzip, deflate",
            "accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
        },
        # Chrome 83 Windows
        {
            "connection": "keep-alive",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "navigate",
            "Sec-Fetch-User": "?1",
            "sec-fetch-dest": "document",
            "referer": "https://www.google.com/",
            "accept-Encoding": "gzip, deflate",
            "accept-Language": "en-US,en;q=0.9"
        }
    ]

    def __init__(self):
        pass

    def getRandom(self):
        return random.choice(self.headersList)
