from os import getenv, getcwd, makedirs
from shutil import rmtree
from dotenv import load_dotenv
import pymongo
import feedparser
from datetime import datetime
import bson
from openai import OpenAI, AzureOpenAI
import traceback
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import re

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

def getWebContent(entry,selector,dir):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"}
        r = requests.get(
                entry.link,
                headers=headers
            ).text
        file = open('{}/{}.html'.format(dir,re.sub('[^A-Za-z0-9_\-.]','',entry.id)),'wt')
        file.write(r)
        file.close()

        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        browser = webdriver.Chrome(options=options)
        browser.get('file://{}/{}.html'.format(dir,re.sub('[^A-Za-z0-9_\-\.]','',entry.id)))
        html = browser.page_source
        browser.quit()

        soup = BeautifulSoup(html, "html.parser")
        tags = soup.select(selector)

        content = ""
        for tag in tags:
            content+=tag.text.strip()

        return content
    except Exception as e:
        raise e

def processEntry(entry,config,dir):
    try:
        content = getWebContent(entry,config['content_html_selector'],dir)
        entry.update({'content':{config['lang']:content}})
        if 'summary' in entry: entry.update({'summary':{config['lang']:entry.summary}})
        if 'title' in entry: entry.update({'title':{config['lang']:entry.title}})
        if 'published' in entry: entry.update({'published':datetime.strptime(entry.published,'%a, %d %b %Y %H:%M:%S %Z')})
        if 'media_thumbnail' in entry: entry.update({'media_thumbnail':entry.media_thumbnail[0]['url']})
        if 'tags' in entry: entry.update({'tags':[tag['term'] for tag in entry.tags]})
        if 'authors' in entry: entry.update({'authors':[author['name'] for author in entry.authors]})
        entry.update({'lang':config['lang']})
        entry.update({'attribution':config['attribution']})
        return entry
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
    r = db['logs'].insert_one({'feedId':config['_id'],'start':datetime.now(),'crawled':[],'inserted':[],'errors':[]})
    logId = bson.ObjectId(r.inserted_id)
    db['feeds'].update_one({'_id':config['_id']},{"$set":{'status':'running','crawlId':logId}})
    date_format = '%a, %d %b %Y %H:%M:%S %Z'
    dir  = '{}/{}/{}'.format(getcwd(),'temp',config['_id'])
    try:
        makedirs(dir,exist_ok=True)
    except FileExistsError:
        pass

    feed = feedparser.parse(config['url'])
    db['feeds'].update_one({'_id':config['_id']},{"$set":{'lastCrawl':datetime.now()}})
    if 'lastCrawl' in config:
        lastCrawl = config["lastCrawl"]
        if lastCrawl < datetime.strptime(feed.feed.updated,date_format):
            for entry in feed.entries:
                entry_date = datetime.strptime(entry.published,date_format)
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

    db['logs'].update_one({'_id':logId},{"$set":{'end':datetime.now()}})
    db['feeds'].update_one({'_id':config['_id']},{"$set":{'status':'stopped'}})
    rmtree(dir)
    return logId

client, db = connect(MDB_URI)
openai_client,openai_type = openai()
        

