from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from bson.json_util import dumps
import bson
import json
from datetime import datetime
from feeds import feeds
from crawler import Entry
import feedparser
from os import getcwd,mkdir,getenv
import traceback
from shutil import rmtree
import pymongo

def connect():
    try:
        client = pymongo.MongoClient(getenv("MDBCONNSTR"))
        client.admin.command('ping')
        try:
            db = client.get_database(getenv("MDB_DB"))
            print("Successfully connected to MongoDB {} database!".format(db.name))
            return client, db
        except Exception as e:
            print(e)
            print("Failed to connect to {}. Quitting.".format(db))
            exit()
    except Exception as e:
        print(e)
        print("Failed to connect to MongoDB. Quitting.")
        exit()

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
client,db = connect()
setup()

@app.get("/feeds")
def getFeeds():
    try:
        feedList = list(db['feeds'].find({}).sort('crawl_date',-1))
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
        crawls = list(db['logs'].find({'feed_id':feedId}).sort('end',-1))
        return returnPrettyJson(crawls)
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/feed/<string:feedId>/history/clear")
def deleteFeedCrawlHistory(feedId):
    try:
        delete = db['logs'].delete_many({'feed_id':feedId})
        return returnPrettyJson(delete),200
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
            entry = Entry(
                DATA=feed.entries[0],
                DIR=dir,
                SELECTOR=config['content_html_selector'],
                LANG=config['lang'],
                ATTRIBUTION=config['attribution']).processEntry()
        except Exception as e:
            return traceback.format_exc(),500
        
        rmtree(dir)
        return returnPrettyJson(entry),200
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/feed/<string:feedId>/start")
def queueCrawl(feedId):
    try:
        q = db['queue'].find_one({'feed_id':feedId,'action':'start'})
        if q:
            return returnPrettyJson({'msg':'Feed {} already in queue to start'.format(feedId)}),200
        
        f = db['feeds'].find_one({'_id':feedId},{'status':1,"crawl":1,'config':1})
        if not 'status' in f or f['status'] == 'stopped':
            r = db['queue'].insert_one({'action':'start','feed_id':feedId,'config':f['config']})
            return returnPrettyJson({'config':f['config'],'queued_task':r.inserted_id}),200
        elif f['status'] == 'running':
            return returnPrettyJson({'msg':'Feed {} already running'.format(feedId),'status':f['crawl']}),200
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/feed/<string:feedId>/stop")
def queueStopCrawl(feedId):
    try:
        q = db['queue'].find_one({'feed_id':feedId,'action':'stop'})
        if q:
            return returnPrettyJson({'msg':'Feed {} already in queue to stop'.format(feedId)}),200
        
        f = db['feeds'].find_one({'_id':feedId},{"pid":"$crawl.pid",'status':1})
        if 'status' in f and f['status'] == 'running':
            try:
                r = db['queue'].insert_one({'action':'stop','feed_id':feedId,'pid':f['pid']})
                return returnPrettyJson({'pid':f['pid']}),200
            except Exception as e:
                return returnPrettyJson(e),500
        elif f['status'] != 'running' or 'status' not in r:
            return returnPrettyJson({'msg':'Feed {} is not running'.format(feedId)}),200
    except Exception as e:
        return returnPrettyJson(e),500

# @app.get("/queue")
# def getQueue():
#     try:
#         crawls = list(db['queue'].find().sort('start',-1))
#         return returnPrettyJson(crawls),200
#     except Exception as e:
#         return returnPrettyJson(e),500

# @app.get("/queue/<string:taskId>")
# def queuedTask(taskId):
#     try:
#         status = db['queue'].find_one({'_id':bson.ObjectId(taskId)})
#         return returnPrettyJson(status),200
#     except Exception as e:
#         return returnPrettyJson(e),500

