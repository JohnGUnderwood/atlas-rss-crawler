
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from datetime import datetime
import re

def getWebContent(entry,selector,dir):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"}
        r = requests.get(
                entry.link,
                headers=headers
            ).text
        print(entry.id)
        print(re.sub('[^A-Za-z0-9_\-.]+','',entry.id))
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
        if 'published' in entry: entry.update({'published':datetime.strptime(entry.published, config['date_format'])})
        if 'media_thumbnail' in entry: entry.update({'media_thumbnail':entry.media_thumbnail[0]['url']})
        if 'tags' in entry: entry.update({'tags':[tag['term'] for tag in entry.tags]})
        entry.update({'lang':config['lang']})
        entry.update({'attribution':config['attribution']})
        return entry
    except Exception as e:
        raise e
