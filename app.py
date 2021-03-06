from flask import Flask, request, jsonify
from flask.helpers import url_for
from reviews.main.scraper import ScraperFactory
from reviews.common.config import config, updateConfigFromArgs
import requests
import json


app = Flask("Review Scraper")
app.config['JSON_SORT_KEYS'] = False

@app.route('/scrape', methods=['POST'])
def scrape():
    engine = request.form.get('engine').title()
    url = request.form.get('url')
    scraper = ScraperFactory.get_client(engine)
    result = scraper.scrapeReviews(url)
    response = {
        'result': {
            'success': True,
            'data': result
        }
    }

    if len(result) == 0:
        response['result']['success'] = False
        response['result'].pop('data')
    return jsonify(response), 200


# Todo: disable below when running using gunicorn
#app.run(host='0.0.0.0', port=5051, debug=config.get('debug'))
