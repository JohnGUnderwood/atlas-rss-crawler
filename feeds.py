feeds = [
    {
        '_id':'bbc_world',
        'config':{
            'lang':'en',
            'url':"https://feeds.bbci.co.uk/news/world/rss.xml",
            'content_html_selector':'article > div[data-component="text-block"]',
            'attribution':'BBC'
        }
    },
    {
        '_id':'bbc_mundo',
        'config':{
            'lang':'es',
            'url':"https://feeds.bbci.co.uk/mundo/rss.xml",
            'content_html_selector':'main > div > p',
            'attribution':'BBC Mundo'
        }
    },
    {
        '_id':'france_24_en',
        'config':{
            'lang':'en',
            'url':"https://www.france24.com/en/rss",
            'content_html_selector':"p.t-content__chapo,div.t-content__body > p",
            'attribution':'France24'
        }
    },
    {
        '_id':'france_24_fr',
        'config':{
            'lang':'fr',
            'url':"https://www.france24.com/fr/rss",
            'content_html_selector':"p.t-content__chapo,div.t-content__body > p",
            'attribution':'France24'
        }
    },
    {
        '_id':'france_24_es',
        'config':{
            'lang':'es',
            'url':"https://www.france24.com/es/rss",
            'content_html_selector':"p.t-content__chapo,div.t-content__body > p",
            'attribution':'France24'
        }
    }
]