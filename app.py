from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from bson.json_util import dumps
import bson
import json
from datetime import datetime
from feeds import feeds
from crawler import db, processEntry
import feedparser
from os import getcwd,mkdir
import traceback
from shutil import rmtree

def setup():
    installed = list(db["feeds"].find())
    if len(installed) < 1:
        db['feeds'].insert_many(feeds)
        print("Installed all feeds: {}".format(", ".join([feed["_id"] for feed in feeds])))
    else:
        for feed in feeds:
            print("Processing feed {}".format(feed['_id']))
            if feed['_id'] in [item['_id'] for item in installed]:
                print("\tFeed is already installed") 
            else:
                print("\tAdding config for feed.")
                db['feeds'].insert_one(feed)

def returnPrettyJson(data):
    try:
        return jsonify(**json.loads(dumps(data)))
    except TypeError:
        try:
            return jsonify(*json.loads(dumps(data)))
        except TypeError:
            try: 
                return dumps(data)
            except TypeError:
                return repr(data)
        

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

setup()

@app.get("/feeds")
def getFeeds():
    try:
        feedList = list(db['feeds'].find({}))
        return returnPrettyJson(feedList), 200
    except Exception as e:
        return returnPrettyJson(e),500

@app.post("/feeds")
def postFeed():
    try:
        feed = db['feeds'].insert_one(request.form)
        return returnPrettyJson(feed), 200
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/feed/<string:feedId>")
def getFeed(feedId):
    try:
        config = db['feeds'].find_one({'_id':feedId})
        return returnPrettyJson(config), 200
    except Exception as e:
        return returnPrettyJson(e),500
    
@app.get("/feed/<string:feedId>/history")
def getFeedCrawlHistory(feedId):
    try:
        crawls = list(db['logs'].find({'feedId':feedId}).sort('end',-1))
        return returnPrettyJson(crawls)
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/feed/<string:feedId>/test")
def testFeed(feedId):
    try:
        config = db['feeds'].find_one({'_id':feedId})
        feed = feedparser.parse(config['url'])
        dir = '{}/{}'.format(getcwd(),'test')
        try:
            mkdir(dir)
        except FileExistsError:
            pass
        try:
            processEntry(feed.entries[0],config,dir)
        except Exception as e:
            return traceback.format_exc(),500
        
        rmtree(dir)
        return returnPrettyJson(feed.entries[0]),200
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/feed/<string:feedId>/start")
def queueCrawl(feedId):
    try:
        config = db['feeds'].find_one({'_id':feedId})
        if not 'status' in config or config['status'] == 'stopped':
            r = db['queue'].insert_one({'queued_time':datetime.now(),'status':'waiting','config':config})
            return returnPrettyJson({'crawl_queue_id':r.inserted_id,'status':{'queued_time':datetime.now(),'status':'waiting','config':config}}),200
        elif config['status'] == 'running':
            crawlStatus = db['logs'].find_one({'_id':bson.ObjectId(config['crawlId'])})
            return returnPrettyJson({'msg':'Feed {} already running'.format(feedId),'status':crawlStatus}),200
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/crawls")
def getCrawls():
    try:
        crawls = list(db['logs'].find().sort('end',-1))
        return returnPrettyJson(crawls)
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/crawl/<string:crawlId>")
def getCrawl(crawlId):
    try:
        crawlStatus = db['logs'].find_one({'_id':bson.ObjectId(crawlId)})
        return returnPrettyJson(crawlStatus)
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/queue")
def getQueue():
    try:
        crawls = list(db['queue'].find().sort('start',-1))
        return returnPrettyJson(crawls),200
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/queue/<string:crawlId>")
def queuedTask(crawlId):
    try:
        status = db['queue'].find_one({'_id':bson.ObjectId(crawlId)})
        return returnPrettyJson(status),200
    except Exception as e:
        return returnPrettyJson(e),500

