from flask import render_template
from flask import request
from bson.json_util import dumps, RELAXED_JSON_OPTIONS
from bson.objectid import ObjectId
import json
from json import loads
from bson import json_util
from project import mongo
from flask import jsonify
from functools import wraps
import re
import newspaper
from newspaper import Article
import time
from time import mktime
from datetime import datetime
from pytz import timezone
import bs4
import feedparser as fp
import pandas as pd

from tasks import scrapeNews
from . import data_blueprint


@data_blueprint.route('/getData/', methods=['GET'])
def getData():

    news_collection = mongo.db.environment_collection #Replace testData to actual DB
    output = []
    try:
        news_articles = loads(dumps(news_collection.find({"title": "Hurricane Zeta Leaves Death And Destruction In Its Wake"}))) # make topic passable
        
        for article in news_articles:

            # structure schema here
            output.append({
                'title': article['title'],
                'summary': article['summary'],
                'source_name': article['source_name']
            })
        if len(output) == 0:
            output = {'code': 2, "error": "User not found"}
        else:
            output = {"count": len(output), "results": output}
    except:
        output = {'code': 2, "error": "Error fetching details from DB"}

    return output


@data_blueprint.route('/postData/', methods=['POST'])
def postData():
    request_json = request.get_json()
    url_list = request_json['url_list']
    all_news = []

    for news_source in url_list:


        feed_url = fp.parse(news_source)

        source_name = news_source
        #source_url = news_source
        url_feed = news_source
        article_list = []

        for article in feed_url.entries:
            article_dict = {}

            #date = article.published_parsed
            artilce_url = article.link

            content = Article(artilce_url) #Newspapaer 3k's Article module to read the contents
            try: 
                content.download() #Downloading the News article
                content.parse()
                content.nlp()  
                

            except:
                pass

            # Updating all the information to a dictionary

            article_dict.update({'source_name': source_name, 'source_url': url_feed, "article_url": artilce_url, 'image_url': content.top_image,'video_url': content.movies, 'publish_date':content.publish_date,'title':content.title, 'article': content.text, 'author':content.authors, "summary": content.summary, "keywords": content.keywords})
            article_list.append(article_dict)

        all_news.extend(article_list)

    fmt = '%Y-%m-%dT-%H-%M%Z%z'
    # define eastern timezone
    #eastern = timezone('US/Eastern')
    # naive datetime
    naive_dt = datetime.now()
    #loc_dt = datetime.now(eastern)
    start_time = naive_dt.strftime(fmt)

    print("Download started:", start_time)

    news_db = mongo.db.testData
    news_db.insert_many(all_news)

    print("Complete")
    
    return "Completed"
    

@data_blueprint.route('/scrapeURL/', methods=['GET'])
def scrapeURL():
    
    scrapeNews.delay()
    return "Scrape URL called"