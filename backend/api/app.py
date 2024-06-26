from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from bson.json_util import dumps
import json
from packages import Entry,MyChromeDriver,MongoDBConnection,MyFeedParser
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
        
def test(config):
    try:
        feed = MyFeedParser(config['url']).parseFeed()
        try:
            entry = Entry(
                DATA=feed.entries[0],
                SELECTORS=config['content_html_selectors'],
                LANG=config['lang'],
                ATTRIBUTION=config['attribution'],
                DRIVER=driver,
                DATE_FORMAT=config['date_format'],
                CUSTOM_FIELDS=config.get('custom_fields',None)
            ).processEntry()
        except Exception as e:
            return {"error":str(traceback.format_exc())},200
        return returnPrettyJson(entry),200
    except Exception as e:
        return returnPrettyJson(e),200
    
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
connection = MongoDBConnection()
db = connection.connect()
driver = MyChromeDriver()

@app.post('/test')
def testConfig():
    try:
        return test(request.json)
    except Exception as e:
        return returnPrettyJson(e),200
    
@app.get("/feeds")
def getFeeds():
    try:
        feedList = list(db['feeds'].find({}))
        feedDict = {feed['_id']: feed for feed in feedList}
        return returnPrettyJson(feedDict), 200
    except Exception as e:
        return returnPrettyJson(e),500

@app.post("/feeds")
def postFeed():
    try:
        db['feeds'].insert_one(request.json)
        feedList = list(db['feeds'].find({}))
        feedDict = {feed['_id']: feed for feed in feedList}
        return returnPrettyJson(feedDict), 200
    except Exception as e:
        return returnPrettyJson(e),500
    
@app.get("/feeds/search")
def searchFeeds():
    query = request.args.get('q', default = "", type = str)
    try:
        feedList = list(db['feeds'].aggregate([
            {"$search":{
                "compound":{
                    "should":[
                        {"autocomplete":{"query":query,"path":"_id"}},
                        {"autocomplete":{"query":query,"path":"config.attribution"}},
                        {"autocomplete":{"query":query,"path":"config.url"}}
                    ]
                }
            }}
        ]))
        feedDict = {feed['_id']: feed for feed in feedList}
        return returnPrettyJson(feedDict), 200
    except Exception as e:
        return returnPrettyJson(e),500

@app.get("/feed/<string:feedId>")
def getFeed(feedId):
    try:
        config = db['feeds'].find_one({'_id':feedId})
        return returnPrettyJson(config), 200
    except Exception as e:
        return returnPrettyJson(e),500

@app.delete("/feed/<string:feedId>")
def deleteFeed(feedId):
    try:
        config = db['feeds'].find_one_and_delete({'_id':feedId})
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
        return test(config=f['config'])
    except Exception as e:
        return returnPrettyJson(e),200

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

