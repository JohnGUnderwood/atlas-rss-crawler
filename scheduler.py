from crawler import client, db, crawl
from multiprocessing import Process
from datetime import datetime
import os

def process(config,queue_id):
    print("Processing crawl: ",queue_id)
    print('parent process:', os.getppid())
    print('process id:', os.getpid())
    logId = crawl(config)
    db['queue'].delete_one({'_id':queue_id})
    return "Finished. Crawl log: {}".format(logId)

if __name__ == '__main__':
    while True:
        for q in list(db["queue"].find({'status':'waiting'})):
            db['queue'].update_one({'_id':q['_id']},{"$set":{'status':'processing','processed_time':datetime.now()}})
            p = Process(target=process, args=(q['config'],q['_id']))
            p.start()
            p.join()