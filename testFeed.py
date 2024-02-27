from sys import argv
from feeds import feeds
from crawler import Crawler
from os import getenv, getpid
import bson

feedId = argv[1]
found = False
for config in feeds:
    if config['_id'] == feedId:
        print(config)
        found = True
        crawlId = bson.ObjectId()
        crawler= Crawler(MDB_URL=getenv("MDBCONNSTR"),MDB_DB=getenv("MDB_DB"),FEED_CONFIG=config,CRAWL_ID=crawlId,PID=getpid())
        print("Running crawl: ",crawlId)
        crawler.start()
        print("Finished. Crawl log: {}".format(crawlId))
    
if not found:
    print("{} not found in feeds.py".format(feedId))
