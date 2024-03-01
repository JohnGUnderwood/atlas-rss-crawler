from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from bson.json_util import dumps
import json
from crawler import Entry,MyChromeDriver,MongoDBConnection
import feedparser
import traceback

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
connection = MongoDBConnection()
db = connection.connect()
driver = MyChromeDriver()

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
        crawls = list(db['logs'].find({'feed_id':feedId}).sort('end',-1))
        return returnPrettyJson(crawls)
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/feed/<string:feedId>/history/clear")
def deleteFeedCrawlHistory(feedId):
    try:
        db['logs'].delete_many({'feed_id':feedId})
        db['feeds'].update_one({'_id':feedId},{"$unset":{'crawl':1}})
        r = db['feeds'].find_one({'_id':feedId})
        return returnPrettyJson(r),200
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/feed/<string:feedId>/test")
def testFeed(feedId):
    try:
        f = db['feeds'].find_one({'_id':feedId},{'config':1})
        feed = feedparser.parse(f['config']['url'])
        try:
            
            entry = Entry(
                DATA=feed.entries[0],
                SELECTOR=f['config']['content_html_selector'],
                LANG=f['config']['lang'],
                ATTRIBUTION=f['config']['attribution'],
                DRIVER=driver
            ).processEntry()
        except Exception as e:
            return {"error":str(traceback.format_exc())},500
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
        if not 'status' in f or f['status'] == 'stopped' or f['status'] == 'finished':
            crawlConfig = f['config']
            r = db['queue'].insert_one({'action':'start','feed_id':feedId,'config':crawlConfig})
            return returnPrettyJson({'status':'starting','queued_task':r.inserted_id}),200
        elif f['status'] == 'running':
            return returnPrettyJson({'msg':'Feed {} already running'.format(feedId),'crawl':f['crawl'],'status':f['status']}),200
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/feed/<string:feedId>/stop")
def queueStopCrawl(feedId):
    try:
        q = db['queue'].find_one({'feed_id':feedId,'action':'stop'})
        if q:
            return returnPrettyJson({'msg':'Feed {} already in queue to stop'.format(feedId)}),200
        
        f = db['feeds'].find_one({'_id':feedId},{"pid":"$crawl.pid",'status':1})
        if 'status' in f:
            if f['status'] == 'running':
                try:
                    r = db['queue'].insert_one({'action':'stop','feed_id':feedId,'pid':f['pid']})
                    return returnPrettyJson({'pid':f['pid'],'status':'stopping'}),200
                except Exception as e:
                    return returnPrettyJson(e),500
            elif f['status'] != 'running':
                return returnPrettyJson({'msg':'Feed {} is not running'.format(feedId),'status':f['status']}),200
        else:
            return returnPrettyJson({'msg':'Feed {} already stopped'.format(feedId),'status':'not run'}),200
    except Exception as e:
        return returnPrettyJson(e),500

