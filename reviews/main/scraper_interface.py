from abc import ABC, abstractclassmethod


class IScraper(ABC):
    """Interface file for site scrapers"""

    @abstractclassmethod
    def scrapeListings(self, url, csvFileNamePath):
        pass

    @abstractclassmethod
    def scrapeReviews(self, url):
        pass

    @abstractclassmethod
    def scrapeImages(self, url, imageSavePath):
        pass
