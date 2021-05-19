import os
import pathlib
import requests
from hashlib import sha256
from http.cookiejar import MozillaCookieJar
from reviews.common.config import config

siteUrl = 'https://www.houzz.com/professionals/roofing-and-gutters/northern-lights-exteriors-pfvwus-pf~973447938'
siteHash = sha256(siteUrl.encode('utf-8')).hexdigest()

cookiesFile = f"{config.get('project_physical_root_path')}tmp/cookies/{siteHash}.txt" # Places "cookies.txt" next to the script file.
cj = MozillaCookieJar(cookiesFile)
if os.path.exists(cookiesFile):  # Only attempt to load if the cookie file exists.
    cj.load(ignore_discard=True, ignore_expires=True)  # Loads session cookies too (expirydate=0).

s = requests.Session()
s.headers = {
    'authority': 'www.houzz.com',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'accept': '*/*',
    'x-requested-with': 'XMLHttpRequest',
    'x-hz-request': 'true',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'x-hz-view-mode': 'null',
    'sec-gpc': '1',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.houzz.com/professionals/roofing-and-gutters/northern-lights-exteriors-pfvwus-pf~973447938',
    'accept-language': 'en-GB,en;q=0.9',
}

s.cookies = cj  # Tell Requests session to use the cookiejar.

# DO STUFF HERE WHICH REQUIRES THE PERSISTENT COOKIES...
response = s.get("https://www.houzz.com/professionals/roofing-and-gutters/northern-lights-exteriors-pfvwus-pf~973447938")
response = s.get("https://www.houzz.com/j/ajax/profileReviewsAjax?userId=5057474&proId=177044&fromItem=12&itemsPerPage=134")
print(response.text)
cj.save(ignore_discard=True, ignore_expires=True)  # Saves session cookies too (expirydate=0).
