# What is this?
Crawler to ingest RSS feeds into MongoDB Atlas

# Okay. How does it work?
The application users a few very cool packages to read an RSS feed, open the reference web pages, and parse the html. I am very grateful to:

[feedparser](https://feedparser.readthedocs.io/en/latest/#)

[Beautiful Soup](https://beautiful-soup-4.readthedocs.io/en/latest/#)

[Selenium](https://www.selenium.dev/selenium/docs/api/py/index.html)

# Tell me more...
The app is split into a backend and frontend. The backend is written in python and provides a processor which reads a queue of crawl tasks as well as flask API to handle requests.

# Tell me more about the task queue.
The data layer for the app is MongoDB Atlas. Configurations for the RSS feeds to crawl are stored in a 'feeds' collection. When an API request to start a feed crawl is received a new task is created in the 'queue' collection. The processor polls this collection every second and when a new task is detected it reads the configuration and starts a crawl process.

# So what happens in a 'crawl process'
During the crawl the target RSS feed url is access and all items in the feed parsed. Each item has a link to a web page which is then opened by the crawler script and the contents parse to extract more data. All this data for each RSS item is then indexed as separate documents in the 'docs' collection. Finally, the status of the crawl is saved as log in the 'logs' collection. In the feeds collection the current crawl log is always saved on the originating feed configuration under the 'crawl' field.

# Can I stop a crawl that's happening?
Yes! The stop API creates a stop task with the PID for the running crawl (which is saved in the orignation feed config). This PID is used to stop the appropriate crawl process.

# So there might be more than one crawl process?
Yes. The processor script uses multiprocessing to spawn a new process for each task.
