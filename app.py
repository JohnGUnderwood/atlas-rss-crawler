from os import getenv, getcwd, mkdir
from shutil import rmtree
from dotenv import load_dotenv
import pymongo
import feedparser
from feeds import feeds
from datetime import datetime
import bson
from openai import OpenAI, AzureOpenAI
from processEntry import processEntry
import traceback

load_dotenv()

MDB_URI=getenv("MDBCONNSTR")
MDB_DB=getenv("MDB_DB")

def connect(url):
    try:
        client = pymongo.MongoClient(url)
        client.admin.command('ping')
        try:
            db = client.get_database(MDB_DB)
            print("Successfully connected to MongoDB {} database!".format(MDB_DB))
            return [client,db]
        except Exception as e:
            print(e)
            print("Failed to connect to {}. Quitting.".format(MDB_DB))
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

def openai():
    if getenv("OPENAIAPIKEY") and getenv("OPENAIDEPLOYMENT") and getenv("OPENAIENDPOINT"):
        try:
            client = AzureOpenAI(
                api_key = getenv("OPENAIAPIKEY"),  
                api_version = "2023-12-01-preview",
                azure_endpoint = getenv("OPENAIENDPOINT")
            )
            print("Successfully created AzureOpenAI client!")
            return [client,"azure_openai"]
        except Exception as e:
            raise e
    elif getenv("OPENAIAPIKEY"):
        try:
            client = OpenAI(api_key = getenv("OPENAIAPIKEY"))
            print("Successfully created OpenAI client!")
            return [client,"openai"]
        except Exception as e:
            raise e

def embed(content,client,type):
    if type == "azure_openai":
        response = client.embeddings.create(
            input=content,
            model=getenv("OPENAIDEPLOYMENT")
        )
        return {"provider":"AzureOpenAI","model":getenv("OPENAIDEPLOYMENT"),"dimensions":len(response.data[0].embedding),"vector":response.data[0].embedding}
    elif type == "openai":
        response = client.embeddings.create(
            input=content,
            model="text-embedding-3-large",
            dimensions=256
        )
        return {"provider":"OpenAI","model":"text-embedding-3-large","dimensions":len(response.data[0].embedding),"vector":response.data[0].embedding}
    else:
        raise "Unrecognised client type {} passed to embed function".format(type)
    
def addEntry(session,logId=None,entry=None):
    try:
        docs_collection = session.client[MDB_DB].docs
        logs_collection = session.client[MDB_DB].logs
        resp = docs_collection.insert_one(entry,session=session)
        logs_collection.update_one({'_id':logId},{"$push":{"crawled":entry.id,"inserted":bson.ObjectId(resp.inserted_id)}},session=session)
    
        print("Entry update transaction successful")
        return
    except Exception as e:
        raise e

def crawl(config):
    dir  = '{}/{}/{}'.format('temp',getcwd(),config['_id'])
    try:
        mkdir(dir)
    except FileExistsError:
        pass
    feed = feedparser.parse(config['url'])
    db['feeds'].update_one({'_id':config['_id']},{"$set":{'lastCrawl':datetime.now()}})
    r = db['logs'].insert_one({'feedId':config['_id'],'start':datetime.now(),'crawled':[],'inserted':[],'errors':[]})
    logId = bson.ObjectId(r.inserted_id)
    if 'lastCrawl' in config:
        lastCrawl = config["lastCrawl"]
        if lastCrawl < datetime.strptime(feed.feed.updated,config['date_format']):
            for entry in feed.entries:
                entry_date = datetime.strptime(entry.published, config['date_format'])
                if entry_date > lastCrawl:
                    try:
                        entry = processEntry(entry,config,dir)
                        entry.update({'embedding':embed("{}. {}".format(entry.title,entry['content'][config['lang']]),openai_client,openai_type)})
                        with client.start_session() as session:
                            session.with_transaction(lambda session: addEntry(session,logId=logId,entry=entry))
                    except Exception:
                        e = traceback.format_exc()
                        db['logs'].update_one({'_id':logId},{'$push':{'errors':{'entryId':entry.id,'error':e}}})

    else:
        for entry in feed.entries:
            try:
                entry = processEntry(entry,config,dir)
                with client.start_session() as session:
                    session.with_transaction(lambda session: addEntry(session,logId=logId,entry=entry))
            except Exception:
                e = traceback.format_exc()
                db['logs'].update_one({'_id':logId},{'$push':{'errors':{'entryId':entry.id,'error':e}}})

    db['logs'].update_one({'_id':logId},{"$set":{'status':'stopped','end':datetime.now()}})
    rmtree(dir)

client, db = connect(MDB_URI)
openai_client,openai_type = openai()
setup()
installed = list(db["feeds"].find())
for config in installed:
    crawl(config)

# from flask import Flask
# app = Flask(__name__)

# @app.get("/start/<string:feedId>")
# def startCrawl(feedId):
#     config = db['feeds'].find_one({'_id':feedId})
#     if config['status'] == 'stopped':
#         db['feeds'].update_one({'_id':config['_id']},{"$set":{'status':'running'}})
#         crawl(config)
#         db['feeds'].update_one({'_id':config['_id']},{"$set":{'status':'stopped'}})
#         return 
#     else:
#         return "<p>Feed {} alread running</p>"




