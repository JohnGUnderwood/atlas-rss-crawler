from crawler import Crawler
from multiprocessing import Process, Queue
import os
import signal
import pymongo
from pymongo import ReturnDocument
from time import sleep
from concurrent.futures import ProcessPoolExecutor
import traceback
from datetime import datetime

def connect():
    try:
        client = pymongo.MongoClient(os.getenv("MDBCONNSTR"))
        client.admin.command('ping')
        try:
            db = client.get_database(os.getenv("MDB_DB",default="news-search"))
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

def startProcess(config,feed_id):
    try:
        print('Parent process:', os.getppid())
        print('Process id:', os.getpid())
        config.update({'_id':feed_id})
        crawler=Crawler(MDB_URL=os.getenv("MDBCONNSTR"),MDB_DB=os.getenv("MDB_DB",default="news-search"),FEED_CONFIG=config,PID=os.getpid())
        print("Running crawl: ",feed_id)
        crawler.start()
        client,db = connect()
        crawl = db['feeds'].find_one_and_update(
            {'_id':config['_id']},
            {"$set":{'crawl.end':datetime.now(),'status':'finished'}},
            return_document=ReturnDocument.AFTER
        )['crawl']
        crawl.update({'feed_id':config['_id']})
        db['logs'].insert_one(crawl)
        print("Finished. Crawl log: {}".format(feed_id))
    except Exception:
        print(traceback.format_exc())

def killProcess(pid,crawlId):
    try: 
        os.kill(pid, signal.SIGTERM)
        print("Stopped crawl: {}".format(crawlId))
    except Exception:
        print(traceback.format_exc())
    

def fetch_data(q):
    client,db = connect()
    data = list(db['queue'].find({"$or":[{'action':'stop'},{'action':'start'}]}))
    if(data):
        print("Found items in queue")
        for item in data:
            print("Processing feed {}.".format(item['feed_id']))
            db['queue'].update_one({'_id':item['_id']},{"$set":{'action':'processed'}})
            q.put(item)
    else:
        print("Nothing in queue")
    client.close()

def process_data(item):
    if item['action'] == 'start':
        print("Found task to start")
        startProcess(item['config'],item['feed_id'])
    elif item['action'] == 'stop':
        print("Found task to stop")
        killProcess(item['pid'],item['feed_id'])

if __name__ == '__main__':
    q = Queue()

    fetch_process = Process(target=fetch_data, args=(q,))

    with ProcessPoolExecutor() as executor:
        while True:
            if not q.empty():
                item = q.get()
                executor.submit(process_data, item)

            if not fetch_process.is_alive():
                fetch_process = Process(target=fetch_data, args=(q,))
                fetch_process.start()

            sleep(1)
        

        
        

        
