import feedparser
from datetime import datetime
import pymongo
from pymongo import ReturnDocument
from bs4 import BeautifulSoup
from selenium import webdriver
import signal
import sys
import traceback

class DuplicateEntryException(Exception):
    def __init__(self, message):
        super().__init__(message)

class ChromeDriver:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("headless")
        self.options.add_argument('--ignore-certificate-errors')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--no-sandbox')
        self.driver = webdriver.Chrome(options=self.options)
    
    def fetchPage(self,link):
        try:
            print("Fetching page from {}".format(link))
            self.driver.get(link)
            html = self.driver.page_source
            print("Got page content.")
            return html
        except Exception:
            print(traceback.format_exc())
            raise Exception("Fetching page failed. {}".format(traceback.format_exc()))
    
    def quit(self):
        self.driver.quit()
        print("Quitting ChromeDriver")

class Entry:
    def __init__(self,DATA,SELECTOR,LANG,ATTRIBUTION):
        self.DATA=DATA
        self.SELECTOR=SELECTOR
        self.LANG=LANG
        self.ATTRIBUTION=ATTRIBUTION
    
    def get(self):
        return self.DATA

    def parseContent(self,html):
        selector = self.SELECTOR
        try:
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
        attribution = self.ATTRIBUTION
        driver = ChromeDriver()
        try:
            html = driver.fetchPage(entry.link)
            content = self.parseContent(html)
            entry.update({'content':{lang:content}})
            entry.update({'_id':entry.id})
            if 'summary' in entry: entry.update({'summary':{lang:entry.summary}})
            if 'title' in entry: entry.update({'title':{lang:entry.title}})
            if 'published' in entry: entry.update({'published':datetime.strptime(entry.published,'%a, %d %b %Y %H:%M:%S %Z')})
            if 'media_thumbnail' in entry: entry.update({'media_thumbnail':entry.media_thumbnail[0]['url']})
            if 'tags' in entry: entry.update({'tags':[tag['term'] for tag in entry.tags]})
            if 'authors' in entry: entry.update({'authors':[author['name'] for author in entry.authors]})
            if 'author' in entry:
                if not 'authors' in entry:
                    entry.update({'authors':entry.author})
            
            entry.update({'lang':lang})
            entry.update({'attribution':attribution})
            self.DATA = entry
            return self.DATA
        except Exception as e:
            raise e
        finally:
            driver.quit()

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
        crawl = self.MDB_CLIENT[self.MDB_DB]['feeds'].find_one_and_update(
            {'_id':self.FEED_CONFIG['_id']},
            {"$set":{'crawl.end':datetime.now(),'status':'stopped'}},
            return_document=ReturnDocument.AFTER
        )['crawl']
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
            feeds_collection = self.MDB_CLIENT[self.MDB_DB].feeds
            docs_collection.insert_one(entry,session=session)
            feeds_collection.update_one({'_id':self.CRAWL_ID},{"$push":{"crawl.inserted":entry['id']}},session=session)
            print("Crawler {}: Entry update transaction successful".format(self.CRAWL_ID))
            return
        except pymongo.errors.DuplicateKeyError:
            print("Crawl {} entry {} already exists in database".format(self.CRAWL_ID,entry['id']))
            raise DuplicateEntryException("Entry id {} already exists".format(entry['id']))
        except Exception as e:
            raise e
        
    def processItem(self,item):
        try:
            entry = Entry(
                DATA=item,
                SELECTOR=self.FEED_CONFIG['content_html_selector'],
                LANG=self.FEED_CONFIG['lang'],
                ATTRIBUTION=self.FEED_CONFIG['attribution']
                ).processEntry()
            try:
                with self.MDB_CLIENT.start_session() as session:
                    session.with_transaction(lambda session: self.insertEntry(session,entry))
            except Exception as e:
                print("Crawler {} failed to insert entry for item {}".format(self.CRAWL_ID,entry['id']),e)
                self.updateFeed({'$push':{'crawl.errors':{'entryId':entry['id'],'error':str(e)}}})
        except Exception as e:
            print("Crawler {} failed to create Entry object for item {}".format(self.CRAWL_ID,item['id']),e)
            self.updateFeed({'$push':{'crawl.errors':{'entryId':item['id'],'error':str(e)}}})
    
    def start(self):
        config = self.FEED_CONFIG
        crawlId = self.CRAWL_ID
        crawl = {'pid':self.PID,'crawled':[],'inserted':[],'errors':[],'duplicates':[]}
        self.updateFeed({"$set":{'crawl':crawl,'status':'running'}})

        feed = feedparser.parse(config['url'])
        self.updateFeed({"$set":{'crawl.start':datetime.now()}})

        for item in feed.entries:
            self.updateFeed({"$push":{"crawl.crawled":item['id']}})
            if self.MDB_CLIENT[self.MDB_DB]['docs'].find_one({'_id':item['id']},{'_id':1}):
                self.updateFeed({'$push':{'crawl.duplicates':item['id']}})
            else:
                self.processItem(item)

        self.MDB_CLIENT.close()
        print('Stopping crawl {}'.format(crawlId))
        self.updateFeed({"$set":{'crawl':crawl,'status':'finished'}})
        return