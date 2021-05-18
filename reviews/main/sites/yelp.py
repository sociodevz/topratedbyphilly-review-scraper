import requests
import sys
from reviews.common.network import Network


class Yelp:

    def __init__(self):
        print('Initalized Yelp shit')
        pass

    def scrapeURL(self, url):
        headersArr = {}
        scrapedRawData = Network.fetch(url, headersArr)
        if(scrapedRawData['code'] == 200):
            print(scrapedRawData)



