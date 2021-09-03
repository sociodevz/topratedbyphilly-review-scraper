from abc import ABC, abstractclassmethod


class ScraperInterface(ABC):

    @abstractclassmethod
    def scrapeListings(self, url, csvFileNamePath):
        pass

    @abstractclassmethod
    def scrapeReviews(self, url):
        pass

    @abstractclassmethod
    def scrapeImages(self, url, imageSavePath):
        pass
