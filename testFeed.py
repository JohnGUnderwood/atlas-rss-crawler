from sys import argv
from feeds import feeds
from crawler import processEntry
import feedparser
from os import getcwd,mkdir
from shutil import rmtree
import traceback

feedId = argv[1]
found = False
for config in feeds:
    if config['_id'] == feedId:
        print(config)
        found = True
        feed = feedparser.parse(config['url'])
        dir = '{}/{}'.format(getcwd(),'test')
        try:
            mkdir(dir)
        except FileExistsError:
            pass
        try:
            processEntry(feed.entries[0],config,dir)
        except Exception as e:
            print(traceback.format_exc())
            exit()
        print(feed.entries[0])
        rmtree(dir)
    
if not found:
    print("{} not found in feeds.py".format(feedId))
