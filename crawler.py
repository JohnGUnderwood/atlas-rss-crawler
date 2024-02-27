from os import getenv, getcwd, makedirs
from shutil import rmtree
import feedparser
from datetime import datetime
import bson
import pymongo
import traceback
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import re
import signal
import sys

class DuplicateEntryException(Exception):
    def __init__(self, message):
        super().__init__(message)

class Entry:
    def __init__(self,DATA,DIR,SELECTOR,LANG,ATTRIBUTION):
        self.DIR=DIR
        self.DATA=DATA
        self.SELECTOR=SELECTOR
        self.LANG=LANG
        self.ATTRIBUTION=ATTRIBUTION
    
    def get(self):
        return self.DATA

    def getWebContent(self):
        entry = self.DATA
        selector = self.SELECTOR
        dir = self.DIR
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
        
    def processEntry(self):
        entry = self.DATA
        lang = self.LANG
        attribtuon = self.ATTRIBUTION
        try:
            content = self.getWebContent()
            entry.update({'content':{lang:content}})
            entry.update({'_id':entry.id})
            if 'summary' in entry: entry.update({'summary':{lang:entry.summary}})
            if 'title' in entry: entry.update({'title':{lang:entry.title}})
            if 'published' in entry: entry.update({'published':datetime.strptime(entry.published,'%a, %d %b %Y %H:%M:%S %Z')})
            if 'media_thumbnail' in entry: entry.update({'media_thumbnail':entry.media_thumbnail[0]['url']})
            if 'tags' in entry: entry.update({'tags':[tag['term'] for tag in entry.tags]})
            if 'authors' in entry: entry.update({'authors':[author['name'] for author in entry.authors]})
            entry.update({'lang':lang})
            entry.update({'attribution':attribtuon})
            self.DATA = entry
            return self.DATA
        except Exception as e:
            raise e

class Crawler:
    def __init__(self,MDB_URL,MDB_DB,FEED_CONFIG,PID):
        self.MDB_DB=MDB_DB
        self.MDB_URL=MDB_URL
        self.FEED_CONFIG=FEED_CONFIG
        self.PID=PID
        self.CRAWL_ID=FEED_CONFIG['_id']
        self.MDB_CLIENT=self.connect()
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self,sig,frame):
        print('SIGTERM received, shutting down')
        self.MDB_CLIENT[self.MDB_DB]['feeds'].update_one({'_id':self.FEED_CONFIG['_id']},{"$set":{'crawl.end':datetime.now(),'status':'stopped'}})
        crawl = self.MDB_CLIENT[self.MDB_DB]['feeds'].find_one({'_id':self.FEED_CONFIG['_id']},{'crawl':1})['crawl']
        crawl.update({'feed_id':self.FEED_CONFIG['_id']})
        self.MDB_CLIENT[self.MDB_DB]['logs'].insert_one(crawl)
        self.MDB_CLIENT.close()
        print('Caught the SystemExit exception while running crawl {}'.format(self.CRAWL_ID))
        sys.exit(0)
    
    def connect(self):
        try:
            client = pymongo.MongoClient(self.MDB_URL)
            client.admin.command('ping')
            try:
                client.get_database(self.MDB_DB)
                print("Crawler {} successfully connected to MongoDB {} database!".format(self.CRAWL_ID,self.MDB_DB))
                return client
            except Exception as e:
                print(e)
                print("Crawler {}  failed to connect to {}. Quitting.".format(self.CRAWL_ID,self.MDB_DB))
                exit()
        except Exception as e:
            print(e)
            print("Crawler {} failed to connect to MongoDB. Quitting.")
            exit()

    def updateFeed(self,update):
        try:
            self.MDB_CLIENT[self.MDB_DB]['feeds'].update_one({'_id':self.FEED_CONFIG['_id']},update)
            return
        except Exception as e:
            raise e
    
    def insertEntry(self,session,entry):
        try:
            docs_collection = self.MDB_CLIENT[self.MDB_DB].docs
            logs_collection = self.MDB_CLIENT[self.MDB_DB].logs
            docs_collection.insert_one(entry,session=session)
            logs_collection.update_one({'_id':self.CRAWL_ID},{"$push":{"inserted":entry['id']}},session=session)
            print("Crawler {}: Entry update transaction successful".format(self.CRAWL_ID))
            return
        except pymongo.errors.DuplicateKeyError:
            print("Crawl {} entry {} already exists in database".format(self.CRAWL_ID,entry['id']))
            raise DuplicateEntryException("Entry id {} already exists".format(entry['id']))
        except Exception as e:
            raise e
        
    def processItem(self,item,dir):
        try:
            entry = Entry(item,dir,self.FEED_CONFIG['content_html_selector'],self.FEED_CONFIG['lang'],self.FEED_CONFIG['attribution']).processEntry()
            try:
                self.updateFeed({"$push":{"crawl.crawled":entry['link']}})
                with self.MDB_CLIENT.start_session() as session:
                    session.with_transaction(lambda session: self.insertEntry(session,entry))
            except DuplicateEntryException as e:
                self.updateFeed({'$push':{'crawl.skipped':entry['id']}})
            except Exception as e:
                print("Crawler {} failed to insert entry for item {}".format(self.CRAWL_ID,entry['id']),e)
                self.updateFeed({'$push':{'crawl.errors':{'entryId':entry['id'],'error':str(e)}}})
        except Exception as e:
            print("Crawler {} failed to create Entry object for item {}".format(self.CRAWL_ID,item['id']),e)
            self.updateFeed({'$push':{'crawl.errors':{'entryId':item['id'],'error':str(e)}}})
    
    def start(self):
        config = self.FEED_CONFIG
        crawlId = self.CRAWL_ID
        crawl = {'pid':self.PID,'crawled':[],'inserted':[],'skipped':[],'errors':[]}
        self.updateFeed({"$set":{'crawl':crawl,'status':'running'}})

        date_format = '%a, %d %b %Y %H:%M:%S %Z'
        dir  = '{}/{}/{}'.format(getcwd(),'temp',config['_id'])
        try:
            makedirs(dir,exist_ok=True)
        except FileExistsError:
            pass

        feed = feedparser.parse(config['url'])
        start = datetime.now()
        self.updateFeed({"$set":{'crawl.start':start,'config.last_crawl_date':start}})
        if 'last_crawl_date' in config:
            if config['last_crawl_date'] < datetime.strptime(feed.feed.updated,date_format):
                for item in feed.entries:
                    item_date = datetime.strptime(item.published,date_format)
                    if item_date > config['last_crawl_date']:
                        self.processItem(item,dir)

        else:
            for item in feed.entries:
                self.processItem(item,dir)

        rmtree(dir)
        self.updateFeed({"$set":{'crawl.end':datetime.now(),'status':'stopped'}})
        crawl = self.MDB_CLIENT[self.MDB_DB]['feeds'].find_one({'_id':self.FEED_CONFIG['_id']},{'crawl':1})['crawl']
        crawl.update({'feed_id':self.FEED_CONFIG['_id']})
        self.MDB_CLIENT[self.MDB_DB]['logs'].insert_one(crawl)
        
        self.MDB_CLIENT.close()
        print('Stopping crawl {}'.format(crawlId))