from crawler import Crawler
from multiprocessing import Process, Queue
import os
import signal
import pymongo
from time import sleep
from concurrent.futures import ProcessPoolExecutor
import traceback

def connect():
    try:
        client = pymongo.MongoClient(os.getenv("MDBCONNSTR"))
        client.admin.command('ping')
        try:
            db = client.get_database(os.getenv("MDB_DB"))
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

def startProcess(config,queue_id):
    try:
        print("Processed task: ",queue_id)
        print('parent process:', os.getppid())
        print('process id:', os.getpid())
        crawler= Crawler(MDB_URL=os.getenv("MDBCONNSTR"),MDB_DB=os.getenv("MDB_DB"),FEED_CONFIG=config,PID=os.getpid())
        print("Running crawl: ",config['_id'])
        crawler.start()
        print("Finished. Crawl log: {}".format(config['_id']))
    except Exception:
        print(traceback.format_exc())

def killProcess(pid,crawlId):
    client,db = connect()
    try:
        db['feeds'].update_one({'_id':crawlId},{"$set":{'status':'stopped'}})
        try: 
            os.kill(pid, signal.SIGTERM)
            print("Stopped crawl: {}".format(crawlId))
        except Exception:
            print(traceback.format_exc())
        finally: client.close()
    except Exception:
        print("Failed to stop crawl {}".format(crawlId),traceback.format_exc())
    finally: client.close()
    

def fetch_data(q):
    client,db = connect()
    data = list(db['queue'].find({'status':'waiting'}))
    if(data):
        print("Found items in queue")
        for item in data:
            print("Removing item {} from queue.".format(item['_id']))
            db['queue'].update_one({'_id':item['_id'],},{"$set":{'status':'processed'}})
            q.put(item)
    else:
        print("Nothing in queue")
    client.close()

def process_data(item):
    if item['action'] == 'start':
        print("Found task to start")
        startProcess(item['config'],item['_id'])
    elif item['action'] == 'stop':
        print("Found task to stop")
        killProcess(item['pid'],item['crawl_id'])

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
        

        
        

        
